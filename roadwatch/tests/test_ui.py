from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from conftest import FakeDetector, make_jpeg
from core import db, service


ROOT = Path(__file__).resolve().parent.parent


def seed():
    ids = []
    for i, (lat, lon, lvl) in enumerate([(10.7769, 106.7009, None), (10.7769, 106.70091, 'Cần kiểm tra sớm'), (10.80, 106.72, 'Nhẹ')]):
        rid, *_ = service.submit_report(FakeDetector(), make_jpeg(i + 20), f'{i}.jpg', location_name=f'Điểm {i}', lat=lat, lon=lon,
                                        gps_source='Nhập tay', source='officer', consent=True, status='verified', final_level=lvl, actor='cb')
        ids.append(rid)
    service.submit_report(FakeDetector(), make_jpeg(40), 'p.jpg', location_name='Chờ duyệt', lat=10.9, lon=106.8,
                          gps_source='Nhập tay', consent=True)
    return ids


def page(name, officer=True):
    at = AppTest.from_file(str(ROOT / 'views' / f'{name}.py'), default_timeout=30)
    if officer:
        at.session_state['role'] = 'officer'
    return at


def no_exception(at):
    assert not at.exception, [e.value for e in at.exception]


def test_app_shell_runs():
    at = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()
    no_exception(at)


@pytest.mark.parametrize('name', ['queue', 'priority', 'route', 'detail', 'reports', 'admin', 'compare', 'video', 'evaluation'])
def test_officer_pages_blocked_for_citizen(name):
    at = page(name, officer=False).run()
    no_exception(at)
    assert any('chỉ dành cho cán bộ' in w.value for w in at.warning)


def test_empty_state_pages():
    for name in ('home', 'map', 'priority', 'route', 'queue', 'detail', 'reports'):
        at = page(name).run()
        no_exception(at)


@pytest.mark.parametrize('name', ['home', 'map', 'priority', 'route', 'detail', 'reports', 'admin', 'queue'])
def test_pages_with_data(name):
    seed()
    at = page(name).run()
    no_exception(at)


def test_queue_approve_and_reject():
    seed()
    at = page('queue').run()
    assert any('Chờ duyệt' in o for o in at.selectbox[0].options)
    # từ chối thiếu lý do -> báo lỗi
    [b for b in at.button if 'Từ chối' in b.label][0].click()
    at.run()
    assert any('lý do' in e.value for e in at.error)
    # duyệt thiếu xác nhận -> báo lỗi
    [b for b in at.button if 'Duyệt' in b.label][0].click()
    at.run()
    assert any('xem lại ảnh' in e.value for e in at.error)
    # duyệt đủ điều kiện
    at.checkbox[0].check()
    [b for b in at.button if 'Duyệt' in b.label][0].click()
    at.run()
    no_exception(at)
    assert db.fetch_df(['pending']).empty
    assert len(db.fetch_df(['verified'])) == 4


def test_route_assign():
    seed()
    at = page('route').run()
    no_exception(at)
    assert len(at.get('link_button')) >= 1


@pytest.mark.parametrize('name', ['submit', 'compare', 'video', 'evaluation'])
def test_detector_pages_render(name, monkeypatch):
    import core.ui as ui
    monkeypatch.setattr(ui, 'detector_or_stop', lambda: FakeDetector())
    seed()
    at = page(name).run()
    no_exception(at)


def test_detector_pages_stop_without_model():
    at = page('submit', officer=False).run()
    no_exception(at)
    assert any('Thiếu mô hình' in e.value for e in at.error)
