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
theme.apply()
st.session_state.setdefault('role', 'citizen')
ui.officer_login_box()

public_pages = [
    st.Page(_page('views/home.py'), title='Trang chủ', icon='🏠', url_path='home', default=True),
    st.Page(_page('views/submit.py'), title='Gửi báo cáo', icon='📷', url_path='submit'),
    st.Page(_page('views/track.py'), title='Tra cứu phản ánh', icon='🔍', url_path='track'),
    st.Page(_page('views/map.py'), title='Bản đồ', icon='🗺️', url_path='map'),
]

if not ui.is_officer():
    public_pages.append(st.Page(_page('views/login.py'), title='Cổng cán bộ', icon='🔐', url_path='login'))
    pages = {'Công khai': public_pages}
else:
    role_lv = ui.officer_role()
    if role_lv == 'field_team':
        officer_pages = [
            st.Page(_page('views/route.py'), title='Lộ trình & giao việc', icon='🚗', url_path='route'),
            st.Page(_page('views/compare.py'), title='Trước/sau sửa chữa', icon='🛠️', url_path='compare'),
            st.Page(_page('views/video.py'), title='Khảo sát video + GPX', icon='🎥', url_path='video'),
            st.Page(_page('views/detail.py'), title='Chi tiết điểm', icon='🔎', url_path='detail'),
            st.Page(_page('views/login.py'), title='Hồ sơ cán bộ', icon='👤', url_path='officer-profile'),
        ]
    else:
        officer_pages = [
            st.Page(_page('views/queue.py'), title='Hàng chờ xác minh', icon='✅', url_path='queue'),
            st.Page(_page('views/priority.py'), title='Ưu tiên kiểm tra', icon='📊', url_path='priority'),
            st.Page(_page('views/route.py'), title='Lộ trình & giao việc', icon='🚗', url_path='route'),
            st.Page(_page('views/detail.py'), title='Chi tiết điểm', icon='🔎', url_path='detail'),
            st.Page(_page('views/compare.py'), title='Trước/sau sửa chữa', icon='🛠️', url_path='compare'),
            st.Page(_page('views/reports.py'), title='Báo cáo', icon='📄', url_path='reports'),
            st.Page(_page('views/video.py'), title='Khảo sát video + GPX', icon='🎥', url_path='video'),
            st.Page(_page('views/evaluation.py'), title='Đánh giá mô hình', icon='🧪', url_path='evaluation'),
            st.Page(_page('views/admin.py'), title='Quản trị & sao lưu', icon='⚙️', url_path='admin'),
            st.Page(_page('views/login.py'), title='Hồ sơ cán bộ', icon='👤', url_path='officer-profile'),
        ]
    pages = {
        'Công khai': public_pages,
        'Cán bộ': officer_pages,
    }

st.navigation(pages).run()
