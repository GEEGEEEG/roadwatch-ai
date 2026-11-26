"""Tầng Cơ sở dữ liệu hợp nhất (RoadWatch AI v5.0):
- Ưu tiên số 1: Supabase PostgreSQL (ghi từng bản ghi nguyên tử, chịu tải đa người dùng, không bao giờ mất dữ liệu khi reboot).
- Tương thích / Kiểm thử cục bộ: SQLite ở chế độ WAL khi chạy offline hoặc pytest.
"""
import json
import logging
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any

import pandas as pd

from . import supabase_rest
from .config import data_dir, now_vn

log = logging.getLogger(__name__)
_INIT_LOCK = threading.RLock()
_INITIALIZED_PATHS: set[str] = set()
_DF_CACHE: dict[tuple, tuple[float, pd.DataFrame]] = {}
_SETTING_CACHE: dict[tuple, tuple[float, Any]] = {}
_DF_TTL_S = 20.0
_SETTING_TTL_S = 60.0
_MISSING = object()


def invalidate_cache() -> None:
    """Clear short-TTL Postgres report/setting caches."""
    _DF_CACHE.clear()
    _SETTING_CACHE.clear()

COLUMNS = [
    'id', 'created_at', 'image_hash', 'dhash_64', 'color_vec', 'image_file', 'annotated_file', 'location_name',
    'latitude', 'longitude', 'gps_source', 'gps_accuracy_m', 'captured_at', 'status', 'source', 'capture_method',
    'contact', 'consent', 'total_boxes', 'count_D00', 'count_D10', 'count_D20', 'count_D40', 'avg_confidence',
    'bbox_union_pct', 'damage_area_m2', 'damage_volume_l', 'damage_depth_desc',
    'ai_level', 'ai_score', 'final_level', 'final_score', 'road_type', 'road_score',
    'note', 'quality_flags', 'screen_flags', 'detections_json', 'elapsed_ms',
    'reviewed_by', 'reviewed_at', 'reject_reason', 'assigned_to', 'due_date',
    'fixed_at', 'after_image_file', 'after_boxes', 'merged_into',
]
NUMERIC = [
    'latitude', 'longitude', 'gps_accuracy_m', 'total_boxes', 'count_D00', 'count_D10', 'count_D20', 'count_D40',
    'avg_confidence', 'bbox_union_pct', 'damage_area_m2', 'damage_volume_l', 'ai_score', 'final_score',
    'road_score', 'elapsed_ms', 'consent', 'after_boxes',
]
INT_COLS = {'consent', 'total_boxes', 'count_D00', 'count_D10', 'count_D20', 'count_D40', 'after_boxes'}
REAL_COLS = {
    'latitude', 'longitude', 'gps_accuracy_m', 'avg_confidence', 'bbox_union_pct', 'damage_area_m2',
    'damage_volume_l', 'ai_score', 'final_score', 'road_score', 'elapsed_ms',
}


class DuplicateImage(Exception):
    def __init__(self, existing_id: str):
        super().__init__(f'Ảnh đã tồn tại: {existing_id}')
        self.existing_id = existing_id


def using_postgres() -> bool:
    """True nếu đang đọc/ghi trực tiếp trên bảng Supabase PostgreSQL."""
    return supabase_rest.table_ready('reports')


def _col_type(c: str) -> str:
    return 'INTEGER' if c in INT_COLS else ('REAL' if c in REAL_COLS else 'TEXT')


def db_path():
    return data_dir() / 'roadwatch.db'


@contextmanager
def connect():
    conn = sqlite3.connect(db_path(), timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA journal_mode=WAL')
        yield conn
        conn.commit()
    finally:
        conn.close()


def init():
    if using_postgres():
        return
    db_file = db_path()
    key = str(db_file.resolve())
    with _INIT_LOCK:
        if key in _INITIALIZED_PATHS and db_file.is_file():
            _initialize_schema()
            return
        _pull_legacy_db_if_needed()
        _initialize_schema()
        _INITIALIZED_PATHS.add(key)


def _initialize_schema():
    cols = ', '.join(
        f'{c} TEXT PRIMARY KEY' if c == 'id' else
        f'{c} TEXT UNIQUE' if c == 'image_hash' else f'{c} {_col_type(c)}'
        for c in COLUMNS
    )
    with connect() as conn:
        conn.execute(f'CREATE TABLE IF NOT EXISTS reports ({cols})')
        conn.execute('CREATE TABLE IF NOT EXISTS history (report_id TEXT, ts TEXT, status TEXT, actor TEXT, note TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value_json TEXT, updated_at TEXT, updated_by TEXT)')
        have = {r[1] for r in conn.execute('PRAGMA table_info(reports)')}
        for c in COLUMNS:
            if c not in have:
                conn.execute(f'ALTER TABLE reports ADD COLUMN {c} {_col_type(c)}')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status)')


def new_id(image_hash: str = '') -> str:
    return 'RW-' + now_vn().strftime('%Y%m%d%H%M%S') + '-' + (image_hash[:4] or uuid.uuid4().hex[:4])


def _clean_row(row: dict) -> dict:
    cleaned = {}
    for k, v in row.items():
        if k not in COLUMNS:
            continue
        if v is None:
            cleaned[k] = None
        elif k in INT_COLS:
            cleaned[k] = int(v)
        elif k in REAL_COLS:
            cleaned[k] = float(v)
        else:
            cleaned[k] = str(v)
    return cleaned


def find_by_hash(image_hash: str) -> str | None:
    if not image_hash:
        return None
    if using_postgres():
        rows = supabase_rest.select('reports', filters={'image_hash': f'eq.{image_hash}'}, columns='id', limit=1)
        return rows[0]['id'] if rows else None
    init()
    with connect() as conn:
        row = conn.execute('SELECT id FROM reports WHERE image_hash=?', (image_hash,)).fetchone()
    return row['id'] if row else None


def insert_report(row: dict) -> str:
    clean = _clean_row(row)
    clean.setdefault('id', new_id(clean.get('image_hash', '') or ''))
    clean.setdefault('created_at', now_vn().strftime('%Y-%m-%d %H:%M:%S'))
    img_hash = clean.get('image_hash')
    existing = find_by_hash(img_hash) if img_hash else None
    if existing:
        raise DuplicateImage(existing)

    if using_postgres():
        try:
            supabase_rest.insert('reports', clean)
        except supabase_rest.SupabaseConflictError as exc:
            raise DuplicateImage(find_by_hash(img_hash or '') or '?') from exc
        add_history(
            clean['id'],
            clean.get('status') or 'pending',
            clean.get('reviewed_by') or clean.get('source') or '',
            'Tạo bản ghi',
        )
        return clean['id']

    init()
    names = ', '.join(clean)
    marks = ', '.join('?' for _ in clean)
    try:
        with connect() as conn:
            conn.execute(f'INSERT INTO reports ({names}) VALUES ({marks})', list(clean.values()))
    except sqlite3.IntegrityError as exc:
        raise DuplicateImage(find_by_hash(img_hash or '') or '?') from exc
    add_history(
        clean['id'],
        clean.get('status') or 'pending',
        clean.get('reviewed_by') or clean.get('source') or '',
        'Tạo bản ghi',
    )
    _push_legacy_db_if_needed()
    return clean['id']


def update_report(report_id: str, **fields) -> None:
    clean = {k: v for k, v in _clean_row(fields).items() if k != 'id'}
    if not clean:
        return
    if using_postgres():
        supabase_rest.update('reports', {'id': f'eq.{report_id}'}, clean)
        return
    init()
    sets = ', '.join(f'{k}=?' for k in clean)
    with connect() as conn:
        conn.execute(f'UPDATE reports SET {sets} WHERE id=?', [*clean.values(), report_id])
    _push_legacy_db_if_needed()


def update_reports_bulk(report_ids: list[str], **fields) -> int:
    """Cập nhật hàng loạt bản ghi trong 1 truy vấn duy nhất (dùng khi giao việc hoặc nghiệm thu cụm)."""
    ids = [str(x) for x in report_ids if x]
    clean = {k: v for k, v in _clean_row(fields).items() if k != 'id'}
    if not ids or not clean:
        return 0
    if using_postgres():
        joined = ','.join(ids)
        supabase_rest.update('reports', {'id': f'in.({joined})'}, clean)
        return len(ids)
    init()
    sets = ', '.join(f'{k}=?' for k in clean)
    marks = ', '.join('?' for _ in ids)
    with connect() as conn:
        cur = conn.execute(f'UPDATE reports SET {sets} WHERE id IN ({marks})', [*clean.values(), *ids])
        updated_count = cur.rowcount
    _push_legacy_db_if_needed()
    return updated_count


def add_history(report_id: str, status: str, actor: str = '', note: str = '') -> None:
    ts = now_vn().strftime('%Y-%m-%d %H:%M:%S')
    if using_postgres() and supabase_rest.table_ready('report_history'):
        supabase_rest.insert('report_history', {
            'report_id': str(report_id),
            'ts': ts,
            'status': str(status),
            'actor': str(actor or ''),
            'note': str(note or ''),
        })
        return
    init()
    with connect() as conn:
        conn.execute('INSERT INTO history VALUES (?,?,?,?,?)', (report_id, ts, status, actor, note))
    _push_legacy_db_if_needed()


def add_history_bulk(entries_or_ids, status: str = '', actor: str = '', note: str = '') -> None:
    """Ghi lịch sử theo lô: hỗ trợ cả [(rid, st, ac, nt), ...] hoặc (ids, status, actor, note)."""
    if not entries_or_ids:
        return
    first = entries_or_ids[0]
    if isinstance(first, (tuple, list)):
        entries = entries_or_ids
    else:
        entries = [(str(rid), str(status), str(actor or ''), str(note or '')) for rid in entries_or_ids]
    ts = now_vn().strftime('%Y-%m-%d %H:%M:%S')
    if using_postgres() and supabase_rest.table_ready('report_history'):
        payload = [
            {'report_id': str(rid), 'ts': ts, 'status': str(st), 'actor': str(ac or ''), 'note': str(nt or '')}
            for rid, st, ac, nt in entries
        ]
        supabase_rest.insert('report_history', payload)
        return
    init()
    with connect() as conn:
        conn.executemany(
            'INSERT INTO history VALUES (?,?,?,?,?)',
            [(str(rid), ts, str(st), str(ac or ''), str(nt or '')) for rid, st, ac, nt in entries],
        )
    _push_legacy_db_if_needed()


def get_history(report_id: str) -> pd.DataFrame:
    if using_postgres() and supabase_rest.table_ready('report_history'):
        rows = supabase_rest.select(
            'report_history',
            filters={'report_id': f'eq.{report_id}'},
            columns='ts,status,actor,note',
            order='ts.asc',
        )
        return pd.DataFrame(rows, columns=['ts', 'status', 'actor', 'note'])
    init()
    with connect() as conn:
        return pd.read_sql_query(
            'SELECT ts, status, actor, note FROM history WHERE report_id=? ORDER BY ts',
            conn,
            params=(report_id,),
        )


def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[COLUMNS].copy()
    for c in NUMERIC:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df


SCREENING_COLUMNS = [
    'id', 'created_at', 'status', 'location_name', 'latitude', 'longitude', 'dhash_64', 'color_vec', 'image_file',
]


def fetch_screening_df(limit: int = 400) -> pd.DataFrame:
    """Truy vấn siêu nhẹ chỉ lấy 9 cột tọa độ & vector thị giác phục vụ kiểm tra trùng lặp tức thì khi Gửi báo cáo."""
    if using_postgres():
        rows = supabase_rest.select(
            'reports',
            columns=','.join(SCREENING_COLUMNS),
            order='created_at.desc',
            limit=limit,
        )
        df = pd.DataFrame(rows, columns=SCREENING_COLUMNS) if rows else pd.DataFrame(columns=SCREENING_COLUMNS)
    else:
        init()
        cols_sql = ', '.join(SCREENING_COLUMNS)
        with connect() as conn:
            df = pd.read_sql_query(f'SELECT {cols_sql} FROM reports ORDER BY created_at DESC LIMIT ?', conn, params=(limit,))
    for c in ('latitude', 'longitude'):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df


def fetch_df(statuses=None) -> pd.DataFrame:
    if using_postgres():
        ck = (
            supabase_rest.get_url(),
            supabase_rest.table_version('reports'),
            tuple(sorted(str(s) for s in statuses)) if statuses else None,
        )
        cached = _DF_CACHE.get(ck)
        if cached is not None and (time.monotonic() - cached[0] < _DF_TTL_S):
            return cached[1].copy()
        filters = {}
        if statuses:
            joined = ','.join(str(s) for s in statuses)
            filters['status'] = f'in.({joined})'
        rows = supabase_rest.select(
            'reports',
            filters=filters,
            columns=','.join(COLUMNS),
            order='created_at.asc',
        )
        df = _normalize_df(pd.DataFrame(rows))
        if len(_DF_CACHE) > 24:
            _DF_CACHE.clear()
        _DF_CACHE[ck] = (time.monotonic(), df)
        return df.copy()

    init()
    query, params = 'SELECT * FROM reports', []
    if statuses:
        query += ' WHERE status IN (%s)' % ','.join('?' for _ in statuses)
        params = list(statuses)
    with connect() as conn:
        df = pd.read_sql_query(query + ' ORDER BY created_at', conn, params=params)
    return _normalize_df(df)


def get_report(report_id: str) -> dict | None:
    if not report_id:
        return None
    if using_postgres():
        rows = supabase_rest.select(
            'reports',
            filters={'id': f'eq.{report_id}'},
            columns=','.join(COLUMNS),
            limit=1,
        )
        if not rows:
            return None
        df = _normalize_df(pd.DataFrame(rows))
        return df.iloc[0].to_dict()
    df = fetch_df()
    hit = df[df.id == report_id]
    return None if hit.empty else hit.iloc[0].to_dict()


# ── Lưu cấu hình động (ma trận AHP, định mức chi phí...) ─────────────────

def get_setting(key: str, default: Any = None) -> Any:
    try:
        if using_postgres() and supabase_rest.table_ready('app_settings'):
            sk = (supabase_rest.get_url(), supabase_rest.table_version('app_settings'), str(key))
            cached = _SETTING_CACHE.get(sk)
            if cached is not None and (time.monotonic() - cached[0] < _SETTING_TTL_S):
                val = cached[1]
                if val is _MISSING:
                    return default
                return json.loads(json.dumps(val)) if isinstance(val, (dict, list)) else val
            rows = supabase_rest.select('app_settings', filters={'key': f'eq.{key}'}, limit=1)
            val = json.loads(rows[0]['value_json']) if rows else _MISSING
            if len(_SETTING_CACHE) > 64:
                _SETTING_CACHE.clear()
            _SETTING_CACHE[sk] = (time.monotonic(), val)
            if val is _MISSING:
                return default
            return json.loads(json.dumps(val)) if isinstance(val, (dict, list)) else val
        init()
        with connect() as conn:
            row = conn.execute('SELECT value_json FROM app_settings WHERE key=?', (key,)).fetchone()
            return json.loads(row['value_json']) if row else default
    except Exception:
        return default


def set_setting(key: str, value: Any, actor: str = '') -> None:
    payload = {
        'key': str(key),
        'value_json': json.dumps(value, ensure_ascii=False),
        'updated_at': now_vn().strftime('%Y-%m-%d %H:%M:%S'),
        'updated_by': str(actor or ''),
    }
    if using_postgres() and supabase_rest.table_ready('app_settings'):
        supabase_rest.insert('app_settings', payload, upsert=True)
        return
    init()
    with connect() as conn:
        conn.execute(
            'INSERT OR REPLACE INTO app_settings (key, value_json, updated_at, updated_by) VALUES (?,?,?,?)',
            (payload['key'], payload['value_json'], payload['updated_at'], payload['updated_by']),
        )


# ── Tương thích tạm thời khi người dùng chưa chạy 001_supabase_schema.sql ──

def _pull_legacy_db_if_needed() -> None:
    if using_postgres():
        return
    try:
        from . import storage
        if not storage.is_enabled():
            return
        data = storage.download('roadwatch.db')
        if data:
            p = db_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
    except Exception as exc:
        log.warning('Kéo DB legacy thất bại: %s', exc)


def _push_legacy_db_if_needed() -> None:
    if using_postgres():
        return
    try:
        from . import storage
        if not storage.is_enabled():
            return
        p = db_path()
        if p.is_file():
            storage.upload('roadwatch.db', p.read_bytes(), 'application/x-sqlite3')
    except Exception as exc:
        log.warning('Đẩy DB legacy thất bại: %s', exc)
