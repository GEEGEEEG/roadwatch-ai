"""Tiện ích dùng chung cho giao diện Streamlit (v5.0)."""
import base64
from functools import lru_cache
import io
from html import escape

import folium
import streamlit as st

from .config import PROJECT_ROOT, data_dir, model_path
from .constants import DISCLAIMER


@lru_cache(maxsize=2)
def _brand_logo_uri() -> str:
    p = PROJECT_ROOT / 'assets' / 'logo_roadwatch.png'
    if not p.is_file():
        return ''
    return f'data:image/png;base64,{base64.b64encode(p.read_bytes()).decode("ascii")}'

_OFFICER_SESSION_KEYS = (
    'role',
    'officer_username',
    'officer_name',
    'officer_unit',
    'officer_role_level',
    'officer_login_time',
)


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


def is_officer() -> bool:
    return st.session_state.get('role') == 'officer'


def officer_role() -> str:
    return str(st.session_state.get('officer_role_level') or 'officer')


def current_actor() -> str:
    """Trả về mã định danh cán bộ thực tế đang thao tác để ghi vào Audit Log."""
    uname = str(st.session_state.get('officer_username') or '').strip()
    if uname:
        return uname
    name = str(st.session_state.get('officer_name') or '').strip()
    return name or 'officer'


def clear_officer_session() -> None:
    for k in _OFFICER_SESSION_KEYS:
        st.session_state.pop(k, None)
    st.session_state['role'] = 'citizen'


def officer_login_box():
    """Trạng thái đăng nhập cán bộ gọn trên thanh bên (không lặp lại logo chính)."""
    with st.sidebar:
        if is_officer():
            officer = escape(str(st.session_state.get('officer_name', 'Cán bộ trực ca')))
            role_tag = {'admin': 'Quản trị', 'officer': 'Thẩm định', 'field_team': 'Duy tu'}.get(officer_role(), 'Cán bộ')
            st.markdown(
                f'<div class="rw-sidebar-info"><b>{officer}</b> · <span>{escape(role_tag)}</span></div>',
                unsafe_allow_html=True,
            )
            if st.button('Đăng xuất', key='btn_officer_logout', use_container_width=True):
                clear_officer_session()
                st.rerun()
        else:
            st.markdown(
                '<div class="rw-sidebar-info">Khu vực điều hành dành riêng cho cán bộ được cấp quyền.</div>',
                unsafe_allow_html=True,
            )


def safe_page_link(page: str, label: str, icon: str | None = None) -> None:
    """Liên kết chuyển trang an toàn cả khi chạy qua st.navigation (kể cả qua bridge) lẫn khi chạy độc lập."""
    try:
        st.page_link((PROJECT_ROOT / page).resolve(), label=label, icon=icon)
        return
    except Exception:
        pass
    try:
        st.page_link(page, label=label, icon=icon)
    except Exception:
        pass


def require_officer(allowed_roles: tuple[str, ...] | None = None):
    if not is_officer():
        st.warning('Trang này chỉ dành cho cán bộ. Đăng nhập ở thanh bên hoặc mở Cổng cán bộ.')
        safe_page_link('views/login.py', label='Mở Cổng Đăng Nhập Cán Bộ', icon=None)
        st.stop()
    if allowed_roles and officer_role() not in allowed_roles:
        st.warning('Tài khoản hiện tại không thuộc nhóm quyền thực hiện chức năng này.')
        st.stop()


def disclaimer():
    st.caption(DISCLAIMER)


@st.cache_resource(show_spinner='Đang tải mô hình nhận diện AI...')
def get_detector():
    from .detector import RoadDamageDetector
    return RoadDamageDetector(model_path())


def detector_or_stop(silent: bool = False):
    """Trả về detector YOLO/ONNX. silent=True -> trả None thay vì st.stop() khi thiếu model."""
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


def image_file(rel: str | None) -> str | None:
    """Lấy đường dẫn file ảnh cục bộ; nếu container vừa khởi động lại thì tự khôi phục từ Supabase Storage."""
    if not rel:
        return None
    p = data_dir() / rel
    if not p.is_file():
        try:
            from . import storage
            if storage.is_enabled():
                data = storage.download(rel)
                if data:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(data)
        except Exception:
            pass
    return str(p) if p.is_file() else None


def image_url_or_file(rel: str | None, public_only: bool = True) -> str | None:
    """Ưu tiên URL CDN Supabase (không tốn đĩa/RAM container) cho giao diện web; fallback về file cục bộ."""
    if not rel:
        return None
    p = data_dir() / rel
    if p.is_file():
        return str(p)
    try:
        from . import storage
        if storage.is_enabled() and storage.get_backend_type() == 'supabase':
            url = storage.get_public_url(rel) if public_only else storage.get_signed_url(rel)
            if url:
                return url
    except Exception:
        pass
    return image_file(rel)


class _BaseLayerControl(folium.LayerControl):
    """Chỉ đưa các lớp nền (TileLayer, overlay=False) vào bộ chuyển đổi nền bản đồ.
    Ngăn lỗi JS undefined khi các lớp overlay (MarkerCluster, HeatMap, CircleMarker) được thêm sau."""
    def render(self, **kwargs):
        self.overlays.clear()
        for item in self._parent._children.values():
            if isinstance(item, folium.map.Layer) and item.control and not item.overlay:
                self.base_layers[item.layer_name] = item.get_name()
        super(folium.LayerControl, self).render(**kwargs)


def add_legal_map_layers(fmap: folium.Map) -> None:
    """Thêm các lớp bản đồ nền trực quan, hiển thị đầy đủ tên đường (Google Maps, Google Hybrid, OSM)."""
    # 1. Google Maps Đường phố (Mặc định: hiện đầy đủ tên đường, ngõ hẻm, địa danh tiếng Việt)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr='Google Maps',
        name='Bản đồ Đường phố (Google Maps)',
        overlay=False,
        control=True,
        show=True,
        max_zoom=20,
    ).add_to(fmap)
    # 2. Google Maps Vệ tinh Hybrid (Ảnh vệ tinh có tên đường & địa danh)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google Maps Hybrid',
        name='Ảnh Vệ tinh có Tên đường (Google Hybrid)',
        overlay=False,
        control=True,
        show=False,
        max_zoom=20,
    ).add_to(fmap)
    # 3. Bản đồ OpenStreetMap tiêu chuẩn
    folium.TileLayer(
        tiles='https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        name='Bản đồ Đường phố (OpenStreetMap)',
        overlay=False,
        control=True,
        show=False,
        max_zoom=19,
    ).add_to(fmap)
    # 4. Ảnh Vệ tinh thuần túy (Esri World Imagery)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics',
        name='Ảnh Vệ tinh thuần túy (Esri)',
        overlay=False,
        control=True,
        show=False,
        max_zoom=19,
    ).add_to(fmap)
    _BaseLayerControl(position='topright', collapsed=True).add_to(fmap)


PRIORITY_PRESETS = {
    'Cân bằng tiêu chuẩn (Mặc định)': (50, 30, 20, 40, 'Cân bằng giữa độ nặng, phản ánh dân và cấp đường.'),
    'An toàn khẩn cấp (Ổ gà sâu)': (70, 15, 15, 35, 'Ưu tiên tối đa các vị trí hư hại nặng, nguy cơ tai nạn.'),
    'Trục chính & Trường / Bệnh viện': (35, 15, 50, 45, 'Ưu tiên tuyến quốc lộ, huyết mạch lưu lượng xe lớn.'),
    'Theo phản ánh cộng đồng': (30, 55, 15, 50, 'Ưu tiên điểm nóng có nhiều người dân phản ánh lặp lại.'),
    'Tùy chỉnh thủ công (Chuyên gia)': (None, None, None, None, 'Tự điều chỉnh từng trọng số và bán kính bên dưới.'),
}


def weights_sidebar():
    """Bộ chọn kịch bản ưu tiên trực quan cho cán bộ + tùy chỉnh nâng cao cho chuyên gia."""
    ss = st.session_state
    preset_names = list(PRIORITY_PRESETS.keys())
    mode = st.sidebar.selectbox(
        'Chế độ ưu tiên duy tu',
        preset_names,
        index=ss.get('_w_preset_idx', 0),
        help='Cán bộ không cần hiểu công thức toán vẫn chọn nhanh được kịch bản phù hợp thực tế.',
    )
    ss['_w_preset_idx'] = preset_names.index(mode)
    pa, pb, pc, pr, desc = PRIORITY_PRESETS[mode]
    st.sidebar.caption(desc)

    is_custom = pa is None
    if not is_custom:
        a, b, c, r = pa, pb, pc, pr
        st.sidebar.caption(f'Áp dụng: **Mức độ {a}% · Phản ánh {b}% · Tuyến {c}% · Gom {r}m**')
    else:
        a, b, c, r = ss.get('_wa', 50), ss.get('_wb', 30), ss.get('_wc', 20), ss.get('_wr', 40)

    with st.sidebar.expander('Tinh chỉnh chi tiết (Nâng cao)', expanded=is_custom):
        a = st.slider('Trọng số mức độ (%)', 0, 100, int(a), 5, disabled=not is_custom)
        b = st.slider('Trọng số số báo cáo (%)', 0, 100, int(b), 5, disabled=not is_custom)
        c = st.slider('Trọng số cấp tuyến (%)', 0, 100, int(c), 5, disabled=not is_custom)
        r = st.slider('Bán kính gom điểm nóng (m)', 10, 200, int(r), 5, disabled=not is_custom)
        if not is_custom:
            st.caption('Chọn mục **"Tùy chỉnh thủ công"** ở trên nếu bạn muốn kéo tay các thông số này.')
        else:
            st.caption('Nếu tổng ≠ 100% hệ thống tự chuẩn hóa.')

    ss['_wa'], ss['_wb'], ss['_wc'], ss['_wr'] = a, b, c, r
    return (a, b, c), float(r)


def qr_png(text: str) -> bytes:
    import qrcode
    buf = io.BytesIO()
    qrcode.make(text).save(buf, format='PNG')
    return buf.getvalue()


def page_intro(kicker: str, title: str, description: str, compact: bool = True):
    if compact:
        st.markdown(
            '<div class="rw-page-head"><h1>'
            + escape(title)
            + '</h1><p>'
            + escape(description)
            + '</p></div>',
            unsafe_allow_html=True,
        )
        return
    st.markdown(
        '<div class="rw-page-intro"><span class="rw-overline">'
        + escape(kicker)
        + '</span><h1>'
        + escape(title)
        + '</h1><p>'
        + escape(description)
        + '</p></div>',
        unsafe_allow_html=True,
    )


def kpi_grid(items: list[tuple[str, object]], cols: int = 4) -> None:
    """Responsive CSS Grid KPI cards (prevents 1-column vertical stacking at 1280px with open sidebar)."""
    n = max(2, min(5, int(cols)))
    cards = ''.join(
        f'<div class="rw-kpi-card"><small>{escape(str(lbl))}</small><strong>{escape(str(val))}</strong></div>'
        for lbl, val in items
    )
    st.markdown(f'<div class="rw-kpi-row rw-kpi-cols-{n}">{cards}</div>', unsafe_allow_html=True)


def steps(*items, active: int = 0):
    if not items:
        return
    nodes_html = []
    for i, label in enumerate(items):
        if i < active:
            cls, icon = 'completed', '✓'
        elif i == active:
            cls, icon = 'active', str(i + 1)
        else:
            cls, icon = 'pending', str(i + 1)
        node = (
            f'<div class="rw-step-node {cls}">'
            f'<div class="rw-step-circle">{icon}</div>'
            f'<div class="rw-step-label">{escape(label)}</div></div>'
        )
        nodes_html.append(node)
        if i < len(items) - 1:
            line_cls = 'completed-line' if i < active else ''
            nodes_html.append(f'<div class="rw-step-line {line_cls}"></div>')
    st.markdown(f'<div class="rw-stepper-box"><div class="rw-stepper">{"".join(nodes_html)}</div></div>', unsafe_allow_html=True)


def confetti_celebrate():
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
            p.x += p.vx; p.y += p.vy; p.vy += 0.38;
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
          if (alive && elapsed < 2600) requestAnimationFrame(frame);
          else canvas.remove();
        }
        requestAnimationFrame(frame);
      })();
    </script>
    """
    components.html(js, height=0, width=0)


def safe_csv_export(df):
    clone = df.copy()
    for col in clone.select_dtypes(include=['object', 'string']).columns:
        clone[col] = clone[col].map(
            lambda v: "'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else v
        )
    return clone.to_csv(index=False).encode('utf-8-sig')
