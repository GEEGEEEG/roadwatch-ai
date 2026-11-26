"""Quản lý tài khoản cán bộ, phân quyền 3 cấp (RBAC) & chống dò mật khẩu (Brute-force Lockout).

Hỗ trợ lưu trữ bền vững trên bảng `public.officers` của Supabase PostgreSQL
(tự động fallback về `officers.db` cục bộ khi chạy offline / unit test).

Các vai trò (role):
- 'admin'      : Quản trị viên hệ thống (quản lý TK, cấu hình AHP/đơn giá, sao lưu/khôi phục)
- 'officer'    : Cán bộ thẩm định & điều phối (duyệt/từ chối/gộp, lập lộ trình, xuất báo cáo)
- 'field_team' : Đội duy tu hiện trường (tuần đường, xem việc được giao, tải ảnh nghiệm thu)
"""
import hashlib
import hmac
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta

from . import supabase_rest
from .config import cfg, data_dir, demo_mode_enabled, now_vn

_LOCK = threading.RLock()
_ITER = 260_000
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 10
VALID_ROLES = ('admin', 'officer', 'field_team')
_SEED_CACHE: dict[tuple, float] = {}
_ADMIN_CACHE: dict[tuple, tuple[float, bool]] = {}
_SEED_TTL_S = 300.0
_ADMIN_TRUE_TTL_S = 300.0
_ADMIN_FALSE_TTL_S = 30.0


def invalidate_auth_cache() -> None:
    """Clear in-memory Postgres auth seed/admin caches after account mutations."""
    _SEED_CACHE.clear()
    _ADMIN_CACHE.clear()


def _using_postgres() -> bool:
    return supabase_rest.table_ready('officers')


def _auth_db_path():
    return data_dir() / 'officers.db'


@contextmanager
def _conn():
    db = sqlite3.connect(_auth_db_path(), timeout=15)
    db.row_factory = sqlite3.Row
    try:
        db.execute('PRAGMA journal_mode=WAL')
        yield db
        db.commit()
    finally:
        db.close()


def _hash_password(password: str, salt: bytes | None = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, _ITER)
    return salt.hex() + '$' + h.hex()


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split('$', 1)
        salt = bytes.fromhex(salt_hex)
        h = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, _ITER)
        return hmac.compare_digest(h.hex(), hash_hex)
    except Exception:
        return False


def _bootstrap_admin_password() -> str:
    """Lấy mật khẩu khởi tạo Admin từ Streamlit Secrets (ROADWATCH_ADMIN_PASSWORD hoặc ROADWATCH_OFFICER_PASSWORD)."""
    return cfg('ROADWATCH_ADMIN_PASSWORD') or cfg('ROADWATCH_OFFICER_PASSWORD')


def _demo_credentials() -> tuple[str, str]:
    user = cfg('ROADWATCH_DEMO_USER', 'canbo_demo') or 'canbo_demo'
    pw = cfg('ROADWATCH_DEMO_PASSWORD', 'Demo@RoadWatch2026') or 'Demo@RoadWatch2026'
    return user.strip().lower(), pw


def get_demo_account_hint() -> tuple[str, str] | None:
    """Chỉ trả về thông tin tài khoản Demo khi ROADWATCH_DEMO_MODE được bật."""
    if not demo_mode_enabled():
        return None
    return _demo_credentials()


def _ensure_local_table():
    with _conn() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS officers (
                username        TEXT PRIMARY KEY,
                password_hash   TEXT NOT NULL,
                full_name       TEXT DEFAULT '',
                unit            TEXT DEFAULT '',
                role            TEXT DEFAULT 'officer',
                active          INTEGER DEFAULT 1,
                failed_attempts INTEGER DEFAULT 0,
                locked_until    TEXT DEFAULT NULL,
                created_at      TEXT,
                last_login      TEXT
            )
        """)
        have = {r[1] for r in db.execute('PRAGMA table_info(officers)')}
        if 'failed_attempts' not in have:
            db.execute('ALTER TABLE officers ADD COLUMN failed_attempts INTEGER DEFAULT 0')
        if 'locked_until' not in have:
            db.execute('ALTER TABLE officers ADD COLUMN locked_until TEXT DEFAULT NULL')


def _seed_accounts_if_empty():
    now_s = now_vn().strftime('%Y-%m-%d %H:%M:%S')
    boot_pw = _bootstrap_admin_password()
    demo_on = demo_mode_enabled()
    demo_user, demo_pw = _demo_credentials()

    if _using_postgres():
        seed_key = (supabase_rest.get_url(), demo_on, demo_user, supabase_rest.table_version('officers')[0])
        ts = _SEED_CACHE.get(seed_key)
        if ts is not None and (time.monotonic() - ts < _SEED_TTL_S):
            return
        existing = supabase_rest.select('officers', columns='username', limit=1)
        if existing:
            # Nếu bật chế độ Demo mà chưa có TK demo thì bổ sung TK demo quyền officer
            if demo_on:
                has_demo = supabase_rest.select('officers', filters={'username': f'eq.{demo_user}'}, columns='username', limit=1)
                if not has_demo:
                    supabase_rest.insert('officers', {
                        'username': demo_user,
                        'password_hash': _hash_password(demo_pw),
                        'full_name': 'Cán bộ Demo (Hội đồng đánh giá)',
                        'unit': 'Đội Duy tu Đường bộ (Demo)',
                        'role': 'officer',
                        'active': 1,
                        'failed_attempts': 0,
                        'created_at': now_s,
                    }, upsert=True)
            _SEED_CACHE[seed_key] = time.monotonic()
            return

        seed_rows = []
        if boot_pw:
            seed_rows.append({
                'username': 'admin',
                'password_hash': _hash_password(boot_pw),
                'full_name': 'Quản trị viên hệ thống',
                'unit': 'Ban Quản trị RoadWatch AI',
                'role': 'admin',
                'active': 1,
                'failed_attempts': 0,
                'created_at': now_s,
            })
        if demo_on:
            seed_rows.append({
                'username': demo_user,
                'password_hash': _hash_password(demo_pw),
                'full_name': 'Cán bộ Demo (Hội đồng đánh giá)',
                'unit': 'Đội Duy tu Đường bộ (Demo)',
                'role': 'officer',
                'active': 1,
                'failed_attempts': 0,
                'created_at': now_s,
            })
        if seed_rows:
            supabase_rest.insert('officers', seed_rows, upsert=True)
        _SEED_CACHE[seed_key] = time.monotonic()
        return

    # Fallback SQLite cục bộ
    _ensure_local_table()
    with _conn() as db:
        count = db.execute('SELECT COUNT(*) FROM officers').fetchone()[0]
        if count == 0:
            admin_pw = boot_pw or ('Admin@LocalDev' if demo_on else '')
            if admin_pw:
                db.execute(
                    'INSERT INTO officers (username,password_hash,full_name,unit,role,active,failed_attempts,created_at) VALUES (?,?,?,?,?,1,0,?)',
                    ('admin', _hash_password(admin_pw), 'Quản trị viên hệ thống', 'Ban Quản trị RoadWatch AI', 'admin', now_s),
                )
            if demo_on:
                db.execute(
                    'INSERT OR IGNORE INTO officers (username,password_hash,full_name,unit,role,active,failed_attempts,created_at) VALUES (?,?,?,?,?,1,0,?)',
                    (demo_user, _hash_password(demo_pw), 'Cán bộ Demo (Hội đồng đánh giá)', 'Đội Duy tu Đường bộ (Demo)', 'officer', now_s),
                )


def has_any_admin() -> bool:
    """Kiểm tra hệ thống đã có tài khoản Quản trị viên nào chưa (phục vụ thiết lập lần đầu)."""
    if _using_postgres():
        adm_key = (supabase_rest.get_url(), supabase_rest.table_version('officers')[0])
        cached = _ADMIN_CACHE.get(adm_key)
        if cached is not None:
            ts, val = cached
            ttl = _ADMIN_TRUE_TTL_S if val else _ADMIN_FALSE_TTL_S
            if time.monotonic() - ts < ttl:
                return val
        _seed_accounts_if_empty()
        rows = supabase_rest.select('officers', filters={'role': 'eq.admin', 'active': 'eq.1'}, columns='username', limit=1)
        found = bool(rows)
        _ADMIN_CACHE[adm_key] = (time.monotonic(), found)
        return found
    _seed_accounts_if_empty()
    with _conn() as db:
        row = db.execute("SELECT 1 FROM officers WHERE role='admin' AND active=1 LIMIT 1").fetchone()
        return bool(row)


def bootstrap_first_admin(username: str, password: str, full_name: str = 'Quản trị viên hệ thống') -> str | None:
    """Cho phép khởi tạo tài khoản Admin đầu tiên khi hệ thống mới tinh chưa có Admin nào."""
    if has_any_admin():
        return 'Hệ thống đã có Quản trị viên. Vui lòng đăng nhập bằng tài khoản hiện có.'
    if len(password or '') < 8:
        return 'Mật khẩu Quản trị viên cần tối thiểu 8 ký tự.'
    err = create_officer(username, password, full_name, 'Ban Quản trị RoadWatch AI', role='admin')
    if err is None:
        invalidate_auth_cache()
    return err


def _get_officer_row(username: str) -> dict | None:
    u = (username or '').strip().lower()
    if not u:
        return None
    if _using_postgres():
        rows = supabase_rest.select('officers', filters={'username': f'eq.{u}'}, limit=1)
        return rows[0] if rows else None
    with _conn() as db:
        row = db.execute('SELECT * FROM officers WHERE username=?', (u,)).fetchone()
        return dict(row) if row else None


def _update_officer_fields(username: str, **fields) -> int:
    u = username.strip().lower()
    if _using_postgres():
        updated = supabase_rest.update('officers', {'username': f'eq.{u}'}, fields)
        return len(updated)
    sets = ', '.join(f'{k}=?' for k in fields)
    with _conn() as db:
        return db.execute(f'UPDATE officers SET {sets} WHERE username=?', [*fields.values(), u]).rowcount


def login_with_status(username: str, password: str) -> tuple[dict | None, str | None]:
    """Xác thực đăng nhập kèm thông báo khóa tạm nếu sai quá nhiều lần.
    Trả về (officer_dict, None) nếu thành công, hoặc (None, error_message) nếu thất bại."""
    with _LOCK:
        _seed_accounts_if_empty()
        u = (username or '').strip().lower()
        if not u or not password:
            return None, 'Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.'

        row = _get_officer_row(u)
        if not row or not int(row.get('active', 1)):
            return None, 'Tên đăng nhập/mật khẩu không đúng hoặc tài khoản đã bị vô hiệu hóa.'

        now = now_vn()
        locked_until_str = row.get('locked_until')
        if locked_until_str:
            try:
                locked_dt = datetime.fromisoformat(str(locked_until_str))
                if locked_dt > now:
                    mins = max(1, int((locked_dt - now).total_seconds() // 60) + 1)
                    return None, f'Tài khoản tạm khóa do nhập sai nhiều lần. Vui lòng thử lại sau {mins} phút.'
            except ValueError:
                pass

        if not _verify_password(password, row['password_hash']):
            fails = int(row.get('failed_attempts') or 0) + 1
            if fails >= MAX_FAILED_ATTEMPTS:
                until = (now + timedelta(minutes=LOCKOUT_MINUTES)).strftime('%Y-%m-%d %H:%M:%S')
                _update_officer_fields(u, failed_attempts=fails, locked_until=until)
                return None, f'Nhập sai {MAX_FAILED_ATTEMPTS} lần liên tiếp. Tài khoản tạm khóa {LOCKOUT_MINUTES} phút.'
            _update_officer_fields(u, failed_attempts=fails)
            return None, 'Tên đăng nhập hoặc mật khẩu không đúng.'

        now_s = now.strftime('%Y-%m-%d %H:%M:%S')
        needs_sync_reset = bool(int(row.get('failed_attempts') or 0) or row.get('locked_until'))
        if _using_postgres() and not needs_sync_reset:
            def _bg_touch(uname: str = u, ts: str = now_s) -> None:
                try:
                    _update_officer_fields(uname, last_login=ts)
                except Exception:
                    pass
            threading.Thread(target=_bg_touch, daemon=True).start()
        else:
            _update_officer_fields(u, failed_attempts=0, locked_until=None, last_login=now_s)
        row['last_login'] = now_s
        row.pop('password_hash', None)
        return row, None


def login(username: str, password: str) -> dict | None:
    """API tương thích ngược: trả về dict cán bộ hoặc None."""
    officer, _ = login_with_status(username, password)
    return officer


def list_officers() -> list[dict]:
    _seed_accounts_if_empty()
    cols = 'username,full_name,unit,role,active,created_at,last_login'
    if _using_postgres():
        return supabase_rest.select('officers', columns=cols, order='created_at.asc')
    with _conn() as db:
        return [dict(r) for r in db.execute(f'SELECT {cols} FROM officers ORDER BY created_at').fetchall()]


def create_officer(username: str, password: str, full_name: str, unit: str, role: str = 'officer') -> str | None:
    _seed_accounts_if_empty()
    u = (username or '').strip().lower()
    if not u or not password:
        return 'Tên đăng nhập và mật khẩu không được để trống.'
    if len(password) < 6:
        return 'Mật khẩu tối thiểu 6 ký tự.'
    role = role if role in VALID_ROLES else 'officer'
    payload = {
        'username': u,
        'password_hash': _hash_password(password),
        'full_name': (full_name or '').strip(),
        'unit': (unit or '').strip(),
        'role': role,
        'active': 1,
        'failed_attempts': 0,
        'locked_until': None,
        'created_at': now_vn().strftime('%Y-%m-%d %H:%M:%S'),
    }
    if _using_postgres():
        try:
            supabase_rest.insert('officers', payload)
            invalidate_auth_cache()
            return None
        except supabase_rest.SupabaseConflictError:
            return f'Tên đăng nhập "{u}" đã tồn tại.'
    try:
        with _conn() as db:
            db.execute(
                'INSERT INTO officers (username,password_hash,full_name,unit,role,active,failed_attempts,created_at) VALUES (?,?,?,?,?,1,0,?)',
                (u, payload['password_hash'], payload['full_name'], payload['unit'], role, payload['created_at']),
            )
        return None
    except sqlite3.IntegrityError:
        return f'Tên đăng nhập "{u}" đã tồn tại.'


def change_password(username: str, old_pw: str, new_pw: str) -> str | None:
    _seed_accounts_if_empty()
    row = _get_officer_row(username)
    if not row or not _verify_password(old_pw, row['password_hash']):
        return 'Mật khẩu hiện tại không đúng.'
    if len(new_pw or '') < 6:
        return 'Mật khẩu mới tối thiểu 6 ký tự.'
    _update_officer_fields(username, password_hash=_hash_password(new_pw), failed_attempts=0, locked_until=None)
    return None


def reset_password(username: str, new_pw: str) -> str | None:
    _seed_accounts_if_empty()
    if len(new_pw or '') < 6:
        return 'Mật khẩu tối thiểu 6 ký tự.'
    rows = _update_officer_fields(username, password_hash=_hash_password(new_pw), failed_attempts=0, locked_until=None)
    return None if rows else f'Không tìm thấy tài khoản "{username}".'


def toggle_active(username: str) -> bool:
    _seed_accounts_if_empty()
    row = _get_officer_row(username)
    if not row:
        return False
    new_state = 0 if int(row.get('active', 1)) else 1
    _update_officer_fields(username, active=new_state)
    invalidate_auth_cache()
    return bool(new_state)


def is_admin(username: str) -> bool:
    _seed_accounts_if_empty()
    row = _get_officer_row(username)
    return bool(row and row.get('role') == 'admin' and int(row.get('active', 1)))
