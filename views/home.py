"""Trang chủ: Dashboard quản lý tổng quan (KPI, bản đồ phân bố, thống kê theo loại hư hỏng)."""
from html import escape

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from core import db
from core.ui import add_legal_map_layers, disclaimer, is_officer, safe_page_link

SEVERE_LEVEL = 'Cần kiểm tra sớm'
MAP_STATUSES = ('verified', 'assigned', 'fixed')
LEVEL_COLORS = {SEVERE_LEVEL: '#DC2626', 'Trung bình': '#F59E0B', 'Nhẹ': '#16A34A'}
DEFECT_LABELS = {
    'count_D00': 'D00 · Nứt dọc',
    'count_D10': 'D10 · Nứt ngang',
    'count_D20': 'D20 · Nứt mạng lưới',
    'count_D40': 'D40 · Ổ gà',
}

st.markdown("""
<section class="rw-hero" aria-labelledby="roadwatch-title">
  <div class="rw-hero-grid">
    <div>
      <span class="rw-kicker">RoadWatch AI v5.0 · Giám sát hạ tầng đường bộ thông minh</span>
      <h1 id="roadwatch-title">Mỗi phản ánh nhỏ.<br>Một tuyến đường an toàn hơn.</h1>
      <p class="rw-lead">Chụp ảnh mặt đường, định vị GPS chuẩn xác. AI tự động khoanh vùng ổ gà, vết nứt & ước lượng diện tích; cán bộ xác minh và xếp hạng ưu tiên duy tu theo mô hình AHP.</p>
    </div>
    <div class="rw-hero-visual" role="img" aria-label="Minh họa quy trình phản ánh hư hỏng mặt đường đến bản đồ và xác minh">
      <div class="rw-visual-head"><span><span class="rw-visual-dot"></span>Quy trình khép kín</span><span>ROADWATCH v5</span></div>
      <div class="rw-visual-road"><span class="rw-road-line"></span><span class="rw-road-pin"></span></div>
      <div class="rw-visual-flow"><span>01 · Chụp ảnh</span><span>02 · AI phân tích</span><span>03 · Duy tu</span></div>
    </div>
  </div>
</section>
""", unsafe_allow_html=True)

st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
if is_officer():
    c1, c2, c3, c4 = st.columns(4, gap='small')
    with c1:
        safe_page_link('views/submit.py', label='📷  Chụp & gửi phản ánh', icon=None)
    with c2:
        safe_page_link('views/queue.py', label='✅  Hàng chờ thẩm định', icon=None)
    with c3:
        safe_page_link('views/priority.py', label='📊  Xếp hạng AHP & Dự toán', icon=None)
    with c4:
        safe_page_link('views/map.py', label='🗺️  Bản đồ GIS công khai', icon=None)
else:
    a, b, c = st.columns(3, gap='medium')
    with a:
        safe_page_link('views/submit.py', label='📷  Chụp và gửi phản ánh', icon=None)
    with b:
        safe_page_link('views/track.py', label='🔍  Tra cứu mã hồ sơ RW-...', icon=None)
    with c:
        safe_page_link('views/map.py', label='🗺️  Bản đồ điểm đã xác minh', icon=None)

# ── Dashboard tổng quan ────────────────────────────────────────────────────
df = db.fetch_df()
if df.empty:
    recorded = df
else:
    recorded = df[~df.status.isin(['rejected', 'merged'])].copy()

total_recorded = len(recorded)
pending_count = int((df.status == 'pending').sum()) if not df.empty else 0
if recorded.empty:
    new_today = 0
    severe_count = 0
else:
    created = pd.to_datetime(recorded['created_at'], errors='coerce')
    new_today = int((created.dt.normalize() == pd.Timestamp.now().normalize()).sum())
    level = recorded['final_level'].fillna('')
    level = level.where(level != '', recorded['ai_level'].fillna(''))
    recorded['level'] = level
    severe_count = int((level == SEVERE_LEVEL).sum())

st.markdown(
    '<section class="rw-section"><span class="rw-overline">Dashboard quản lý tổng quan</span>'
    '<h2>Tình hình hư hỏng mặt đường thời gian thực</h2>'
    '<p>Số liệu tổng hợp trực tiếp từ cơ sở dữ liệu hệ thống (không tính hồ sơ đã từ chối hoặc đã gộp).</p></section>',
    unsafe_allow_html=True,
)
st.markdown(f"""<div class="rw-overview">
<div class="rw-kpi"><small>📍 Tổng điểm hư hỏng đã ghi nhận</small><strong>{total_recorded}</strong><em>Mọi trạng thái hợp lệ</em></div>
<div class="rw-kpi"><small>🆕 Hư hỏng mới trong ngày</small><strong>{new_today}</strong><em>Ghi nhận hôm nay</em></div>
<div class="rw-kpi"><small>🚨 Hư hỏng nghiêm trọng</small><strong>{severe_count}</strong><em>Mức "Cần kiểm tra sớm"</em></div>
<div class="rw-kpi"><small>⏳ Đang chờ xác minh</small><strong>{pending_count}</strong><em>Trong hàng chờ cán bộ</em></div>
</div>""", unsafe_allow_html=True)

map_col, chart_col = st.columns([3, 2], gap='large')

with map_col:
    st.subheader('🗺️ Bản đồ phân bố hư hỏng')
    points = pd.DataFrame()
    if not recorded.empty:
        points = recorded[recorded.status.isin(MAP_STATUSES)].dropna(subset=['latitude', 'longitude'])
    if points.empty:
        st.info('Chưa có điểm hư hỏng nào được xác minh để hiển thị trên bản đồ.')
    else:
        fmap = folium.Map(
            location=[points.latitude.mean(), points.longitude.mean()],
            zoom_start=13,
            control_scale=True,
            tiles=None,
        )
        add_legal_map_layers(fmap)
        for r in points.itertuples():
            color = LEVEL_COLORS.get(r.level, '#2563EB')
            popup = f'<b>{escape(str(r.location_name))}</b><br>Mức độ: {escape(str(r.level))}<br>Mã: {escape(str(r.id))}'
            folium.CircleMarker(
                location=[r.latitude, r.longitude],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                tooltip=str(r.location_name),
                popup=folium.Popup(popup, max_width=260),
            ).add_to(fmap)
        if len(points) > 1:
            fmap.fit_bounds(
                [[points.latitude.min(), points.longitude.min()], [points.latitude.max(), points.longitude.max()]],
                padding=(30, 30),
            )
        st_folium(fmap, height=420, returned_objects=[], width=None)
        st.caption('🔴 Cần kiểm tra sớm · 🟠 Trung bình · 🟢 Nhẹ. Chỉ hiển thị điểm đã được cán bộ xác minh.')

with chart_col:
    st.subheader('📊 Thống kê theo loại hư hỏng')
    if recorded.empty:
        st.info('Chưa có dữ liệu để thống kê.')
    else:
        stats = pd.Series(
            {label: int(pd.to_numeric(recorded[col], errors='coerce').fillna(0).sum()) for col, label in DEFECT_LABELS.items()}
        )
        if int(stats.sum()) == 0:
            st.info('AI chưa phát hiện vùng hư hỏng nào trong các hồ sơ hiện có.')
        else:
            st.bar_chart(stats, horizontal=True)
            st.caption('Số vùng hư hỏng do AI phát hiện, cộng dồn từ các hồ sơ hợp lệ.')

st.markdown(
    '<div class="rw-footnote">RoadWatch AI hỗ trợ sàng lọc kỹ thuật và lập kế hoạch duy tu đường bộ. '
    'Không sử dụng điện thoại khi đang điều khiển phương tiện giao thông.</div>',
    unsafe_allow_html=True,
)
with st.expander('Quyền riêng tư & nguyên tắc công khai dữ liệu'):
    st.write(
        'Ảnh chờ duyệt không công khai trên bản đồ chung để bảo đảm tính xác thực và quyền riêng tư. '
        'Vui lòng chỉ chụp mặt đường, hạn chế chụp cận cảnh khuôn mặt hoặc biển số phương tiện cá nhân.'
    )
disclaimer()
