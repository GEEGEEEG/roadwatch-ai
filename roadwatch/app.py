import streamlit as st

from core import db, theme, ui

st.set_page_config(page_title='RoadWatch AI', page_icon='🛣️', layout='wide')
db.init()
theme.apply()
st.session_state.setdefault('role', 'citizen')
ui.officer_login_box()

pages = {
    'Công khai': [
        st.Page('views/home.py', title='Trang chủ', icon='🏠', url_path='home', default=True),
        st.Page('views/submit.py', title='Gửi báo cáo', icon='📷', url_path='submit'),
        st.Page('views/map.py', title='Bản đồ', icon='🗺️', url_path='map'),
    ],
    'Cán bộ': [
        st.Page('views/queue.py', title='Hàng chờ xác minh', icon='✅', url_path='queue'),
        st.Page('views/priority.py', title='Ưu tiên kiểm tra', icon='📊', url_path='priority'),
        st.Page('views/route.py', title='Lộ trình & giao việc', icon='🚗', url_path='route'),
        st.Page('views/detail.py', title='Chi tiết điểm', icon='🔎', url_path='detail'),
        st.Page('views/compare.py', title='Trước/sau sửa chữa', icon='🛠️', url_path='compare'),
        st.Page('views/reports.py', title='Báo cáo', icon='📄', url_path='reports'),
        st.Page('views/video.py', title='Khảo sát video + GPX', icon='🎥', url_path='video'),
        st.Page('views/evaluation.py', title='Đánh giá mô hình', icon='🧪', url_path='evaluation'),
        st.Page('views/admin.py', title='Quản trị & sao lưu', icon='⚙️', url_path='admin'),
    ],
}
if not ui.is_officer():
    pages.pop('Cán bộ')
st.navigation(pages).run()
