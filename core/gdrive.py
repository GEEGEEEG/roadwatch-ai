"""Google Drive sync tùy chọn — kích hoạt khi đặt GDRIVE_FOLDER_ID trong Streamlit Secrets.

Cấu trúc thư mục trên Drive:
  <GDRIVE_FOLDER_ID>/
    roadwatch.db       ← SQLite DB
    images/            ← ảnh gốc
    annotated/         ← ảnh đã vẽ khung nhận diện
    after/             ← ảnh sau sửa chữa

Cách kích hoạt (Streamlit Secrets hoặc biến môi trường):
  GDRIVE_FOLDER_ID            = "1AbCdEf..."   # ID thư mục Drive
  GDRIVE_SERVICE_ACCOUNT_JSON = '{"type":"service_account",...}'  # nội dung JSON

Nếu 2 giá trị trên chưa đặt, mọi hàm trong module này là no-op — app chạy
bình thường với SQLite cục bộ như cũ.
"""
import io
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# Cache id của các subfolder để không gọi Drive API nhiều lần mỗi session
_subfolder_cache: dict[str, str] = {}


# ── Cấu hình ──────────────────────────────────────────────────────────────

def _cfg(name: str) -> str:
    from .config import cfg
    return cfg(name)


def is_enabled() -> bool:
    """Trả về True nếu cả GDRIVE_FOLDER_ID và GDRIVE_SERVICE_ACCOUNT_JSON đều có."""
    return bool(_cfg('GDRIVE_FOLDER_ID') and _cfg('GDRIVE_SERVICE_ACCOUNT_JSON'))


def _root_id() -> str:
    fid = _cfg('GDRIVE_FOLDER_ID')
    if not fid:
        raise RuntimeError('Chưa đặt GDRIVE_FOLDER_ID trong Secrets.')
    return fid


# ── Kết nối ───────────────────────────────────────────────────────────────

def _get_service_account_info() -> dict:
    """Lấy dict thông tin Service Account từ secrets hoặc biến môi trường.
    Xử lý an toàn: dict, AttrDict, chuỗi JSON, đường dẫn file, hoặc TOML section."""
    val = None
    # 1. Thử từ streamlit secrets với các biến thể tên key
    try:
        import streamlit as st
        for k in ('GDRIVE_SERVICE_ACCOUNT_JSON', 'gdrive_service_account_json',
                  'SERVICE_ACCOUNT_JSON', 'GDRIVE_SERVICE_ACCOUNT'):
            if k in st.secrets:
                val = st.secrets[k]
                break
        if val is None and 'gdrive' in st.secrets:
            g_sec = st.secrets['gdrive']
            if isinstance(g_sec, dict) or hasattr(g_sec, 'get'):
                val = g_sec.get('service_account_json') or g_sec.get('service_account')
    except Exception:
        pass

    # 2. Thử từ config / biến môi trường nếu secrets chưa có
    if val is None:
        val = _cfg('GDRIVE_SERVICE_ACCOUNT_JSON') or _cfg('gdrive_service_account_json')

    if not val:
        raise RuntimeError('Chưa tìm thấy biến GDRIVE_SERVICE_ACCOUNT_JSON trong Streamlit Secrets.')

    # Trường hợp 1: val là đối tượng dạng Dict (dict, AttrDict, Mapping)
    if isinstance(val, dict) or hasattr(val, 'keys'):
        d = dict(val)
        # Nếu bị bọc lồng trong 1 key khác
        for sub_k in ('service_account', 'gdrive_service_account_json', 'credentials'):
            if sub_k in d and isinstance(d[sub_k], dict):
                d = dict(d[sub_k])
                break
        return d

    # Trường hợp 2: val là chuỗi (string)
    if isinstance(val, str):
        val_clean = val.strip()

        # Kiểm tra nếu người dùng vô tình dán đường dẫn file
        try:
            fpath = Path(val_clean)
            if fpath.is_file():
                content = fpath.read_text(encoding='utf-8').strip()
                return json.loads(content)
        except Exception:
            pass

        # Thử parse JSON tiêu chuẩn
        try:
            parsed = json.loads(val_clean)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as jde:
            # Thử parse chuỗi Python dict (ví dụ {'type': ...})
            import ast
            try:
                parsed_ast = ast.literal_eval(val_clean)
                if isinstance(parsed_ast, dict):
                    return parsed_ast
            except Exception:
                pass
            raise RuntimeError(
                f'Lỗi định dạng JSON trong GDRIVE_SERVICE_ACCOUNT_JSON: {jde}.\n'
                f'Gợi ý: Hãy bọc toàn bộ nội dung JSON trong 3 dấu nháy đơn \'\'\'...\'\'\' trong Streamlit Secrets.'
            )

    raise RuntimeError(f'Kiểu dữ liệu của GDRIVE_SERVICE_ACCOUNT_JSON không hợp lệ: {type(val).__name__}.')


def get_service_account_email() -> str:
    """Lấy email của Service Account để hướng dẫn người dùng Share thư mục Drive."""
    try:
        info = _get_service_account_info()
        return info.get('client_email', '')
    except Exception:
        return ''


def test_connection() -> dict:
    """Kiểm tra chi tiết kết nối Google Drive và quyền truy cập thư mục."""
    res = {
        'ok': False,
        'email': '',
        'folder_id': '',
        'folder_name': '',
        'message': '',
        'debug_info': ''
    }
    
    # 1. Kiểm tra Folder ID
    try:
        fid = _root_id()
        res['folder_id'] = fid
    except Exception as e:
        res['message'] = f'Chưa cấu hình GDRIVE_FOLDER_ID trong Secrets ({e})'
        return res

    # 2. Kiểm tra Service Account
    try:
        info = _get_service_account_info()
    except Exception as exc:
        res['message'] = str(exc)
        return res

    email = info.get('client_email', '')
    res['email'] = email
    if not email:
        keys_found = list(info.keys()) if isinstance(info, dict) else []
        res['message'] = (
            f'Trong GDRIVE_SERVICE_ACCOUNT_JSON không tìm thấy trường "client_email"!\n'
            f'Các trường đang có: {keys_found}.\n'
            'Hãy chắc chắn bạn đã sao chép đúng toàn bộ file JSON của Service Account tải từ Google Cloud Console.'
        )
        return res

    try:
        svc = _build_service()
    except Exception as e:
        res['message'] = f'Lỗi khởi tạo kết nối Google Drive API: {e}'
        return res

    # 3. Kiểm tra quyền truy cập thư mục mục tiêu trên Drive
    try:
        folder_meta = svc.files().get(
            fileId=fid,
            fields='id, name, capabilities, trashed',
            supportsAllDrives=True
        ).execute()

        if folder_meta.get('trashed'):
            res['message'] = f'Thư mục "{folder_meta.get("name")}" (ID: {fid}) đang nằm trong Thùng rác Google Drive.'
            return res

        res['folder_name'] = folder_meta.get('name', 'Thư mục Drive')
        caps = folder_meta.get('capabilities', {})
        can_add = caps.get('canAddChildren', False)

        if not can_add:
            res['message'] = (
                f'Service Account ({email}) chỉ có quyền Xem (Viewer) đối với thư mục "{res["folder_name"]}".\n\n'
                f'👉 **Cách sửa:** Vào Google Drive, click chuột phải vào thư mục "{res["folder_name"]}" chọn **Chia sẻ**, '
                f'đổi quyền của `{email}` thành **Người chỉnh sửa (Editor)**.'
            )
            return res

        # 4. Thử tạo và xóa 1 file test nhỏ để xác minh quyền ghi
        try:
            from googleapiclient.http import MediaIoBaseUpload
            test_content = b'roadwatch_connection_test'
            media = MediaIoBaseUpload(io.BytesIO(test_content), mimetype='text/plain')
            meta = {'name': '_test_connection.tmp', 'parents': [fid]}
            tmp_file = svc.files().create(body=meta, media_body=media, fields='id').execute()
            tmp_id = tmp_file.get('id')
            if tmp_id:
                svc.files().delete(fileId=tmp_id).execute()
        except Exception as write_err:
            res['message'] = (
                f'Đã tìm thấy thư mục "{res["folder_name"]}" nhưng không thể ghi tệp: {write_err}. '
                f'Hãy đảm bảo Service Account có quyền "Người chỉnh sửa" (Editor).'
            )
            return res

        res['ok'] = True
        res['message'] = f'✅ Kết nối thành công! Thư mục "{res["folder_name"]}" đã sẵn sàng nhận dữ liệu.'
        return res

    except Exception as e:
        err_str = str(e)
        if '404' in err_str or 'File not found' in err_str:
            res['message'] = (
                f'Không tìm thấy thư mục (ID: `{fid}`) hoặc Service Account chưa được chia sẻ quyền truy cập!\n\n'
                f'👉 **Cách khắc phục:**\n'
                f'1. Mở Google Drive, click chuột phải vào thư mục **RoadWatch Data** chọn **Chia sẻ (Share)**.\n'
                f'2. Thêm email: `{email}`\n'
                f'3. Đặt vai trò là **Người chỉnh sửa (Editor)** rồi nhấn **Gửi**.'
            )
        else:
            res['message'] = f'Lỗi khi truy vấn Google Drive API: {e}'
        return res


def sync_all_to_drive() -> tuple[int, int, list[str]]:
    """Đồng bộ toàn bộ cơ sở dữ liệu và các ảnh hiện có lên Drive.
    Trả về: (số_file_thành_công, tổng_số_file, danh_sách_lỗi)"""
    if not is_enabled():
        return 0, 0, ['Google Drive chưa được cấu hình.']

    from .config import data_dir
    p_data = data_dir()
    db_file = p_data / 'roadwatch.db'
    
    files_to_sync: list[tuple[str, Path, str]] = []
    
    # 1. Database
    if db_file.is_file():
        files_to_sync.append(('roadwatch.db', db_file, 'application/x-sqlite3'))

    # 2. Images, Annotated, After
    for folder in ('images', 'annotated', 'after'):
        fdir = p_data / folder
        if fdir.is_dir():
            for p in fdir.glob('*'):
                if p.is_file():
                    mime = 'image/jpeg' if p.suffix.lower() in ('.jpg', '.jpeg') else 'image/png'
                    files_to_sync.append((f'{folder}/{p.name}', p, mime))

    success = 0
    errors = []
    
    for rel_path, path_obj, mime in files_to_sync:
        try:
            data = path_obj.read_bytes()
            upload(rel_path, data, mime=mime)
            success += 1
        except Exception as exc:
            errors.append(f'{rel_path}: {exc}')

    return success, len(files_to_sync), errors


# ── Thao tác nội bộ ───────────────────────────────────────────────────────

def _find_file(svc, name: str, parent_id: str) -> str | None:
    """Tìm file trong folder Drive theo tên. Trả về file id hoặc None."""
    # Thoát ký tự ' trong tên file để tránh lỗi query
    safe = name.replace("'", "\\'")
    q = f"name='{safe}' and '{parent_id}' in parents and trashed=false"
    res = svc.files().list(q=q, fields='files(id)', pageSize=1).execute()
    files = res.get('files', [])
    return files[0]['id'] if files else None


def _get_or_create_folder(svc, name: str, parent_id: str) -> str:
    """Lấy hoặc tạo subfolder. Kết quả được cache trong session."""
    cache_key = f'{parent_id}/{name}'
    if cache_key in _subfolder_cache:
        return _subfolder_cache[cache_key]
    safe = name.replace("'", "\\'")
    q = (f"name='{safe}' and '{parent_id}' in parents and "
         f"mimeType='application/vnd.google-apps.folder' and trashed=false")
    res = svc.files().list(q=q, fields='files(id)', pageSize=1).execute()
    files = res.get('files', [])
    if files:
        fid = files[0]['id']
    else:
        meta = {'name': name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]}
        fid = svc.files().create(body=meta, fields='id').execute()['id']
    _subfolder_cache[cache_key] = fid
    return fid


def _resolve_parent(svc, rel_path: str) -> tuple[str, str]:
    """Phân giải rel_path thành (parent_folder_id, filename).
    Ví dụ: 'images/abc.jpg' → (id_folder_images, 'abc.jpg')
            'roadwatch.db'  → (root_id, 'roadwatch.db')
    """
    parts = Path(rel_path).parts
    if len(parts) == 1:
        return _root_id(), parts[0]
    parent = _get_or_create_folder(svc, parts[0], _root_id())
    return parent, '/'.join(parts[1:])


# ── API công khai ─────────────────────────────────────────────────────────

def upload(rel_path: str, data: bytes,
           mime: str = 'application/octet-stream') -> None:
    """Upload bytes lên Drive theo đường dẫn tương đối.
    Nếu file đã tồn tại thì cập nhật. No-op nếu Drive chưa cấu hình."""
    if not is_enabled():
        return
    try:
        from googleapiclient.http import MediaIoBaseUpload
        svc = _build_service()
        parent_id, filename = _resolve_parent(svc, rel_path)
        media = MediaIoBaseUpload(io.BytesIO(data), mimetype=mime, resumable=False)
        existing = _find_file(svc, filename, parent_id)
        if existing:
            svc.files().update(fileId=existing, media_body=media).execute()
        else:
            meta = {'name': filename, 'parents': [parent_id]}
            svc.files().create(body=meta, media_body=media, fields='id').execute()
        log.debug('GDrive upload OK: %s', rel_path)
    except Exception as exc:
        log.warning('GDrive upload "%s" thất bại: %s', rel_path, exc)


def download(rel_path: str) -> bytes | None:
    """Download file từ Drive theo đường dẫn tương đối.
    Trả về bytes hoặc None nếu file không tồn tại / Drive chưa cấu hình."""
    if not is_enabled():
        return None
    try:
        from googleapiclient.http import MediaIoBaseDownload
        svc = _build_service()
        parent_id, filename = _resolve_parent(svc, rel_path)
        fid = _find_file(svc, filename, parent_id)
        if not fid:
            return None
        buf = io.BytesIO()
        dl = MediaIoBaseDownload(buf, svc.files().get_media(fileId=fid))
        done = False
        while not done:
            _, done = dl.next_chunk()
        log.debug('GDrive download OK: %s (%d bytes)', rel_path, buf.tell())
        return buf.getvalue()
    except Exception as exc:
        log.warning('GDrive download "%s" thất bại: %s', rel_path, exc)
        return None
