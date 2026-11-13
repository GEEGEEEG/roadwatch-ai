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


def detector_or_stop(silent: bool = False):
    """Trả về detector YOLO.
    silent=True → trả về None nếu không có model (thay vì st.stop()),
    dùng cho preview không bắt buộc."""
    if not model_path().is_file():
        if silent:
            return None
        st.error(f'Thiếu mô hình tại {model_path()}. Tải checkpoint 4 lớp D00/D10/D20/D40 và đặt đúng vị trí.')
        st.stop()
    try:
        return get_detector()
    except Exception as exc:
        if silent:
            return None
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


def steps(*items, active=0):
    """Custom Stepper 3 bước trực quan với vòng tròn số phát sáng và đường line đổi màu."""
    if not items:
        return
    nodes_html = []
    for i, label in enumerate(items):
        if i < active:
            cls = 'completed'
            icon = '✓'
        elif i == active:
            cls = 'active'
            icon = str(i + 1)
        else:
            cls = 'pending'
            icon = str(i + 1)

        node = f'<div class="rw-step-node {cls}"><div class="rw-step-circle">{icon}</div><div class="rw-step-label">{escape(label)}</div></div>'
        nodes_html.append(node)
        if i < len(items) - 1:
            line_cls = 'completed-line' if i < active else ''
            nodes_html.append(f'<div class="rw-step-line {line_cls}"></div>')

    full_html = f'<div class="rw-stepper-box"><div class="rw-stepper">{"".join(nodes_html)}</div></div>'
    st.markdown(full_html, unsafe_allow_html=True)


def confetti_celebrate():
    """Bắn pháo hoa Confetti siêu nhẹ (JS thuần, không phụ thuộc package ngoài)."""
    import streamlit.components.v1 as components
    js = """
    <canvas id="confetti-canvas" style="position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:999999;"></canvas>
    <script>
      (function() {
        const canvas = document.getElementById('confetti-canvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        const colors = ['#2563EB', '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];
        const pieces = [];
        for (let i = 0; i < 75; i++) {
          pieces.push({
            x: canvas.width / 2 + (Math.random() - 0.5) * 200,
            y: canvas.height * 0.35,
            vx: (Math.random() - 0.5) * 14,
            vy: (Math.random() - 0.85) * 16,
            size: Math.random() * 9 + 4,
            color: colors[Math.floor(Math.random() * colors.length)],
            rotation: Math.random() * 360,
            rotSpeed: (Math.random() - 0.5) * 10,
            opacity: 1
          });
        }
        
        let startTime = Date.now();
        function frame() {
          const elapsed = Date.now() - startTime;
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          
          let alive = false;
          for (const p of pieces) {
            p.x += p.vx;
            p.y += p.vy;
            p.vy += 0.38;
            p.rotation += p.rotSpeed;
            p.opacity = Math.max(0, 1 - elapsed / 2600);
            
            if (p.opacity > 0 && p.y < canvas.height + 20) {
              alive = true;
              ctx.save();
              ctx.translate(p.x, p.y);
              ctx.rotate(p.rotation * Math.PI / 180);
              ctx.fillStyle = p.color;
              ctx.globalAlpha = p.opacity;
              ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6);
              ctx.restore();
            }
          }
          if (alive && elapsed < 2600) {
            requestAnimationFrame(frame);
          } else {
            canvas.remove();
          }
        }
        requestAnimationFrame(frame);
      })();
    </script>
    """
    components.html(js, height=0, width=0)


def safe_csv_export(df):
    """Ngăn công thức spreadsheet ngoài ý muốn từ chuỗi do người dùng nhập."""
    clone=df.copy()
    for col in clone.select_dtypes(include=['object','string']).columns:
        clone[col]=clone[col].map(lambda v: "'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@','\t','\r')) else v)
    return clone.to_csv(index=False).encode('utf-8-sig')
