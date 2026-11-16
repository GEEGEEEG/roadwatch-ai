"""Client giao tiếp trực tiếp với Supabase PostgreSQL qua PostgREST (HTTPS JSON).

Ưu điểm trên Streamlit Community Cloud:
- Không phụ thuộc thư viện C nặng (libpq), tương thích 100% IPv4/IPv6 và Python 3.11-3.13.
- Ghi/cập nhật từng dòng nguyên tử (atomic row-level CRUD), triệt tiêu hoàn toàn lỗi ghi đè file SQLite.
- Tự động fallback sang SQLite cục bộ khi chạy unit test hoặc khi người dùng chưa chạy file SQL khởi tạo.
"""
import base64
import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .config import PROJECT_ROOT, cfg

log = logging.getLogger(__name__)

_PROBE_CACHE: dict[str, tuple[float, bool]] = {}
_PROBE_TTL_S = 60.0


class SupabaseConflictError(Exception):
    """Ném ra khi vi phạm ràng buộc UNIQUE (HTTP 409 / Postgres 23505)."""


def get_url() -> str:
    url = cfg('SUPABASE_URL', '').rstrip('/')
    for suffix in ('/rest/v1', '/storage/v1'):
        if url.endswith(suffix):
            url = url[:-len(suffix)].rstrip('/')
    return url


def get_api_key() -> str:
    """Ưu tiên SUPABASE_SERVICE_ROLE_KEY (chuẩn bảo mật phía server), fallback về SUPABASE_KEY."""
    return cfg('SUPABASE_SERVICE_ROLE_KEY') or cfg('SUPABASE_KEY')


def get_key_role() -> str:
    """Giải mã payload JWT (không cần khóa bí mật) để biết key đang dùng là 'service_role' hay 'anon'."""
    key = get_api_key()
    if not key or key.count('.') != 2:
        return 'unknown'
    try:
        payload_b64 = key.split('.')[1]
        padding = '=' * (-len(payload_b64) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload_b64 + padding).decode('utf-8'))
        return str(data.get('role', 'unknown'))
    except Exception:
        return 'unknown'


def is_configured() -> bool:
    """True nếu có cấu hình Supabase và không đang ở chế độ cô lập unit test cục bộ."""
    if os.environ.get('ROADWATCH_DATA') and not os.environ.get('ROADWATCH_TEST_SUPABASE'):
        # Khi pytest đặt ROADWATCH_DATA vào thư mục tạm, luôn dùng SQLite tạm để cô lập test
        if str(PROJECT_ROOT / 'data') != os.environ.get('ROADWATCH_DATA'):
            return False
    return bool(get_url() and get_api_key())


def reset_probe_cache() -> None:
    _PROBE_CACHE.clear()


def _headers(prefer: str = '') -> dict[str, str]:
    key = get_api_key()
    h = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    if prefer:
        h['Prefer'] = prefer
    return h


def _request(method: str, table: str, *, params: dict[str, str] | None = None,
             body: Any = None, prefer: str = '', timeout: int = 20) -> Any:
    base = get_url()
    if not base:
        raise RuntimeError('Chưa cấu hình SUPABASE_URL.')
    q = f"?{urllib.parse.urlencode(params, safe='(),.*:')}" if params else ''
    url = f"{base}/rest/v1/{urllib.parse.quote(table)}{q}"
    data = json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, headers=_headers(prefer), method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode('utf-8').strip()
            return json.loads(raw) if raw else []
    except urllib.error.HTTPError as exc:
        err_text = exc.read().decode('utf-8', errors='ignore')
        if exc.code == 409 or '23505' in err_text:
            raise SupabaseConflictError(err_text) from exc
        raise RuntimeError(f'Supabase REST {method} /{table} HTTP {exc.code}: {err_text}') from exc


def table_ready(table: str = 'reports', force: bool = False) -> bool:
    """Kiểm tra bảng PostgreSQL đã tồn tại và có quyền đọc/ghi hay chưa (có cache 60s)."""
    if not is_configured():
        return False
    now = time.monotonic()
    cached = _PROBE_CACHE.get(table)
    if not force and cached and (now - cached[0] < _PROBE_TTL_S):
        return cached[1]
    try:
        _request('GET', table, params={'select': '*', 'limit': '1'}, timeout=8)
        _PROBE_CACHE[table] = (now, True)
        return True
    except Exception as exc:
        log.debug('Bảng Supabase "%s" chưa sẵn sàng (dùng fallback SQLite): %s', table, exc)
        _PROBE_CACHE[table] = (now, False)
        return False


def select(table: str, *, filters: dict[str, str] | None = None,
           columns: str = '*', order: str = '', limit: int | None = None) -> list[dict]:
    params: dict[str, str] = {'select': columns}
    if filters:
        params.update(filters)
    if order:
        params['order'] = order
    if limit is not None:
        params['limit'] = str(limit)
    res = _request('GET', table, params=params)
    return res if isinstance(res, list) else []


def insert(table: str, payload: dict | list[dict], *, upsert: bool = False) -> list[dict]:
    prefer = 'return=representation'
    if upsert:
        prefer = 'resolution=merge-duplicates,return=representation'
    res = _request('POST', table, body=payload, prefer=prefer)
    return res if isinstance(res, list) else []


def update(table: str, filters: dict[str, str], payload: dict) -> list[dict]:
    if not filters:
        raise ValueError('Cần điều kiện filter khi UPDATE bảng Supabase.')
    res = _request('PATCH', table, params=filters, body=payload, prefer='return=representation')
    return res if isinstance(res, list) else []


def diagnose_postgres() -> dict:
    """Chẩn đoán toàn diện kết nối Supabase PostgreSQL cho trang Quản trị."""
    reset_probe_cache()
    info = {
        'configured': is_configured(),
        'url': get_url(),
        'key_role': get_key_role(),
        'tables': {},
        'all_ready': False,
        'message': '',
    }
    if not info['configured']:
        info['message'] = 'Chưa cấu hình SUPABASE_URL và SUPABASE_SERVICE_ROLE_KEY (hoặc SUPABASE_KEY) trong Secrets.'
        return info

    required_tables = ('reports', 'report_history', 'officers', 'app_settings')
    missing = []
    errors = []
    for t in required_tables:
        try:
            _request('GET', t, params={'select': '*', 'limit': '1'}, timeout=8)
            info['tables'][t] = True
            _PROBE_CACHE[t] = (time.monotonic(), True)
        except Exception as exc:
            info['tables'][t] = False
            _PROBE_CACHE[t] = (time.monotonic(), False)
            msg = str(exc)
            if '404' in msg or 'PGRST205' in msg or '42P01' in msg:
                missing.append(t)
            else:
                errors.append(f'{t}: {msg}')

    if not missing and not errors:
        info['all_ready'] = True
        role_note = (
            'Đang dùng `service_role` key (Chuẩn bảo mật Server).'
            if info['key_role'] == 'service_role'
            else 'Đang dùng `anon` key — khuyến nghị đổi sang `SUPABASE_SERVICE_ROLE_KEY` trong Streamlit Secrets để bật RLS bảo mật tối đa.'
        )
        info['message'] = f'✅ Supabase PostgreSQL đã kết nối đầy đủ 4 bảng chuẩn! {role_note}'
    elif missing:
        info['message'] = (
            f'⚠️ Thiếu bảng PostgreSQL trên Supabase: `{", ".join(missing)}`.\n\n'
            '👉 Mở **Supabase Dashboard → SQL Editor**, dán nội dung file `migrations/001_supabase_schema.sql` và bấm **Run**.'
        )
    else:
        info['message'] = (
            '⚠️ Lỗi phân quyền truy cập bảng Supabase PostgreSQL:\n'
            + '\n'.join(errors[:3])
            + '\n\n👉 Hãy đặt `SUPABASE_SERVICE_ROLE_KEY` (lấy tại Project Settings → API → service_role secret) vào Streamlit Secrets.'
        )
    return info
