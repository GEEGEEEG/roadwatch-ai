"""Tiện ích dùng chung cho giao diện Streamlit."""
import hmac

import streamlit as st

from .config import cfg, data_dir, model_path
from .constants import DISCLAIMER


def _version():
    try:
        return tuple(int(x) for x in st.__version__.split('.')[:2])
    except Exception:
        return (1, 40)


def stretch(fn=None):
    """Streamlit >= 1.50 dùng width='stretch'; bản cũ dùng use_container_width=True."""
    return {'width': 'stretch'} if _version() >= (1, 50) else {'use_container_width': True}


def df_show(df, **kw):
    st.dataframe(df, **stretch(st.dataframe), **kw)


def img_show(img, **kw):
    st.image(img, **stretch(st.image), **kw)


def is_officer():
    return st.session_state.get('role') == 'officer'


def officer_login_box():
    pw = cfg('ROADWATCH_OFFICER_PASSWORD')
    with st.sidebar:
        if is_officer():
            st.success('Đã đăng nhập: cán bộ')
            if st.button('Đăng xuất'):
                st.session_state['role'] = 'citizen'
                st.rerun()
            return
        with st.expander('Đăng nhập cán bộ'):
            if not pw:
                st.caption('Chưa đặt ROADWATCH_OFFICER_PASSWORD nên chức năng cán bộ đang khóa.')
                return
            entered = st.text_input('Mật khẩu', type='password', key='officer_pw')
            if st.button('Đăng nhập'):
                if hmac.compare_digest(entered.encode(), pw.encode()):
                    st.session_state['role'] = 'officer'
                    st.rerun()
                else:
                    st.error('Sai mật khẩu.')


def require_officer():
    if not is_officer():
        st.warning('Trang này chỉ dành cho cán bộ. Đăng nhập ở thanh bên.')
        st.stop()


def disclaimer():
    st.caption(DISCLAIMER)


@st.cache_resource(show_spinner='Đang tải trọng số YOLO...')
def get_detector():
    from .detector import RoadDamageDetector
    return RoadDamageDetector(model_path())


def detector_or_stop():
    if not model_path().is_file():
        st.error(f'Thiếu mô hình tại {model_path()}. Tải checkpoint 4 lớp D00/D10/D20/D40 và đặt đúng vị trí.')
        st.stop()
    try:
        return get_detector()
    except Exception as exc:
        st.error(f'Không mở được checkpoint: {exc}')
        st.stop()


def image_file(rel):
    p = data_dir() / rel if rel else None
    if p and not p.is_file():
        # Thử khôi phục từ Drive nếu file bị mất (sau khi app ngủ/restart)
        try:
            from . import gdrive
            if gdrive.is_enabled():
                data = gdrive.download(rel)
                if data:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(data)
        except Exception:
            pass
    return str(p) if p and p.is_file() else None


def weights_sidebar():
    """Thanh trượt trọng số (nhớ giá trị khi chuyển trang). Trả về ((a, b, c), radius_m)."""
    ss = st.session_state
    a = st.sidebar.slider('Trọng số mức độ (%)', 0, 100, ss.get('_wa', 50), 5)
    b = st.sidebar.slider('Trọng số số báo cáo (%)', 0, 100, ss.get('_wb', 30), 5)
    c = st.sidebar.slider('Trọng số cấp tuyến (%)', 0, 100, ss.get('_wc', 20), 5)
    r = st.sidebar.slider('Bán kính gom điểm nóng (m)', 10, 200, ss.get('_wr', 40), 5)
    ss['_wa'], ss['_wb'], ss['_wc'], ss['_wr'] = a, b, c, r
    st.sidebar.caption('Nếu tổng ≠ 100% hệ thống tự chuẩn hóa.')
    return (a, b, c), float(r)


def qr_png(text):
    import io
    import qrcode
    buf = io.BytesIO()
    qrcode.make(text).save(buf, format='PNG')
    return buf.getvalue()
