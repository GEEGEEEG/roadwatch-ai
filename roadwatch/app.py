import streamlit as st

from core import db, theme, ui

st.set_page_config(page_title='RoadWatch AI | Phát hiện và giám sát hư hỏng mặt đường', page_icon='🛣️', layout='wide', initial_sidebar_state='auto', menu_items={'About': 'RoadWatch AI · Ứng dụng minh họa hỗ trợ phát hiện, giám sát và ưu tiên kiểm tra hư hỏng mặt đường. Kết quả AI cần cán bộ xác minh.'})
db.init()
theme.apply()
st.session_state.setdefault('role', 'citizen')
ui.officer_login_box()

public_pages = [
    st.Page('views/home.py', title='Trang chủ', icon='🏠', url_path='home', default=True),
    st.Page('views/submit.py', title='Gửi báo cáo', icon='📷', url_path='submit'),
    st.Page('views/map.py', title='Bản đồ', icon='🗺️', url_path='map'),
]

if not ui.is_officer():
    public_pages.append(st.Page('views/login.py', title='Cổng cán bộ', icon='🔐', url_path='login'))
    pages = {'Công khai': public_pages}
else:
    officer_pages = [
        st.Page('views/queue.py', title='Hàng chờ xác minh', icon='✅', url_path='queue'),
        st.Page('views/priority.py', title='Ưu tiên kiểm tra', icon='📊', url_path='priority'),
        st.Page('views/route.py', title='Lộ trình & giao việc', icon='🚗', url_path='route'),
        st.Page('views/detail.py', title='Chi tiết điểm', icon='🔎', url_path='detail'),
        st.Page('views/compare.py', title='Trước/sau sửa chữa', icon='🛠️', url_path='compare'),
        st.Page('views/reports.py', title='Báo cáo', icon='📄', url_path='reports'),
        st.Page('views/video.py', title='Khảo sát video + GPX', icon='🎥', url_path='video'),
        st.Page('views/evaluation.py', title='Đánh giá mô hình', icon='🧪', url_path='evaluation'),
        st.Page('views/admin.py', title='Quản trị & sao lưu', icon='⚙️', url_path='admin'),
        st.Page('views/login.py', title='Hồ sơ cán bộ', icon='👤', url_path='officer-profile'),
    ]
    pages = {
        'Công khai': public_pages,
        'Cán bộ': officer_pages,
    }

st.navigation(pages).run()
