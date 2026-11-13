"""Unified Cloud Storage Manager cho RoadWatch AI.
Hỗ trợ:
  1. Supabase Storage — MIỄN PHÍ 100%, KHÔNG CẦN THẺ NGÂN HÀNG, 1GB vĩnh viễn (Khuyên dùng số 1).
  2. Google Cloud Storage (GCS) — Cho tài khoản có thẻ/Billing.
  3. Google Drive (GDrive) — Hỗ trợ fallback cho Shared Drive.

Cấu hình trong Streamlit Secrets:
  # Lựa chọn 1: Supabase (Khuyên dùng - 100% Free, không cần thẻ)
  SUPABASE_URL    = "https://xxxx.supabase.co"
  SUPABASE_KEY    = "eyJhbGciOi..."
  SUPABASE_BUCKET = "roadwatch-data"

  # Lựa chọn 2: Google Cloud Storage
  GCS_BUCKET_NAME = "roadwatch-data-514509"
  GDRIVE_SERVICE_ACCOUNT_JSON = '''{...}'''

  # Lựa chọn 3: Google Drive
  GDRIVE_FOLDER_ID = "1AbCdEf..."
  GDRIVE_SERVICE_ACCOUNT_JSON = '''{...}'''
"""
import io
import json
import logging
from pathlib import Path
from urllib.parse import quote_plus
import urllib.request
import urllib.error

log = logging.getLogger(__name__)

# ── Cấu hình & Thông tin kết nối ──────────────────────────────────────────

def _cfg(name: str, default: str = '') -> str:
    from .config import cfg
    val = cfg(name, '')
    if not val:
        try:
            import streamlit as st
            val = str(st.secrets.get(name, '') or st.secrets.get(name.lower(), ''))
        except Exception:
            pass
    return (val or default).strip()


def get_backend_type() -> str:
    """Trả về 'supabase', 'gcs', 'gdrive', hoặc 'none'."""
    if _cfg('SUPABASE_URL') and _cfg('SUPABASE_KEY'):
        return 'supabase'
    if _cfg('GCS_BUCKET_NAME') or _cfg('GCP_BUCKET_NAME'):
        return 'gcs'
    if _cfg('GDRIVE_FOLDER_ID'):
        return 'gdrive'
    return 'none'


def is_enabled() -> bool:
    """True nếu đã cấu hình một trong các dịch vụ lưu trữ."""
    btype = get_backend_type()
    if btype == 'supabase':
        return bool(_cfg('SUPABASE_URL') and _cfg('SUPABASE_KEY'))
    if btype == 'gcs':
        return bool(_get_gcs_bucket_name() and _has_gcp_credentials())
    if btype == 'gdrive':
        return bool(_cfg('GDRIVE_FOLDER_ID') and _has_gcp_credentials())
    return False


# ── SUPABASE STORAGE IMPLEMENTATION ───────────────────────────────────────

def _get_supabase_url() -> str:
    url = _cfg('SUPABASE_URL').rstrip('/')
    # Tự động gọt bỏ đuôi /rest/v1 nếu người dùng sao chép từ Data API
    for suffix in ('/rest/v1', '/rest/v1/', '/storage/v1', '/storage/v1/'):
        if url.endswith(suffix):
            url = url[:-len(suffix)].rstrip('/')
    return url


def _get_supabase_bucket() -> str:
    return _cfg('SUPABASE_BUCKET', 'roadwatch-data') or 'roadwatch-data'


def _supabase_headers(mime: str = 'application/octet-stream') -> dict:
    key = _cfg('SUPABASE_KEY')
    return {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': mime,
        'x-upsert': 'true',  # ghi đè file nếu đã tồn tại
    }


def _supabase_upload(rel_path: str, data: bytes, mime: str = 'application/octet-stream') -> None:
    url_base = _get_supabase_url()
    bucket = _get_supabase_bucket()
    # Supabase upload endpoint: POST hoặc PUT tới /storage/v1/object/{bucket}/{wildcard}
    clean_path = rel_path.lstrip('/')
    url = f"{url_base}/storage/v1/object/{bucket}/{quote_plus(clean_path, safe='/')}"
    
    headers = _supabase_headers(mime)
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            pass
    except urllib.error.HTTPError as e:
        # Nếu lỗi 400 hoặc 409, thử PUT
        if e.code in (400, 409):
            req_put = urllib.request.Request(url, data=data, headers=headers, method='PUT')
            with urllib.request.urlopen(req_put, timeout=30) as resp:
                pass
        else:
            err_body = e.read().decode('utf-8', errors='ignore')
            raise RuntimeError(f"Supabase Upload HTTP {e.code}: {err_body}")


def _supabase_download(rel_path: str) -> bytes | None:
    url_base = _get_supabase_url()
    bucket = _get_supabase_bucket()
    clean_path = rel_path.lstrip('/')
    url = f"{url_base}/storage/v1/object/authenticated/{bucket}/{quote_plus(clean_path, safe='/')}"
    headers = {
        'apikey': _cfg('SUPABASE_KEY'),
        'Authorization': f"Bearer {_cfg('SUPABASE_KEY')}",
    }
    req = urllib.request.Request(url, headers=headers, method='GET')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        log.warning('Supabase Download HTTP %s: %s', e.code, e.reason)
        return None
    except Exception as exc:
        log.warning('Supabase Download "%s" thất bại: %s', rel_path, exc)
        return None


def _test_supabase_connection() -> dict:
    url_base = _get_supabase_url()
    bucket = _get_supabase_bucket()
    res = {
        'ok': False,
        'backend': 'supabase',
        'bucket_name': bucket,
        'url': url_base,
        'message': ''
    }

    if not url_base or not _cfg('SUPABASE_KEY'):
        res['message'] = 'Chưa cấu hình SUPABASE_URL hoặc SUPABASE_KEY trong Streamlit Secrets.'
        return res

    test_file = '_roadwatch_test.tmp'
    try:
        # 1. Thử ghi file test
        _supabase_upload(test_file, b'roadwatch_supabase_ok', 'text/plain')
        # 2. Thử đọc lại
        content = _supabase_download(test_file)
        if content != b'roadwatch_supabase_ok':
            res['message'] = f'Supabase: Ghi file thành công nhưng không đọc lại được từ bucket "{bucket}".'
            return res

        # 3. Dọn dẹp file test
        try:
            del_url = f"{url_base}/storage/v1/object/{bucket}/{test_file}"
            req_del = urllib.request.Request(del_url, headers={
                'apikey': _cfg('SUPABASE_KEY'),
                'Authorization': f"Bearer {_cfg('SUPABASE_KEY')}",
            }, method='DELETE')
            urllib.request.urlopen(req_del, timeout=10)
        except Exception:
            pass

        res['ok'] = True
        res['message'] = f'✅ Kết nối Supabase thành công! Bucket "{bucket}" đã sẵn sàng lưu trữ vĩnh viễn.'
        return res

    except Exception as e:
        err = str(e)
        if '404' in err or 'Bucket not found' in err:
            res['message'] = (
                f'Không tìm thấy Bucket "{bucket}" trên Supabase!\n\n'
                f'👉 **Cách khắc phục:**\n'
                f'1. Mở trang Supabase ➔ Chọn mục **Storage** ở menu bên trái.\n'
                f'2. Bấm **New bucket** ➔ Đặt tên là: `{bucket}`.\n'
                f'3. Bật công tắc **Public bucket** ➔ Bấm **Save**.'
            )
        elif '403' in err or '401' in err or 'Unauthorized' in err:
            res['message'] = (
                f'Lỗi xác thực Supabase API Key (HTTP 401/403)!\n\n'
                f'👉 **Cách khắc phục:**\n'
                f'Vào Supabase ➔ Project Settings ➔ API ➔ Copy lại mã **anon / public key** và kiểm tra lại SUPABASE_KEY trong Secrets.'
            )
        else:
            res['message'] = f'Lỗi kết nối Supabase: {e}'
        return res


# ── GOOGLE CLOUD STORAGE & GDRIVE UTILITIES ────────────────────────────────

def _get_gcs_bucket_name() -> str:
    return _cfg('GCS_BUCKET_NAME') or _cfg('GCP_BUCKET_NAME')


def _has_gcp_credentials() -> bool:
    try:
        info = _get_service_account_info()
        return bool(info.get('client_email') or info.get('private_key'))
    except Exception:
        return False


def _get_service_account_info() -> dict:
    val = None
    try:
        import streamlit as st
        for k in ('GCS_SERVICE_ACCOUNT_JSON', 'GDRIVE_SERVICE_ACCOUNT_JSON',
                  'gcs_service_account_json', 'gdrive_service_account_json',
                  'SERVICE_ACCOUNT_JSON', 'GDRIVE_SERVICE_ACCOUNT'):
            if k in st.secrets:
                val = st.secrets[k]
                break
    except Exception:
        pass

    if val is None:
        for k in ('GCS_SERVICE_ACCOUNT_JSON', 'GDRIVE_SERVICE_ACCOUNT_JSON',
                  'gcs_service_account_json', 'gdrive_service_account_json'):
            raw = _cfg(k)
            if raw:
                val = raw
                break

    if not val:
        raise RuntimeError('Chưa cấu hình Service Account JSON trong Streamlit Secrets.')

    if isinstance(val, dict) or hasattr(val, 'keys'):
        d = dict(val)
        for sub_k in ('service_account', 'credentials'):
            if sub_k in d and isinstance(d[sub_k], dict):
                d = dict(d[sub_k])
                break
        return d

    if isinstance(val, str):
        val_clean = val.strip()
        try:
            return json.loads(val_clean)
        except Exception:
            pass
        import ast
        try:
            res = ast.literal_eval(val_clean)
            if isinstance(res, dict):
                return res
        except Exception:
            pass
        raise RuntimeError('Lỗi cú pháp JSON trong Service Account Key.')

    raise RuntimeError(f'Kiểu dữ liệu Service Account không hợp lệ: {type(val).__name__}.')


def get_service_account_email() -> str:
    try:
        info = _get_service_account_info()
        return info.get('client_email', '')
    except Exception:
        return ''


def _gcs_upload(rel_path: str, data: bytes, mime: str = 'application/octet-stream') -> None:
    bucket_name = _get_gcs_bucket_name()
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import AuthorizedSession
    info = _get_service_account_info()
    creds = Credentials.from_service_account_info(
        info, scopes=['https://www.googleapis.com/auth/devstorage.read_write'])
    session = AuthorizedSession(creds)
    url = f"https://storage.googleapis.com/upload/storage/v1/b/{bucket_name}/o?uploadType=media&name={quote_plus(rel_path)}"
    res = session.post(url, headers={'Content-Type': mime}, data=data)
    if res.status_code not in (200, 201):
        raise RuntimeError(f"GCS Upload HTTP {res.status_code}: {res.text}")


def _gcs_download(rel_path: str) -> bytes | None:
    bucket_name = _get_gcs_bucket_name()
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import AuthorizedSession
    info = _get_service_account_info()
    creds = Credentials.from_service_account_info(
        info, scopes=['https://www.googleapis.com/auth/devstorage.read_write'])
    session = AuthorizedSession(creds)
    url = f"https://storage.googleapis.com/storage/v1/b/{bucket_name}/o/{quote_plus(rel_path)}?alt=media"
    res = session.get(url)
    if res.status_code == 200:
        return res.content
    return None


# ── UNIFIED PUBLIC API ────────────────────────────────────────────────────

def upload(rel_path: str, data: bytes, mime: str = 'application/octet-stream') -> None:
    """Tải bytes lên Cloud (Supabase, GCS, hoặc Google Drive)."""
    if not is_enabled():
        return
    btype = get_backend_type()
    try:
        if btype == 'supabase':
            _supabase_upload(rel_path, data, mime)
            log.debug('Supabase upload OK: %s', rel_path)
        elif btype == 'gcs':
            _gcs_upload(rel_path, data, mime)
            log.debug('GCS upload OK: %s', rel_path)
        elif btype == 'gdrive':
            from . import gdrive
            gdrive.upload(rel_path, data, mime)
    except Exception as exc:
        log.warning('Cloud upload "%s" (%s) thất bại: %s', rel_path, btype, exc)


def download(rel_path: str) -> bytes | None:
    """Tải bytes từ Cloud (Supabase, GCS, hoặc Google Drive)."""
    if not is_enabled():
        return None
    btype = get_backend_type()
    try:
        if btype == 'supabase':
            return _supabase_download(rel_path)
        elif btype == 'gcs':
            return _gcs_download(rel_path)
        elif btype == 'gdrive':
            from . import gdrive
            return gdrive.download(rel_path)
    except Exception as exc:
        log.warning('Cloud download "%s" (%s) thất bại: %s', rel_path, btype, exc)
        return None


def test_connection() -> dict:
    """Kiểm tra chi tiết kết nối Cloud Storage."""
    btype = get_backend_type()
    if btype == 'supabase':
        return _test_supabase_connection()
    if btype == 'gcs':
        # GCS test
        bucket_name = _get_gcs_bucket_name()
        email = get_service_account_email()
        try:
            _gcs_upload('_test.tmp', b'ok', 'text/plain')
            return {'ok': True, 'backend': 'gcs', 'message': f'✅ Kết nối GCS thành công tới bucket "{bucket_name}".'}
        except Exception as e:
            return {'ok': False, 'backend': 'gcs', 'message': f'Lỗi GCS: {e}'}
    if btype == 'gdrive':
        from . import gdrive
        return gdrive.test_connection()
    return {
        'ok': False,
        'backend': 'none',
        'message': 'Chưa cấu hình dịch vụ lưu trữ đám mây (SUPABASE_URL, GCS_BUCKET_NAME hoặc GDRIVE_FOLDER_ID) trong Secrets.'
    }


def sync_all_to_cloud() -> tuple[int, int, list[str]]:
    """Đồng bộ toàn bộ database và các ảnh hiện trường lên Cloud."""
    if not is_enabled():
        return 0, 0, ['Dịch vụ lưu trữ đám mây chưa được cấu hình.']

    from .config import data_dir
    p_data = data_dir()
    db_file = p_data / 'roadwatch.db'
    
    files_to_sync: list[tuple[str, Path, str]] = []
    if db_file.is_file():
        files_to_sync.append(('roadwatch.db', db_file, 'application/x-sqlite3'))

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
