import sqlite3

import pandas as pd

from core import db
from core.constants import ACTIVE_STATUSES
from core.geo import haversine_m, nearby_points
from core.priority import build_hotspots


def _ins(rid, lat, lon, status='verified', **kw):
    row = dict(id=rid, image_hash=rid, location_name='Nguyễn Văn Linh', latitude=lat, longitude=lon, status=status,
               final_score=70.0, ai_score=70.0, road_score=75.0, count_D40=1, ai_level='Cần kiểm tra sớm',
               final_level='Cần kiểm tra sớm', source='citizen', consent=1)
    row.update(kw)
    db.insert_report(row)


def test_nearby_points_distance_and_order():
    _ins('RW-A', 16.0600, 108.2200)
    _ins('RW-B', 16.0601, 108.2200)   # ~11 m
    _ins('RW-C', 16.0610, 108.2200)   # ~111 m, ngoài bán kính
    df = db.fetch_df()
    hits = nearby_points(df, 16.06003, 108.2200, 50, ACTIVE_STATUSES)
    assert [h[0] for h in hits] == ['RW-A', 'RW-B']
    assert abs(hits[0][1] - float(haversine_m(16.06003, 108.22, 16.06, 108.22))) < 0.01
    assert nearby_points(df, 16.0, 108.0, 50) == [] and nearby_points(None, 1, 1, 50) == []


def test_pending_not_matched_as_gốc():
    _ins('RW-P', 16.06, 108.22, status='pending')
    assert nearby_points(db.fetch_df(), 16.06, 108.22, 30, ACTIVE_STATUSES) == []


def test_merge_adds_to_parent_frequency_without_new_hotspot():
    _ins('RW-1', 16.0600, 108.2200)
    base = build_hotspots(db.fetch_df())
    assert len(base) == 1 and base.report_count[0] == 1
    _ins('RW-2', 16.06005, 108.2200, status='pending')
    _ins('RW-3', 16.06006, 108.2200, status='pending')
    for rid in ('RW-2', 'RW-3'):
        db.update_report(rid, status='merged', merged_into='RW-1')
    after = build_hotspots(db.fetch_df())
    assert len(after) == 1                       # không sinh điểm nóng mới
    assert after.report_count[0] == 3 and after.merged_count[0] == 2
    assert after.frequency_component[0] == 30.0  # 3 lượt x 10
    assert 'gồm 2 phản ánh đã gộp' in after.ranking_reason[0]
    assert after.priority_score[0] > base.priority_score[0]


def test_merged_excluded_from_map_statuses_and_orphans_ignored():
    _ins('RW-1', 16.06, 108.22)
    _ins('RW-X', 16.07, 108.23, status='merged', merged_into='RW-không-tồn-tại')
    hs = build_hotspots(db.fetch_df())
    assert len(hs) == 1 and hs.merged_count[0] == 0


def test_old_database_gets_merged_into_column(tmp_data):
    with db.connect() as conn:
        conn.execute('DROP TABLE reports')
        conn.execute('CREATE TABLE reports (id TEXT PRIMARY KEY, created_at TEXT, status TEXT)')
    db.init()
    with db.connect() as conn:
        cols = {r[1] for r in conn.execute('PRAGMA table_info(reports)')}
    assert 'merged_into' in cols
    assert isinstance(db.fetch_df(), pd.DataFrame)
