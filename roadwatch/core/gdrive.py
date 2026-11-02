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

def _build_service():
    """Tạo Google Drive API service từ service account JSON.
    Import muộn để không lỗi khi chưa cài google-api-python-client."""
    raw = _cfg('GDRIVE_SERVICE_ACCOUNT_JSON')
    if not raw:
        raise RuntimeError('Chưa đặt GDRIVE_SERVICE_ACCOUNT_JSON trong Secrets.')
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        raise RuntimeError(
            'Thiếu thư viện Google Drive. Thêm vào requirements.txt:\n'
            '  google-api-python-client>=2.100\n  google-auth>=2.20')
    info = json.loads(raw)
    creds = Credentials.from_service_account_info(
        info, scopes=['https://www.googleapis.com/auth/drive'])
    return build('drive', 'v3', credentials=creds, cache_discovery=False)


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
