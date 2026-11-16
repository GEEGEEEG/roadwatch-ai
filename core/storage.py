"""Unified Cloud Storage & Migration Manager cho RoadWatch AI v5.0.

Vai trò chuẩn:
  - Ảnh hiện trường (`images/`, `annotated/`, `after/`) lưu trên Supabase Storage (phân phối qua CDN / Signed URL).
  - Bảng dữ liệu (`reports`, `report_history`, `officers`, `app_settings`) lưu trên Supabase PostgreSQL (`core/supabase_rest.py`).
  - Vẫn tương thích ngược với GCS / Google Drive nếu người dùng cấu hình biến cũ.
"""
import io
import json
import logging
from pathlib import Path
from urllib.parse import quote
import urllib.error
import urllib.request

from .config import cfg

log = logging.getLogger(__name__)


def _cfg(name: str, default: str = '') -> str:
    return cfg(name, default)


def _supabase_key() -> str:
    return _cfg('SUPABASE_SERVICE_ROLE_KEY') or _cfg('SUPABASE_KEY')


def get_backend_type() -> str:
    """Trả về 'supabase', 'gcs', 'gdrive', hoặc 'none'."""
    if _cfg('SUPABASE_URL') and _supabase_key():
        return 'supabase'
    if _cfg('GCS_BUCKET_NAME') or _cfg('GCP_BUCKET_NAME'):
        return 'gcs'
    if _cfg('GDRIVE_FOLDER_ID'):
        return 'gdrive'
    return 'none'


def is_enabled() -> bool:
    """True nếu đã cấu hình dịch vụ lưu trữ đám mây và không chạy trong môi trường pytest cô lập."""
    from . import supabase_rest
    btype = get_backend_type()
    if btype == 'supabase':
        return supabase_rest.is_configured()
    if btype == 'gcs':
        return bool(_get_gcs_bucket_name() and _has_gcp_credentials())
    if btype == 'gdrive':
        return bool(_cfg('GDRIVE_FOLDER_ID') and _has_gcp_credentials())
    return False


# ── SUPABASE STORAGE IMPLEMENTATION ───────────────────────────────────────

def _get_supabase_url() -> str:
    url = _cfg('SUPABASE_URL').rstrip('/')
    for suffix in ('/rest/v1', '/rest/v1/', '/storage/v1', '/storage/v1/'):
        if url.endswith(suffix):
            url = url[:-len(suffix)].rstrip('/')
    return url


def _get_supabase_bucket() -> str:
    return _cfg('SUPABASE_BUCKET', 'roadwatch-data') or 'roadwatch-data'


def _supabase_headers(mime: str = 'application/octet-stream') -> dict:
    key = _supabase_key()
    return {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': mime,
        'x-upsert': 'true',
    }


def get_public_url(rel_path: str) -> str | None:
    """Trả về URL CDN công khai của ảnh trên Supabase Storage (nếu bucket là public)."""
    if get_backend_type() != 'supabase' or not is_enabled() or not rel_path:
        return None
    url_base = _get_supabase_url()
    bucket = _get_supabase_bucket()
    clean_path = rel_path.lstrip('/')
    return f"{url_base}/storage/v1/object/public/{quote(bucket)}/{quote(clean_path, safe='/')}"


def get_signed_url(rel_path: str, expires_in: int = 3600) -> str | None:
    """Tạo Signed URL tạm thời cho ảnh nhạy cảm/riêng tư trên Supabase Storage."""
    if get_backend_type() != 'supabase' or not is_enabled() or not rel_path:
        return None
    url_base = _get_supabase_url()
    bucket = _get_supabase_bucket()
    clean_path = rel_path.lstrip('/')
    sign_endpoint = f"{url_base}/storage/v1/object/sign/{quote(bucket)}/{quote(clean_path, safe='/')}"
    key = _supabase_key()
    payload = json.dumps({'expiresIn': int(expires_in)}).encode('utf-8')
    req = urllib.request.Request(
        sign_endpoint,
        data=payload,
        headers={
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            signed_rel = data.get('signedURL') or data.get('signedUrl')
            if signed_rel:
                if signed_rel.startswith('http'):
                    return signed_rel
                return f"{url_base}/storage/v1{signed_rel}"
    except Exception:
        pass
    return get_public_url(rel_path)


def _supabase_upload(rel_path: str, data: bytes, mime: str = 'application/octet-stream') -> None:
    url_base = _get_supabase_url()
    bucket = _get_supabase_bucket()
    clean_path = rel_path.lstrip('/')
    url = f"{url_base}/storage/v1/object/{quote(bucket)}/{quote(clean_path, safe='/')}"

    headers = _supabase_headers(mime)
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30):
            return
    except urllib.error.HTTPError as e:
        if e.code in (400, 409):
            req_put = urllib.request.Request(url, data=data, headers=headers, method='PUT')
            with urllib.request.urlopen(req_put, timeout=30):
                return
        err_body = e.read().decode('utf-8', errors='ignore')
        raise RuntimeError(f'Supabase Upload HTTP {e.code}: {err_body}') from e


def _supabase_download(rel_path: str) -> bytes | None:
    """Tải file từ Supabase Storage: thử endpoint chuẩn có xác thực trước, sau đó fallback sang public URL."""
    url_base = _get_supabase_url()
    bucket = _get_supabase_bucket()
    clean_path = rel_path.lstrip('/')
    key = _supabase_key()
    encoded_path = quote(clean_path, safe='/')

    candidates = [
        (f"{url_base}/storage/v1/object/{quote(bucket)}/{encoded_path}", True),
        (f"{url_base}/storage/v1/object/public/{quote(bucket)}/{encoded_path}", False),
        (f"{url_base}/storage/v1/object/authenticated/{quote(bucket)}/{encoded_path}", True),
    ]
    for url, with_auth in candidates:
        headers = {'apikey': key, 'Authorization': f'Bearer {key}'} if with_auth and key else {}
        req = urllib.request.Request(url, headers=headers, method='GET')
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            log.debug('Supabase Download thử URL %s trả HTTP %s', url, e.code)
        except Exception as exc:
            log.debug('Supabase Download lỗi %s: %s', url, exc)
    return None


def _test_supabase_connection() -> dict:
    url_base = _get_supabase_url()
    bucket = _get_supabase_bucket()
    res = {
        'ok': False,
        'backend': 'supabase',
        'bucket_name': bucket,
        'url': url_base,
        'message': '',
    }

    if not url_base or not _supabase_key():
        res['message'] = 'Chưa cấu hình SUPABASE_URL hoặc SUPABASE_SERVICE_ROLE_KEY / SUPABASE_KEY trong Streamlit Secrets.'
        return res

    test_file = '_roadwatch_test.tmp'
    try:
        _supabase_upload(test_file, b'roadwatch_supabase_ok', 'text/plain')
        content = _supabase_download(test_file)
        if content != b'roadwatch_supabase_ok':
            res['message'] = f'Supabase: Ghi file thành công nhưng chưa đọc lại được từ bucket "{bucket}".'
            return res

        try:
            del_url = f"{url_base}/storage/v1/object/{quote(bucket)}/{test_file}"
            req_del = urllib.request.Request(
                del_url,
                headers={'apikey': _supabase_key(), 'Authorization': f'Bearer {_supabase_key()}'},
                method='DELETE',
            )
            urllib.request.urlopen(req_del, timeout=10)
        except Exception:
            pass

        res['ok'] = True
        res['message'] = f'✅ Supabase Storage kết nối thành công! Bucket `{bucket}` sẵn sàng lưu trữ ảnh CDN.'
        return res

    except Exception as e:
        err = str(e)
        if '404' in err or 'Bucket not found' in err:
            res['message'] = (
                f'Không tìm thấy Bucket `{bucket}` trên Supabase!\n\n'
                '👉 **Cách khắc phục:** Chạy file `migrations/001_supabase_schema.sql` trong SQL Editor '
                f'(tự động tạo bucket `{bucket}`) hoặc vào mục **Storage → New bucket** tạo `{bucket}` (bật Public).'
            )
        elif '403' in err or '401' in err or 'Unauthorized' in err or 'row-level security' in err.lower():
            res['message'] = (
                'Lỗi quyền ghi Supabase Storage (HTTP 401/403 hoặc chặn RLS)!\n\n'
                '👉 **Cách khắc phục chuẩn nhất:** Vào Supabase → **Project Settings → API**, sao chép mã **`service_role` (secret)** '
                'và đặt vào Streamlit Secrets dưới tên `SUPABASE_SERVICE_ROLE_KEY`.'
            )
        else:
            res['message'] = f'Lỗi kết nối Supabase Storage: {e}'
        return res


# ── GOOGLE CLOUD STORAGE & GDRIVE LEGACY COMPATIBILITY ────────────────────

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
        for k in ('GCS_SERVICE_ACCOUNT_JSON', 'GDRIVE_SERVICE_ACCOUNT_JSON'):
            raw = _cfg(k)
            if raw:
                val = raw
                break
    if not val:
        raise RuntimeError('Chưa cấu hình Service Account JSON.')
    if isinstance(val, dict) or hasattr(val, 'keys'):
        return dict(val)
    if isinstance(val, str):
        return json.loads(val.strip())
    raise RuntimeError('Service Account JSON không hợp lệ.')


def get_service_account_email() -> str:
    try:
        return _get_service_account_info().get('client_email', '')
    except Exception:
        return ''


def _gcs_upload(rel_path: str, data: bytes, mime: str = 'application/octet-stream') -> None:
    bucket_name = _get_gcs_bucket_name()
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import AuthorizedSession
    creds = Credentials.from_service_account_info(
        _get_service_account_info(), scopes=['https://www.googleapis.com/auth/devstorage.read_write'])
    session = AuthorizedSession(creds)
    url = f"https://storage.googleapis.com/upload/storage/v1/b/{bucket_name}/o?uploadType=media&name={quote(rel_path, safe='')}"
    res = session.post(url, headers={'Content-Type': mime}, data=data)
    if res.status_code not in (200, 201):
        raise RuntimeError(f'GCS Upload HTTP {res.status_code}: {res.text}')


def _gcs_download(rel_path: str) -> bytes | None:
    bucket_name = _get_gcs_bucket_name()
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import AuthorizedSession
    creds = Credentials.from_service_account_info(
        _get_service_account_info(), scopes=['https://www.googleapis.com/auth/devstorage.read_write'])
    session = AuthorizedSession(creds)
    url = f"https://storage.googleapis.com/storage/v1/b/{bucket_name}/o/{quote(rel_path, safe='')}?alt=media"
    res = session.get(url)
    return res.content if res.status_code == 200 else None


# ── UNIFIED PUBLIC API ────────────────────────────────────────────────────

def upload(rel_path: str, data: bytes, mime: str = 'application/octet-stream') -> bool:
    """Tải bytes lên Cloud Storage. Trả về True nếu thành công."""
    if not is_enabled():
        return False
    btype = get_backend_type()
    try:
        if btype == 'supabase':
            _supabase_upload(rel_path, data, mime)
        elif btype == 'gcs':
            _gcs_upload(rel_path, data, mime)
        elif btype == 'gdrive':
            from . import gdrive
            gdrive.upload(rel_path, data, mime)
        return True
    except Exception as exc:
        log.warning('Cloud upload "%s" (%s) thất bại: %s', rel_path, btype, exc)
        return False


def download(rel_path: str) -> bytes | None:
    """Tải bytes từ Cloud Storage."""
    if not is_enabled():
        return None
    btype = get_backend_type()
    try:
        if btype == 'supabase':
            return _supabase_download(rel_path)
        if btype == 'gcs':
            return _gcs_download(rel_path)
        if btype == 'gdrive':
            from . import gdrive
            return gdrive.download(rel_path)
    except Exception as exc:
        log.warning('Cloud download "%s" (%s) thất bại: %s', rel_path, btype, exc)
    return None


def test_connection() -> dict:
    btype = get_backend_type()
    if btype == 'supabase':
        return _test_supabase_connection()
    if btype == 'gcs':
        bucket_name = _get_gcs_bucket_name()
        try:
            _gcs_upload('_test.tmp', b'ok', 'text/plain')
            return {'ok': True, 'backend': 'gcs', 'message': f'✅ Kết nối GCS thành công tới bucket `{bucket_name}`.'}
        except Exception as e:
            return {'ok': False, 'backend': 'gcs', 'message': f'Lỗi GCS: {e}'}
    if btype == 'gdrive':
        from . import gdrive
        return gdrive.test_connection()
    return {
        'ok': False,
        'backend': 'none',
        'message': 'Chưa cấu hình dịch vụ lưu trữ đám mây (SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY) trong Secrets.',
    }


def sync_all_to_cloud() -> tuple[int, int, list[str]]:
    """Đồng bộ toàn bộ ảnh hiện trường (`images/`, `annotated/`, `after/`) lên Cloud Storage,
    đồng thời chuyển tiếp dữ liệu SQLite cục bộ (nếu có) lên bảng Supabase PostgreSQL."""
    if not is_enabled():
        return 0, 0, ['Dịch vụ lưu trữ đám mây chưa được cấu hình.']

    from . import supabase_rest
    from .config import data_dir

    p_data = data_dir()
    files_to_sync: list[tuple[str, Path, str]] = []

    # Nếu chưa tạo bảng PostgreSQL thì mới sao lưu tạm file SQLite; nếu đã có PostgreSQL thì đẩy dòng chuẩn
    pg_ready = supabase_rest.table_ready('reports', force=True)
    if not pg_ready:
        for db_name in ('roadwatch.db', 'officers.db'):
            f = p_data / db_name
            if f.is_file():
                files_to_sync.append((db_name, f, 'application/x-sqlite3'))

    for folder in ('images', 'annotated', 'after'):
        fdir = p_data / folder
        if fdir.is_dir():
            for p in fdir.glob('*'):
                if p.is_file():
                    mime = 'image/jpeg' if p.suffix.lower() in ('.jpg', '.jpeg') else 'image/png'
                    files_to_sync.append((f'{folder}/{p.name}', p, mime))

    success = 0
    errors: list[str] = []
    for rel_path, path_obj, mime in files_to_sync:
        if upload(rel_path, path_obj.read_bytes(), mime=mime):
            success += 1
        else:
            errors.append(f'Không tải lên được: {rel_path}')

    # Nếu Supabase PostgreSQL đã sẵn sàng, đồng bộ luôn các bản ghi từ SQLite cục bộ sang PostgreSQL
    if pg_ready:
        mig_ok, mig_errs = migrate_local_sqlite_to_postgres()
        if mig_errs:
            errors.extend(mig_errs)
        elif mig_ok > 0:
            log.info('Đã đồng bộ %d bản ghi từ SQLite cục bộ lên Supabase PostgreSQL.', mig_ok)

    return success, len(files_to_sync), errors


def migrate_local_sqlite_to_postgres() -> tuple[int, list[str]]:
    """Chuyển tiếp không trùng lặp toàn bộ bản ghi từ roadwatch.db & officers.db cục bộ lên Supabase PostgreSQL."""
    import sqlite3
    from . import db as db_mod
    from . import supabase_rest

    if not supabase_rest.table_ready('reports', force=True):
        return 0, ['Bảng Supabase PostgreSQL chưa sẵn sàng. Hãy chạy file SQL khởi tạo trước.']

    p_data = cfg('ROADWATCH_DATA', '')
    from .config import data_dir
    root = Path(p_data) if p_data else data_dir()
    migrated = 0
    errors: list[str] = []

    # 1. Migrate officers.db
    off_file = root / 'officers.db'
    if off_file.is_file() and supabase_rest.table_ready('officers'):
        try:
            with sqlite3.connect(off_file) as conn:
                conn.row_factory = sqlite3.Row
                rows = [dict(r) for r in conn.execute('SELECT * FROM officers').fetchall()]
            if rows:
                supabase_rest.insert('officers', rows, upsert=True)
                migrated += len(rows)
        except Exception as exc:
            errors.append(f'Migrate officers: {exc}')

    # 2. Migrate roadwatch.db
    rw_file = root / 'roadwatch.db'
    if rw_file.is_file():
        try:
            with sqlite3.connect(rw_file) as conn:
                conn.row_factory = sqlite3.Row
                rep_rows = [
                    {k: v for k, v in dict(r).items() if k in db_mod.COLUMNS}
                    for r in conn.execute('SELECT * FROM reports').fetchall()
                ]
            if rep_rows:
                supabase_rest.insert('reports', rep_rows, upsert=True)
                migrated += len(rep_rows)
        except Exception as exc:
            errors.append(f'Migrate reports: {exc}')

    return migrated, errors
