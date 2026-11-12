"""Quản lý tài khoản cán bộ: tạo TK, xác thực mật khẩu, đổi mật khẩu.

Dùng hashlib.pbkdf2_hmac (thư viện chuẩn Python) thay vì bcrypt
để không cần cài thêm package nào.

Schema bảng officers:
    username TEXT PK, password_hash TEXT, full_name TEXT, unit TEXT,
    role TEXT (admin|officer), active INTEGER, created_at TEXT, last_login TEXT
"""
import hashlib
import hmac
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime

from .config import data_dir

_LOCK = threading.RLock()
_ITER = 260_000   # iterations PBKDF2


# ── Kết nối riêng (không chia sẻ với reports.db để tránh lock) ────────────

def _auth_db_path():
    return data_dir() / 'officers.db'


@contextmanager
def _conn():
    db = sqlite3.connect(_auth_db_path(), timeout=15)
    db.row_factory = sqlite3.Row
    try:
        yield db
        db.commit()
    finally:
        db.close()


def _ensure_table():
    with _conn() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS officers (
                username    TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                full_name   TEXT DEFAULT '',
                unit        TEXT DEFAULT '',
                role        TEXT DEFAULT 'officer',
                active      INTEGER DEFAULT 1,
                created_at  TEXT,
                last_login  TEXT
            )
        """)


def _ensure_initialized():
    """Khởi tạo bảng + tạo tài khoản admin mặc định nếu chưa có ai."""
    _ensure_table()
    with _conn() as db:
        count = db.execute('SELECT COUNT(*) FROM officers').fetchone()[0]
        if count == 0:
            # Tài khoản admin mặc định: admin / Admin@123
            _raw_create(db, username='admin', password='Admin@123',
                        full_name='Quản trị viên hệ thống',
                        unit='Ban Quản trị RoadWatch AI', role='admin')
            # Tài khoản cán bộ demo để test nhanh
            _raw_create(db, username='canbo01', password='canbo123',
                        full_name='Cán bộ Demo (Test)', unit='Đội Duy tu Đường bộ', role='officer')


# ── Helpers hash ──────────────────────────────────────────────────────────

def _hash_password(password: str, salt: bytes | None = None) -> str:
    """Trả về 'hex_salt$hex_hash'."""
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


def _raw_create(db, username, password, full_name='', unit='', role='officer'):
    db.execute(
        'INSERT INTO officers (username,password_hash,full_name,unit,role,active,created_at) VALUES (?,?,?,?,?,1,?)',
        (username.strip().lower(), _hash_password(password), full_name, unit, role,
         datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )


# ── API công khai ─────────────────────────────────────────────────────────

def login(username: str, password: str) -> dict | None:
    """Xác thực; trả về dict thông tin cán bộ hoặc None nếu sai."""
    _ensure_initialized()
    with _conn() as db:
        row = db.execute(
            'SELECT * FROM officers WHERE username=? AND active=1',
            (username.strip().lower(),)
        ).fetchone()
        if not row:
            return None
        if not _verify_password(password, row['password_hash']):
            return None
        db.execute('UPDATE officers SET last_login=? WHERE username=?',
                   (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), row['username']))
        return dict(row)


def list_officers() -> list[dict]:
    _ensure_initialized()
    with _conn() as db:
        return [dict(r) for r in db.execute(
            'SELECT username,full_name,unit,role,active,created_at,last_login FROM officers ORDER BY created_at'
        ).fetchall()]


def create_officer(username: str, password: str, full_name: str, unit: str, role: str = 'officer') -> str | None:
    """Tạo TK mới. Trả None nếu username đã tồn tại."""
    _ensure_initialized()
    username = username.strip().lower()
    if not username or not password:
        return 'Tên đăng nhập và mật khẩu không được để trống.'
    if len(password) < 6:
        return 'Mật khẩu tối thiểu 6 ký tự.'
    try:
        with _conn() as db:
            _raw_create(db, username, password, full_name, unit, role)
        return None  # None = thành công
    except sqlite3.IntegrityError:
        return f'Tên đăng nhập "{username}" đã tồn tại.'


def change_password(username: str, old_pw: str, new_pw: str) -> str | None:
    """Đổi mật khẩu. Trả None nếu thành công, chuỗi lỗi nếu thất bại."""
    _ensure_initialized()
    officer = login(username, old_pw)
    if not officer:
        return 'Mật khẩu hiện tại không đúng.'
    if len(new_pw) < 6:
        return 'Mật khẩu mới tối thiểu 6 ký tự.'
    with _conn() as db:
        db.execute('UPDATE officers SET password_hash=? WHERE username=?',
                   (_hash_password(new_pw), username.strip().lower()))
    return None


def reset_password(username: str, new_pw: str) -> str | None:
    """Admin reset mật khẩu (không cần mật khẩu cũ)."""
    _ensure_initialized()
    if len(new_pw) < 6:
        return 'Mật khẩu tối thiểu 6 ký tự.'
    with _conn() as db:
        rows = db.execute('UPDATE officers SET password_hash=? WHERE username=?',
                          (_hash_password(new_pw), username.strip().lower())).rowcount
    return None if rows else f'Không tìm thấy tài khoản "{username}".'


def toggle_active(username: str) -> bool:
    """Bật/tắt tài khoản. Trả về trạng thái mới (True = active)."""
    _ensure_initialized()
    with _conn() as db:
        row = db.execute('SELECT active FROM officers WHERE username=?',
                         (username.strip().lower(),)).fetchone()
        if not row:
            return False
        new_state = 0 if row['active'] else 1
        db.execute('UPDATE officers SET active=? WHERE username=?',
                   (new_state, username.strip().lower()))
    return bool(new_state)


def is_admin(username: str) -> bool:
    _ensure_initialized()
    with _conn() as db:
        r = db.execute('SELECT role FROM officers WHERE username=?',
                       (username.strip().lower(),)).fetchone()
        return bool(r and r['role'] == 'admin')
