"""Tiện ích dùng chung cho giao diện Streamlit."""
import hmac
from html import escape
from datetime import datetime

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
    """Nhãn thương hiệu cố định + chuyển vào cổng quản trị; không gây rối sidebar."""
    with st.sidebar:
        st.markdown('''<div class="rw-sidebar-brand">
          <div class="rw-logo"><span class="rw-logo-mark">RW</span> RoadWatch AI</div>
          <p class="rw-sidebar-sub">Giám sát & quản lý mặt đường</p>
        </div>''',unsafe_allow_html=True)
        if is_officer():
            officer = escape(str(st.session_state.get('officer_name','Cán bộ trực ca')))
            st.markdown(f'<div class="rw-sidebar-info">🟢 Đang đăng nhập: <b>{officer}</b></div>',unsafe_allow_html=True)
            if st.button('Đăng xuất',key='btn_officer_logout',use_container_width=True):
                for key in ('officer_name','officer_unit','officer_login_time'):
                    st.session_state.pop(key,None)
                st.session_state['role']='citizen'
                st.rerun()
        else:
            st.markdown('<div class="rw-sidebar-info">🔒 Thông tin quản trị chỉ dành cho người được cấp quyền.</div>',unsafe_allow_html=True)


def require_officer():
    if not is_officer():
        st.warning('Trang này chỉ dành cho cán bộ. Đăng nhập ở thanh bên hoặc mở Cổng cán bộ.')
        try:
            st.page_link('views/login.py', label='Mở Cổng Đăng Nhập Cán Bộ', icon='🔐')
        except Exception:
            pass
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


def page_intro(kicker,title,description):
    """Tiêu đề trang đồng nhất, tách bạch nhiệm vụ và nội dung phụ."""
    st.markdown('<div class="rw-page-intro"><span class="rw-overline">'+escape(kicker)+'</span><h1>'+escape(title)+'</h1><p>'+escape(description)+'</p></div>',unsafe_allow_html=True)


def steps(*items,active=0):
    pills=''.join('<span'+(' class="active"' if i==active else '')+'>'+escape(str(i+1))+'. '+escape(v)+'</span>' for i,v in enumerate(items))
    st.markdown('<div class="rw-progress">'+pills+'</div>',unsafe_allow_html=True)


def safe_csv_export(df):
    """Ngăn công thức spreadsheet ngoài ý muốn từ chuỗi do người dùng nhập."""
    clone=df.copy()
    for col in clone.select_dtypes(include=['object','string']).columns:
        clone[col]=clone[col].map(lambda v: "'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@','\t','\r')) else v)
    return clone.to_csv(index=False).encode('utf-8-sig')
