from pathlib import Path

import streamlit as st

from core import db, theme, ui

BASE_DIR = Path(__file__).resolve().parent


def _page(rel: str) -> Path:
    return (BASE_DIR / rel).resolve()


st.set_page_config(
    page_title='RoadWatch AI | Giám sát và quản lý hư hỏng mặt đường đô thị',
    page_icon='🛣️',
    layout='wide',
    initial_sidebar_state='auto',
    menu_items={
        'About': (
            'RoadWatch AI v5.0 · Hệ thống phát hiện, thẩm định và xếp hạng ưu tiên duy tu mặt đường '
            '(YOLOv8 + AHP + PostGIS/Supabase). Kết quả AI luôn được cán bộ xác minh.'
        )
    },
)

# Endpoint siêu nhẹ giữ kết nối Streamlit Cloud & Supabase luôn ấm (Keep-alive Healthcheck)
if st.query_params.get('healthz') == '1':
    db.init()
    st.write('ok')
    st.stop()

db.init()
st.session_state.setdefault('role', 'citizen')
_logo_path = _page('assets/logo_roadwatch.png')
if _logo_path.is_file():
    st.logo(str(_logo_path), size='large', icon_image=str(_logo_path))
ui.officer_login_box()

p_home = st.Page(_page('views/home.py'), title='Trang chủ', default=True)
p_submit = st.Page(_page('views/submit.py'), title='Gửi báo cáo', url_path='submit')
p_track = st.Page(_page('views/track.py'), title='Tra cứu phản ánh', url_path='track')
p_map = st.Page(_page('views/map.py'), title='Bản đồ', url_path='map')
public_pages = [p_home, p_submit, p_track, p_map]

if not ui.is_officer():
    public_pages.append(st.Page(_page('views/login.py'), title='Cổng cán bộ', url_path='login'))
    pages = {'Công khai': public_pages}
    p_dock_4, dock_4_lbl = p_map, 'Bản đồ'
else:
    role_lv = ui.officer_role()
    if role_lv == 'field_team':
        p_route = st.Page(_page('views/route.py'), title='Lộ trình & giao việc', url_path='route')
        officer_pages = [
            p_route,
            st.Page(_page('views/compare.py'), title='Trước/sau sửa chữa', url_path='compare'),
            st.Page(_page('views/video.py'), title='Khảo sát video + GPX', url_path='video'),
            st.Page(_page('views/detail.py'), title='Chi tiết điểm', url_path='detail'),
            st.Page(_page('views/login.py'), title='Hồ sơ cán bộ', url_path='officer-profile'),
        ]
        p_dock_4, dock_4_lbl = p_route, 'Lộ trình'
    else:
        p_queue = st.Page(_page('views/queue.py'), title='Hàng chờ xác minh', url_path='queue')
        officer_pages = [
            p_queue,
            st.Page(_page('views/priority.py'), title='Ưu tiên kiểm tra', url_path='priority'),
            st.Page(_page('views/route.py'), title='Lộ trình & giao việc', url_path='route'),
            st.Page(_page('views/detail.py'), title='Chi tiết điểm', url_path='detail'),
            st.Page(_page('views/compare.py'), title='Trước/sau sửa chữa', url_path='compare'),
            st.Page(_page('views/reports.py'), title='Báo cáo', url_path='reports'),
            st.Page(_page('views/video.py'), title='Khảo sát video + GPX', url_path='video'),
            st.Page(_page('views/admin.py'), title='Quản trị & sao lưu', url_path='admin'),
            st.Page(_page('views/login.py'), title='Hồ sơ cán bộ', url_path='officer-profile'),
        ]
        p_dock_4, dock_4_lbl = p_queue, 'Duyệt'
    pages = {
        'Công khai': public_pages,
        'Cán bộ': officer_pages,
    }

pg = st.navigation(pages)
_post_target = st.session_state.pop('_post_login_target', None)
if _post_target and ui.is_officer():
    _target_page = p_route if ui.officer_role() == 'field_team' else p_queue
    if getattr(pg, 'url_path', '') != getattr(_target_page, 'url_path', ''):
        st.switch_page(_target_page)
theme.apply(getattr(pg, 'url_path', 'home') or 'home')

# Thanh điều hướng Mobile App Bottom Dock (chỉ hiện trên màn hình điện thoại <= 768px)
with st.container(key='rw_mobile_dock'):
    d_cols = st.columns(4, gap='small')
    with d_cols[0]:
        ui.safe_page_link(p_home, label='Trang chủ', icon=None)
    with d_cols[1]:
        ui.safe_page_link(p_submit, label='Gửi ảnh', icon=None)
    with d_cols[2]:
        ui.safe_page_link(p_track, label='Tra cứu', icon=None)
    with d_cols[3]:
        ui.safe_page_link(p_dock_4, label=dock_4_lbl, icon=None)

pg.run()
