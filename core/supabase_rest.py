"""Client giao tiếp trực tiếp với Supabase PostgreSQL qua PostgREST (HTTPS JSON).

Ưu điểm trên Streamlit Community Cloud:
- Không phụ thuộc thư viện C nặng (libpq), tương thích 100% IPv4/IPv6 và Python 3.11-3.13.
- Ghi/cập nhật từng dòng nguyên tử (atomic row-level CRUD), triệt tiêu hoàn toàn lỗi ghi đè file SQLite.
- Tự động fallback sang SQLite cục bộ khi chạy unit test hoặc khi người dùng chưa chạy file SQL khởi tạo.
"""
import base64
import http.client
import json
import logging
import os
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .config import PROJECT_ROOT, cfg

log = logging.getLogger(__name__)

_PROBE_CACHE: dict[str, tuple[float, bool]] = {}
_PROBE_TTL_S = 300.0
_PROBE_FAIL_TTL_S = 60.0
_TLS = threading.local()
_SSL_CTX = ssl.create_default_context()
_VER_LOCK = threading.Lock()
_TABLE_VERSION: dict[str, int] = {}
_CACHE_EPOCH = 0


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
    """Nhận diện role từ khóa Supabase (hỗ trợ cả chuẩn mới sb_secret_/sb_publishable_ và JWT cũ)."""
    key = get_api_key()
    if not key:
        return 'unknown'
    if key.startswith('sb_secret_'):
        return 'service_role'
    if key.startswith('sb_publishable_'):
        return 'anon'
    if key.count('.') != 2:
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


def table_version(table: str) -> tuple[int, int]:
    """Return cache version token (epoch, write_count) for invalidation on table writes."""
    with _VER_LOCK:
        return (_CACHE_EPOCH, _TABLE_VERSION.get(table, 0))


def _bump_table(table: str) -> None:
    with _VER_LOCK:
        _TABLE_VERSION[table] = _TABLE_VERSION.get(table, 0) + 1


def reset_probe_cache() -> None:
    global _CACHE_EPOCH
    _PROBE_CACHE.clear()
    with _VER_LOCK:
        _CACHE_EPOCH += 1


def _has_proxy() -> bool:
    return any(os.environ.get(k) for k in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy'))


def _tls_conns() -> dict[tuple[str, str, int], http.client.HTTPConnection]:
    conns = getattr(_TLS, 'conns', None)
    if conns is None:
        conns = {}
        _TLS.conns = conns
    return conns


def _get_conn(scheme: str, host: str, port: int, timeout: int) -> tuple[http.client.HTTPConnection, bool]:
    conns = _tls_conns()
    key = (scheme, host, port)
    conn = conns.get(key)
    if conn is not None:
        return conn, True
    if scheme == 'https':
        conn = http.client.HTTPSConnection(host, port, timeout=timeout, context=_SSL_CTX)
    else:
        conn = http.client.HTTPConnection(host, port, timeout=timeout)
    conns[key] = conn
    return conn, False


def _drop_conn(key: tuple[str, str, int]) -> None:
    conns = _tls_conns()
    conn = conns.pop(key, None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass


def _headers(prefer: str = '') -> dict[str, str]:
    key = get_api_key()
    h = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Connection': 'keep-alive',
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
    data = json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None
    headers = _headers(prefer)

    if _has_proxy():
        url = f"{base}/rest/v1/{urllib.parse.quote(table)}{q}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode('utf-8').strip()
                return json.loads(raw) if raw else []
        except urllib.error.HTTPError as exc:
            err_text = exc.read().decode('utf-8', errors='ignore')
            if exc.code == 409 or '23505' in err_text:
                raise SupabaseConflictError(err_text) from exc
            raise RuntimeError(f'Supabase REST {method} /{table} HTTP {exc.code}: {err_text}') from exc

    parsed = urllib.parse.urlsplit(base)
    scheme = parsed.scheme.lower()
    host = parsed.hostname
    if not host:
        raise RuntimeError(f'SUPABASE_URL không hợp lệ: {base}')
    port = parsed.port or (443 if scheme == 'https' else 80)
    base_path = parsed.path.rstrip('/')
    path = f"{base_path}/rest/v1/{urllib.parse.quote(table)}{q}"
    key = (scheme, host, port)

    for attempt in range(2):
        conn, reused = _get_conn(scheme, host, port, timeout)
        try:
            conn.timeout = timeout
            if conn.sock is not None:
                conn.sock.settimeout(timeout)
            conn.request(method, path, body=data, headers=headers)
            resp = conn.getresponse()
            raw_bytes = resp.read()
            status = resp.status
            if resp.will_close:
                _drop_conn(key)
            break
        except (http.client.HTTPException, ConnectionResetError, BrokenPipeError, TimeoutError, OSError):
            _drop_conn(key)
            if reused and attempt == 0:
                continue
            raise

    raw = raw_bytes.decode('utf-8').strip()
    if 200 <= status < 300:
        return json.loads(raw) if raw else []
    if status == 409 or '23505' in raw:
        raise SupabaseConflictError(raw)
    raise RuntimeError(f'Supabase REST {method} /{table} HTTP {status}: {raw}')


def table_ready(table: str = 'reports', force: bool = False) -> bool:
    """Kiểm tra bảng PostgreSQL đã tồn tại và có quyền đọc/ghi hay chưa (có cache 300s/60s)."""
    if not is_configured():
        return False
    now = time.monotonic()
    cached = _PROBE_CACHE.get(table)
    if not force and cached:
        ttl = _PROBE_TTL_S if cached[1] else _PROBE_FAIL_TTL_S
        if now - cached[0] < ttl:
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
    _bump_table(table)
    return res if isinstance(res, list) else []


def update(table: str, filters: dict[str, str], payload: dict) -> list[dict]:
    if not filters:
        raise ValueError('Cần điều kiện filter khi UPDATE bảng Supabase.')
    res = _request('PATCH', table, params=filters, body=payload, prefer='return=representation')
    _bump_table(table)
    return res if isinstance(res, list) else []


def delete(table: str, filters: dict[str, str]) -> list[dict]:
    if not filters:
        raise ValueError('Cần điều kiện filter khi DELETE bảng Supabase.')
    res = _request('DELETE', table, params=filters, prefer='return=representation')
    _bump_table(table)
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
