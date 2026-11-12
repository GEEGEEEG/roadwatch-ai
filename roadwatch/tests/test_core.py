import io
import json

import numpy as np
import pandas as pd
import pytest
from PIL import Image

from conftest import FakeDetector, make_jpeg
from core import db, geo, priority, quality, service, video
from core.detector import decode_model_label, severity_rule, union_area_pct, extract_exif_gps
from core.evaluation import metrics_at, metrics_table
from core.report import build_pdf, hotspot_record, template_markdown
from core.backup import make_backup, restore_backup


# ---------- detector (phần thuần) ----------
def test_decode_labels():
    assert decode_model_label('D00') == 'D00'
    assert decode_model_label('road_D40_pothole') == 'D40'
    assert decode_model_label('Alligator crack') == 'D20'
    assert decode_model_label('crack') is None


def test_union_area_no_double_count():
    boxes = [[0, 0, 100, 100], [0, 0, 100, 100]]          # trùng hoàn toàn
    assert union_area_pct(boxes, 200, 200) == pytest.approx(25.0, abs=1.0)
    assert union_area_pct([], 200, 200) == 0.0


def test_severity_rule_levels():
    none = severity_rule([])
    assert none['level'] == 'Không phát hiện' and none['score'] == 0
    pothole = [{'class_code': 'D40', 'confidence': .9, 'bbox_xyxy': [0, 0, 300, 300], 'bbox_area_percent': 30}]
    assert severity_rule(pothole, 600, 600)['level'] == 'Cần kiểm tra sớm'
    longi = [{'class_code': 'D00', 'confidence': .9, 'bbox_xyxy': [0, 0, 10, 10], 'bbox_area_percent': .1}]
    assert severity_rule(longi, 600, 600)['level'] == 'Nhẹ'


def test_exif_missing():
    assert extract_exif_gps(Image.new('RGB', (10, 10)))['has_gps'] is False


# ---------- geo ----------
def test_haversine_and_cluster():
    d = float(geo.haversine_m(10.0, 106.0, 10.0, 106.001))
    assert 100 < d < 120
    labels = geo.cluster_points([10.0, 10.00001, 10.01], [106.0, 106.00001, 106.0], 40)
    assert labels[0] == labels[1] != labels[2]


def test_cluster_no_chaining():
    lons = [106.0 + i * 0.0004 for i in range(10)]        # ~44 m mỗi điểm dọc một tuyến
    labels = geo.cluster_points([10.0] * 10, lons, 40)
    assert len(set(labels)) == 10


def test_route_and_links():
    pts = [(1, 10.0, 106.0), (2, 10.0, 106.1), (3, 10.0, 106.01)]
    r = geo.nearest_neighbor_route(pts, start=(10.0, 106.0))
    assert [x[0] for x in r] == [1, 3, 2]
    assert 'destination=10.0,106.1' in geo.maps_multi_link([(10.0, 106.0), (10.0, 106.1)])
    assert 'waypoints=10.0,106.0' in geo.maps_multi_link([(10.0, 106.0), (10.0, 106.1)])


# ---------- priority ----------
def _row(i, lat, lon, score, status='verified', road=50, d40=1, t=None):
    return {'id': f'r{i}', 'created_at': t or f'2026-11-0{i} 10:00:00', 'location_name': f'P{i}', 'latitude': lat,
            'longitude': lon, 'status': status, 'final_score': score, 'road_score': road, 'count_D40': d40,
            'road_type': 'x'}


def test_final_score_shift():
    assert priority.final_score('Nhẹ', 30, 'Nhẹ') == 30
    assert priority.final_score('Trung bình', 55, 'Cần kiểm tra sớm') == 85
    assert priority.final_score('Nhẹ', 30, 'Không phát hiện') == 0


def test_hotspots_ranking_and_weights():
    df = pd.DataFrame([_row(1, 10.0, 106.0, 90, road=30), _row(2, 10.0, 106.00001, 40, road=30),
                       _row(3, 10.1, 106.0, 60, road=90), _row(4, 10.2, 106.0, 99, status='pending'),
                       _row(5, 10.3, 106.0, 99, status='fixed')])
    hs = priority.build_hotspots(df, (50, 30, 20), 40)
    assert len(hs) == 2                                       # pending/fixed bị loại
    assert hs.iloc[0].report_count in (1, 2)
    first = hs.iloc[0].location_name
    hs2 = priority.build_hotspots(df, (0, 0, 100), 40)
    assert hs2.iloc[0].location_name == 'P3' and first != hs2.iloc[0].location_name
    assert priority.normalize_weights((0, 0, 0)) == priority.DEFAULT_WEIGHTS


def test_trend_and_compare():
    df = pd.DataFrame([_row(1, 10.0, 106.0, 30), _row(2, 10.0, 106.00001, 90), _row(3, 10.1, 106.0, 50, road=90)])
    hs_t = priority.build_hotspots(df, use_trend=True)
    assert (hs_t.trend_bonus > 0).any()
    assert (priority.build_hotspots(df, use_trend=False).trend_bonus == 0).all()
    cmp, rho = priority.compare_rankings(df, (50, 30, 20), (0, 0, 100))
    assert not cmp.empty and -1 <= rho <= 1
    assert priority.build_hotspots(pd.DataFrame()).empty


# ---------- quality / screening ----------
def test_quality_flags():
    dark = quality.assess_quality(Image.new('RGB', (640, 480), (5, 5, 5)))
    assert 'Ảnh quá tối' in dark['flags']
    small = quality.assess_quality(Image.new('RGB', (100, 100), (128, 128, 128)))
    assert 'Ảnh độ phân giải thấp' in small['flags']
    sharp = quality.assess_quality(Image.open(io.BytesIO(make_jpeg(1))))
    assert 'Ảnh có thể bị mờ/rung' not in sharp['flags']
    flat = quality.assess_quality(Image.new('RGB', (640, 480), (128, 128, 128)))
    assert 'Ảnh có thể bị mờ/rung' in flat['flags']


def test_screening_burst():
    now = pd.Timestamp.now()
    ex = pd.DataFrame([{'latitude': 10.0, 'longitude': 106.0, 'created_at': now.strftime('%Y-%m-%d %H:%M:%S')}])
    assert quality.screening_flags(ex, 10.00001, 106.0, now, 1, [])
    assert not quality.screening_flags(ex, 10.1, 106.0, now, 1, [])
    assert quality.screening_flags(None, 10, 106, now, 0, ['Ảnh quá tối'])


# ---------- db + service ----------
def _submit(raw=None, **kw):
    args = dict(location_name='Đường A', lat=10.77, lon=106.69, gps_source='Nhập tay', source='citizen', consent=True)
    args.update(kw)
    return service.submit_report(FakeDetector(), raw or make_jpeg(1), 'a.jpg', **args)


def test_submit_flow_and_duplicate():
    rid, out, q, flags = _submit()
    row = db.get_report(rid)
    assert row['status'] == 'pending' and row['count_D40'] == 1 and row['final_level'] == row['ai_level']
    assert json.loads(row['detections_json'])[0]['class_code'] == 'D40'
    with pytest.raises(db.DuplicateImage):
        _submit()


def test_submit_validation():
    with pytest.raises(service.SubmitError):
        _submit(consent=False)
    with pytest.raises(service.SubmitError):
        _submit(raw=make_jpeg(2), lat='abc')
    with pytest.raises(service.SubmitError):
        _submit(raw=make_jpeg(3), lat=100)
    with pytest.raises(service.SubmitError):
        _submit(raw=make_jpeg(4), location_name='  ')
    with pytest.raises(service.SubmitError):
        service.submit_report(FakeDetector(), b'not an image', 'x.jpg', location_name='A', lat=1, lon=1,
                              gps_source='Nhập tay', consent=True)


def test_officer_override_and_history():
    rid, *_ = _submit(raw=make_jpeg(5), source='officer', status='verified', final_level='Trung bình', actor='cb')
    r = db.get_report(rid)
    assert r['status'] == 'verified' and r['final_level'] == 'Trung bình' and r['reviewed_by'] == 'cb'
    db.update_report(rid, status='assigned')
    db.add_history(rid, 'assigned', 'cb', 'x')
    assert len(db.get_history(rid)) == 2


# ---------- report / backup ----------
def test_report_and_pdf():
    rid, *_ = _submit(raw=make_jpeg(6), source='officer', status='verified')
    df = db.fetch_df()
    hs = priority.build_hotspots(df)
    rec = hotspot_record(hs.iloc[0], df)
    md = template_markdown(rec)
    assert 'D40' in md and rid in md
    pdf = build_pdf(rec, str(db.get_report(rid) and (service.data_dir() / db.get_report(rid)['annotated_file'])))
    assert pdf[:4] == b'%PDF' and len(pdf) > 3000


def test_backup_roundtrip():
    rid, *_ = _submit(raw=make_jpeg(7))
    blob = make_backup()
    for p in (service.data_dir()).rglob('roadwatch.db'):
        p.unlink()
    restore_backup(blob)
    assert db.get_report(rid) is not None


def test_backup_rejects_traversal():
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('../evil.txt', 'x')
    with pytest.raises(ValueError):
        restore_backup(buf.getvalue())


# ---------- video / evaluation ----------
GPX = b'''<gpx xmlns="http://www.topografix.com/GPX/1/1"><trk><trkseg>
<trkpt lat="10.0" lon="106.0"><time>2026-11-02T01:00:00Z</time></trkpt>
<trkpt lat="10.0" lon="106.002"><time>2026-11-02T01:00:20Z</time></trkpt></trkseg></trk></gpx>'''


def test_gpx_interpolation():
    tr = video.parse_gpx(GPX)
    assert len(tr) == 2
    mid = video.interpolate(tr, tr[0][0] + 10)
    assert mid[0] == pytest.approx(10.0) and mid[1] == pytest.approx(106.001)
    assert video.interpolate(tr, tr[0][0] - 1) is None and video.interpolate(tr, tr[-1][0] + 1) is None


def test_metrics():
    df = pd.DataFrame({'gt': ['Có', 'Có', 'Không', 'Không', ''], 'detections': [[('D40', .9)], [('D00', .2)], [('D00', .3)], [], [('D10', .9)]]})
    m = metrics_at(df, 'gt', 0.25)
    assert (m['TP'], m['FP'], m['FN'], m['TN']) == (1, 1, 1, 1) and m['n_labeled'] == 4
    assert m['precision'] == 0.5 and m['recall'] == 0.5 and m['false_alarm_rate'] == 0.5
    assert len(metrics_table(df, 'gt')) == 3


# ---------- damage_analysis & visual_dedup ----------
def test_damage_analysis():
    from core.damage_analysis import analyze_image_damage
    im = Image.new('RGB', (100, 100), color=(180, 180, 180))
    # Tạo một đốm đen giả lập ổ gà
    for x in range(30, 70):
        for y in range(30, 70):
            im.putpixel((x, y), (20, 20, 20))
    dets = [{'class_code': 'D40', 'confidence': 0.95, 'bbox_xyxy': [25, 25, 75, 75]}]
    res = analyze_image_damage(im, dets)
    assert res['total_damage_m2'] > 0
    assert res['estimated_volume_liters'] > 0
    assert len(res['detailed_boxes']) == 1


def test_visual_dedup():
    from core.visual_dedup import image_fingerprint, visual_similarity
    im1 = Image.new('RGB', (64, 64), color=(100, 100, 100))
    im2 = im1.copy()
    im3 = Image.new('RGB', (64, 64), color=(255, 255, 255))
    fp1 = image_fingerprint(im1)
    fp2 = image_fingerprint(im2)
    fp3 = image_fingerprint(im3)
    assert visual_similarity(fp1, fp2) >= 0.99
    assert visual_similarity(fp1, fp3) < 0.90


# ---------- AHP & cost_estimation & corridor_hotspot ----------
def test_ahp_calculation():
    from core.ahp import compute_ahp_weights, compute_ahp_priority
    res = compute_ahp_weights()
    assert len(res['weights']) == 4
    assert np.isclose(np.sum(res['weights']), 1.0)
    assert res['is_consistent'] is True   # CR < 0.10
    score, _ = compute_ahp_priority(80, 70, 50, 20)
    assert 0 <= score <= 100


def test_cost_estimation():
    from core.cost_estimation import estimate_maintenance_cost
    est = estimate_maintenance_cost(area_m2=0.2, volume_l=5.0)
    assert est['total_estimate_vnd'] > 0
    assert 'bao' in est['material_detail']


def test_corridor_clustering():
    from core.corridor_hotspot import analyze_corridor_clusters
    df = pd.DataFrame([
        {'id': '1', 'status': 'verified', 'latitude': 10.000, 'longitude': 106.000, 'location_name': 'Đường A'},
        {'id': '2', 'status': 'verified', 'latitude': 10.001, 'longitude': 106.000, 'location_name': 'Đường A'},
        {'id': '3', 'status': 'verified', 'latitude': 10.002, 'longitude': 106.000, 'location_name': 'Đường A'},
    ])
    clusters = analyze_corridor_clusters(df, max_distance_m=200, min_cluster_size=3)
    assert len(clusters) == 1
    assert clusters[0]['is_wide_degradation'] is True
    assert clusters[0]['cluster_size'] == 3
