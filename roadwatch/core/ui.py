"""Tiện ích dùng chung cho giao diện Streamlit."""
import hmac
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
    pw = cfg('ROADWATCH_OFFICER_PASSWORD')
    with st.sidebar:
        if is_officer():
            name = st.session_state.get('officer_name', 'Cán bộ kỹ thuật')
            unit = st.session_state.get('officer_unit', 'Ban Quản lý Hạ tầng Giao thông')

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
                        border: 1px solid #334155; border-radius: 12px; padding: 14px; margin-bottom: 12px; color: #fff;">
              <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <div style="font-size: 22px; background: rgba(37,99,235,0.25); border: 1px solid #3B82F6; border-radius: 50%; width: 38px; height: 38px; display: flex; align-items: center; justify-content: center;">🛡️</div>
                <div style="line-height: 1.3;">
                  <div style="font-weight: 700; font-size: 13px; color: #F8FAFC;">{name}</div>
                  <div style="font-size: 11px; color: #94A3B8;">{unit}</div>
                </div>
              </div>
              <div style="display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #334155; padding-top: 8px; margin-top: 4px;">
                <span style="font-size: 11px; color: #10B981; font-weight: 600;">🟢 Trực tuyến</span>
                <span style="font-size: 10px; background: #2563EB; color: #fff; padding: 2px 8px; border-radius: 4px; font-weight: 600;">CÁN BỘ</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button('🚪 Đăng xuất cán bộ', key='btn_officer_logout', **stretch(st.button)):
                st.session_state['role'] = 'citizen'
                st.session_state.pop('officer_name', None)
                st.session_state.pop('officer_unit', None)
                st.session_state.pop('officer_login_time', None)
                st.rerun()
            return

        # Khi chưa đăng nhập
        st.markdown("""
        <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 10px; padding: 12px 14px; margin-bottom: 10px;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            <span style="font-size: 16px;">🏛️</span>
            <strong style="font-size: 13px; color: #0F172A;">Cổng Cán Bộ Quản Lý</strong>
          </div>
          <p style="font-size: 11px; color: #64748B; margin: 0; line-height: 1.4;">
            Dành cho cán bộ kỹ thuật kiểm tra và điều phối khắc phục mặt đường.
          </p>
        </div>
        """, unsafe_allow_html=True)

        try:
            st.page_link('views/login.py', label='Cổng Đăng Nhập Cán Bộ', icon='🔐')
        except Exception:
            pass

        with st.expander('Đăng nhập nhanh'):
            if not pw:
                st.caption('Chưa đặt ROADWATCH_OFFICER_PASSWORD nên chức năng cán bộ đang khóa.')
                return
            entered = st.text_input('Mật khẩu', type='password', key='officer_pw')
            if st.button('Đăng nhập', key='quick_login_btn', **stretch(st.button)):
                if hmac.compare_digest(entered.encode(), pw.encode()):
                    st.session_state['role'] = 'officer'
                    st.session_state['officer_name'] = 'Cán bộ trực ca'
                    st.session_state['officer_unit'] = 'Đội Quản lý & Duy tu Đường bộ'
                    st.session_state['officer_login_time'] = datetime.now().strftime('%H:%M:%S %d/%m/%Y')
                    st.rerun()
                else:
                    st.error('Sai mật khẩu.')


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
