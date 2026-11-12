"""SQLite: bản ghi báo cáo + lịch sử trạng thái.

Đồng bộ Google Drive (tùy chọn): nếu GDRIVE_FOLDER_ID và
GDRIVE_SERVICE_ACCOUNT_JSON được đặt trong Streamlit Secrets,
- init() kéo roadwatch.db từ Drive về local trước khi dùng.
- insert_report / update_report / add_history đẩy DB lên Drive sau mỗi lần ghi.
"""
import logging
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime

import pandas as pd

from .config import data_dir

log = logging.getLogger(__name__)
_INIT_LOCK = threading.RLock()
_INITIALIZED_PATHS = set()

COLUMNS = [
    'id', 'created_at', 'image_hash', 'image_file', 'annotated_file', 'location_name',
    'latitude', 'longitude', 'gps_source', 'gps_accuracy_m', 'captured_at', 'status', 'source', 'capture_method', 'contact', 'consent',
    'total_boxes', 'count_D00', 'count_D10', 'count_D20', 'count_D40', 'avg_confidence',
    'bbox_union_pct', 'damage_area_m2', 'damage_volume_l', 'damage_depth_desc',
    'ai_level', 'ai_score', 'final_level', 'final_score', 'road_type', 'road_score',
    'note', 'quality_flags', 'screen_flags', 'detections_json', 'elapsed_ms',
    'reviewed_by', 'reviewed_at', 'reject_reason', 'assigned_to', 'due_date',
    'fixed_at', 'after_image_file', 'after_boxes', 'merged_into',
]
NUMERIC = ['latitude', 'longitude', 'gps_accuracy_m', 'total_boxes', 'count_D00', 'count_D10', 'count_D20', 'count_D40',
           'avg_confidence', 'bbox_union_pct', 'damage_area_m2', 'damage_volume_l', 'ai_score', 'final_score', 'road_score', 'elapsed_ms',
           'consent', 'after_boxes']
INT_COLS = {'consent', 'total_boxes', 'count_D00', 'count_D10', 'count_D20', 'count_D40', 'after_boxes'}
REAL_COLS = {'latitude', 'longitude', 'gps_accuracy_m', 'avg_confidence', 'bbox_union_pct', 'damage_area_m2', 'damage_volume_l',
             'ai_score', 'final_score', 'road_score', 'elapsed_ms'}


class DuplicateImage(Exception):
    def __init__(self, existing_id):
        super().__init__(f'Ảnh đã tồn tại: {existing_id}')
        self.existing_id = existing_id


def _col_type(c):
    return 'INTEGER' if c in INT_COLS else ('REAL' if c in REAL_COLS else 'TEXT')


def db_path():
    return data_dir() / 'roadwatch.db'


@contextmanager
def connect():
    conn = sqlite3.connect(db_path(), timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init():
    db_file = db_path()
    key = str(db_file.resolve())
    with _INIT_LOCK:
        if key in _INITIALIZED_PATHS and db_file.is_file():
            _initialize_schema()  # Nhanh trên local; vẫn tự sửa schema nếu DB vừa khôi phục.
            return
        _pull_db()   # Chỉ khôi phục bản sao Drive một lần mỗi phiên máy chủ, tránh tải mỗi rerun.
        _initialize_schema()
        _INITIALIZED_PATHS.add(key)

def _initialize_schema():
    cols = ', '.join(
        f'{c} TEXT PRIMARY KEY' if c == 'id' else
        f'{c} TEXT UNIQUE' if c == 'image_hash' else f'{c} {_col_type(c)}' for c in COLUMNS)
    with connect() as conn:
        conn.execute(f'CREATE TABLE IF NOT EXISTS reports ({cols})')
        conn.execute('CREATE TABLE IF NOT EXISTS history (report_id TEXT, ts TEXT, status TEXT, actor TEXT, note TEXT)')
        have = {r[1] for r in conn.execute('PRAGMA table_info(reports)')}
        for c in COLUMNS:   # DB cũ chưa có cột mới (ví dụ merged_into) thì thêm vào
            if c not in have:
                conn.execute(f'ALTER TABLE reports ADD COLUMN {c} {_col_type(c)}')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status)')


def new_id(image_hash=''):
    return 'RW-' + datetime.now().strftime('%Y%m%d%H%M%S') + '-' + (image_hash[:4] or uuid.uuid4().hex[:4])


def find_by_hash(image_hash):
    with connect() as conn:
        row = conn.execute('SELECT id FROM reports WHERE image_hash=?', (image_hash,)).fetchone()
    return row['id'] if row else None


def insert_report(row: dict) -> str:
    init()
    row = {k: v for k, v in row.items() if k in COLUMNS}
    row.setdefault('id', new_id(row.get('image_hash', '')))
    row.setdefault('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    existing = find_by_hash(row.get('image_hash')) if row.get('image_hash') else None
    if existing:
        raise DuplicateImage(existing)
    names = ', '.join(row)
    marks = ', '.join('?' for _ in row)
    try:
        with connect() as conn:
            conn.execute(f'INSERT INTO reports ({names}) VALUES ({marks})', list(row.values()))
    except sqlite3.IntegrityError:
        raise DuplicateImage(find_by_hash(row.get('image_hash')) or '?')
    add_history(row['id'], row.get('status', 'pending'), row.get('reviewed_by') or row.get('source', ''), 'Tạo bản ghi')
    _push_db()   # đẩy DB lên Drive sau khi ghi
    return row['id']


def update_report(report_id: str, **fields):
    fields = {k: v for k, v in fields.items() if k in COLUMNS and k != 'id'}
    if not fields:
        return
    sets = ', '.join(f'{k}=?' for k in fields)
    with connect() as conn:
        conn.execute(f'UPDATE reports SET {sets} WHERE id=?', [*fields.values(), report_id])
    _push_db()   # đẩy DB lên Drive sau khi cập nhật


def add_history(report_id, status, actor='', note=''):
    with connect() as conn:
        conn.execute('INSERT INTO history VALUES (?,?,?,?,?)',
                     (report_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), status, actor, note))
    _push_db()   # đẩy DB lên Drive sau khi ghi lịch sử


def get_history(report_id) -> pd.DataFrame:
    init()
    with connect() as conn:
        return pd.read_sql_query('SELECT ts, status, actor, note FROM history WHERE report_id=? ORDER BY ts',
                                 conn, params=(report_id,))


def fetch_df(statuses=None) -> pd.DataFrame:
    init()
    query, params = 'SELECT * FROM reports', []
    if statuses:
        query += ' WHERE status IN (%s)' % ','.join('?' for _ in statuses)
        params = list(statuses)
    with connect() as conn:
        df = pd.read_sql_query(query + ' ORDER BY created_at', conn, params=params)
    for c in NUMERIC:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df


def get_report(report_id):
    df = fetch_df()
    hit = df[df.id == report_id]
    return None if hit.empty else hit.iloc[0].to_dict()


# ── Google Drive sync (tùy chọn) ──────────────────────────────────────────

def _pull_db() -> None:
    """Kéo roadwatch.db từ Drive về local nếu Drive được cấu hình.
    Gọi ở đầu init() — no-op nếu Drive chưa đặt hoặc file chưa có trên Drive."""
    try:
        from . import gdrive
        if not gdrive.is_enabled():
            return
        data = gdrive.download('roadwatch.db')
        if data:
            p = db_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            log.info('Đã kéo roadwatch.db từ Google Drive (%d bytes).', len(data))
        else:
            log.info('GDrive: chưa có roadwatch.db trên Drive, dùng DB local.')
    except Exception as exc:
        log.warning('Kéo DB từ Drive thất bại (dùng DB local): %s', exc)


def _push_db() -> None:
    """Đẩy roadwatch.db lên Drive sau mỗi lần ghi.
    No-op nếu Drive chưa cấu hình hoặc file chưa tồn tại."""
    try:
        from . import gdrive
        if not gdrive.is_enabled():
            return
        p = db_path()
        if not p.is_file():
            return
        gdrive.upload('roadwatch.db', p.read_bytes(), 'application/x-sqlite3')
    except Exception as exc:
        log.warning('Đẩy DB lên Drive thất bại: %s', exc)
