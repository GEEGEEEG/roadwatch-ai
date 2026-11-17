"""Trang chủ: Dashboard quản lý tổng quan (KPI, bản đồ phân bố, biểu đồ xu hướng & cơ cấu hư hỏng)."""
from html import escape

import altair as alt
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from core import db
from core.constants import STATUS_LABELS
from core.ui import add_legal_map_layers, disclaimer, is_officer, safe_page_link, stretch

SEVERE_LEVEL = 'Cần kiểm tra sớm'
MAP_STATUSES = ('verified', 'assigned', 'fixed')
LEVEL_COLORS = {SEVERE_LEVEL: '#DC2626', 'Trung bình': '#F59E0B', 'Nhẹ': '#16A34A'}
LEVEL_ORDER = [SEVERE_LEVEL, 'Trung bình', 'Nhẹ']
DEFECT_LABELS = {
    'count_D00': 'D00 · Nứt dọc',
    'count_D10': 'D10 · Nứt ngang',
    'count_D20': 'D20 · Nứt mạng lưới',
    'count_D40': 'D40 · Ổ gà',
}
DEFECT_COLORS = ['#2563EB', '#0EA5E9', '#F59E0B', '#DC2626']
STATUS_ORDER = ['pending', 'verified', 'assigned', 'fixed']
STATUS_COLORS = ['#F59E0B', '#2563EB', '#0EA5E9', '#16A34A']
CHART_FONT = 'Times New Roman'
TREND_DAYS = 14
MAP_MAX_ZOOM = 16
MAP_HEIGHT = 440
GROUPED_CHART_HEIGHT = 370  # chiều cao vùng vẽ; cộng trục + chú thích ≈ MAP_HEIGHT


def _style(chart):
    return (
        chart.configure(font=CHART_FONT, background='transparent')
        .configure_view(strokeWidth=0)
        .configure_axis(labelFont=CHART_FONT, titleFont=CHART_FONT, gridColor='#E2E8F0', domainColor='#CBD5E1')
        .configure_legend(labelFont=CHART_FONT, titleFont=CHART_FONT, orient='bottom')
    )


def _show(chart):
    st.altair_chart(_style(chart), **stretch(st.altair_chart))


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
    recorded['day'] = pd.to_datetime(recorded['created_at'], errors='coerce').dt.normalize()
    new_today = int((recorded['day'] == pd.Timestamp.now().normalize()).sum())
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

# ── Hàng 1: Bản đồ + Tỷ trọng mức độ + Tiến độ xử lý ───────────────────────
map_col, side_col = st.columns(2, gap='large')

with map_col:
    st.subheader('🗺️ Bản đồ phân bố hư hỏng')
    points = pd.DataFrame()
    if not recorded.empty:
        points = recorded[recorded.status.isin(MAP_STATUSES)].dropna(subset=['latitude', 'longitude'])
        points = points[points.latitude.between(-90, 90) & points.longitude.between(-180, 180)]
    if points.empty:
        st.info('Chưa có điểm hư hỏng nào được xác minh để hiển thị trên bản đồ.')
    else:
        fmap = folium.Map(
            location=[points.latitude.mean(), points.longitude.mean()],
            zoom_start=MAP_MAX_ZOOM,
            max_zoom=20,
            control_scale=True,
            tiles=None,
        )
        add_legal_map_layers(fmap)
        for r in points.itertuples():
            color = LEVEL_COLORS.get(r.level, '#2563EB')
            popup = f'<b>{escape(str(r.location_name))}</b><br>Mức độ: {escape(str(r.level))}<br>Mã: {escape(str(r.id))}'
            folium.CircleMarker(
                location=[r.latitude, r.longitude],
                radius=9,
                color='#FFFFFF',
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.95,
                tooltip=str(r.location_name),
                popup=folium.Popup(popup, max_width=260),
            ).add_to(fmap)
        # Giới hạn mức zoom tối đa để các điểm gần nhau không bị phóng quá sâu khiến bản đồ trống
        fmap.fit_bounds(
            [[points.latitude.min(), points.longitude.min()], [points.latitude.max(), points.longitude.max()]],
            padding=(40, 40),
            max_zoom=MAP_MAX_ZOOM,
        )
        st_folium(fmap, height=MAP_HEIGHT, returned_objects=[], width=None, key='home_dashboard_map')
        st.caption(
            f'🔴 Cần kiểm tra sớm · 🟠 Trung bình · 🟢 Nhẹ · Đang hiển thị {len(points)} điểm đã được cán bộ xác minh.'
        )

with side_col:
    st.subheader('📊 Số vùng hư hỏng theo loại')
    if recorded.empty:
        st.info('Chưa có dữ liệu để thống kê.')
    else:
        counts_df = recorded[list(DEFECT_LABELS)].apply(pd.to_numeric, errors='coerce').fillna(0)
        verified_mask = recorded['status'].isin(MAP_STATUSES)
        rows = []
        for col, label in DEFECT_LABELS.items():
            rows.append({'Loại hư hỏng': label, 'Nhóm': 'Tất cả hồ sơ hợp lệ', 'Số vùng': int(counts_df[col].sum())})
            rows.append({'Loại hư hỏng': label, 'Nhóm': 'Đã được xác minh', 'Số vùng': int(counts_df.loc[verified_mask, col].sum())})
        grouped_df = pd.DataFrame(rows)
        if int(grouped_df['Số vùng'].sum()) == 0:
            st.info('AI chưa phát hiện vùng hư hỏng nào trong các hồ sơ hiện có.')
        else:
            type_order = list(DEFECT_LABELS.values())
            group_order = ['Tất cả hồ sơ hợp lệ', 'Đã được xác minh']
            gbase = alt.Chart(grouped_df).encode(
                y=alt.Y('Loại hư hỏng:N', sort=type_order, title=None, axis=alt.Axis(labelLimit=220)),
                yOffset=alt.YOffset('Nhóm:N', sort=group_order),
                x=alt.X('Số vùng:Q', title=None, axis=alt.Axis(tickMinStep=1, grid=True)),
            )
            gbars = gbase.mark_bar(size=22).encode(
                color=alt.Color('Nhóm:N', sort=group_order, scale=alt.Scale(domain=group_order, range=['#3B5BF6', '#55B5F8'])),
                tooltip=['Loại hư hỏng:N', 'Nhóm:N', 'Số vùng:Q'],
            )
            glabels = gbase.mark_text(align='left', dx=5, font=CHART_FONT).encode(text='Số vùng:Q')
            _show((gbars + glabels).properties(height=GROUPED_CHART_HEIGHT))
            st.caption('Số vùng hư hỏng do AI phát hiện, so sánh tất cả hồ sơ hợp lệ với các hồ sơ đã được cán bộ xác minh.')

donut_col, status_col = st.columns(2, gap='large')

with donut_col:
    st.subheader('🍩 Tỷ trọng mức độ nghiêm trọng')
    if recorded.empty:
        st.info('Chưa có dữ liệu để thống kê.')
    else:
        lv = recorded['level'].value_counts()
        donut_df = pd.DataFrame({'Mức độ': LEVEL_ORDER, 'Số điểm': [int(lv.get(k, 0)) for k in LEVEL_ORDER]})
        donut_df = donut_df[donut_df['Số điểm'] > 0]
        if donut_df.empty:
            st.info('Chưa có hồ sơ nào được đánh giá mức độ.')
        else:
            donut = (
                alt.Chart(donut_df)
                .mark_arc(innerRadius=62, outerRadius=105, stroke='#FFFFFF', strokeWidth=2)
                .encode(
                    theta=alt.Theta('Số điểm:Q'),
                    color=alt.Color(
                        'Mức độ:N',
                        sort=LEVEL_ORDER,
                        scale=alt.Scale(domain=LEVEL_ORDER, range=[LEVEL_COLORS[k] for k in LEVEL_ORDER]),
                    ),
                    tooltip=['Mức độ:N', 'Số điểm:Q'],
                )
                .properties(height=250)
            )
            _show(donut)

with status_col:
    st.subheader('📌 Tiến độ xử lý hồ sơ')
    if df.empty:
        st.info('Chưa có dữ liệu để thống kê.')
    else:
        sc = df['status'].value_counts()
        status_df = pd.DataFrame({
            'Trạng thái': [STATUS_LABELS[k] for k in STATUS_ORDER],
            'Số hồ sơ': [int(sc.get(k, 0)) for k in STATUS_ORDER],
        })
        base = alt.Chart(status_df).encode(
            y=alt.Y('Trạng thái:N', sort=[STATUS_LABELS[k] for k in STATUS_ORDER], title=None),
            x=alt.X('Số hồ sơ:Q', title=None, axis=alt.Axis(tickMinStep=1)),
        )
        bars = base.mark_bar(cornerRadiusEnd=5, size=30).encode(
            color=alt.Color(
                'Trạng thái:N',
                legend=None,
                scale=alt.Scale(domain=[STATUS_LABELS[k] for k in STATUS_ORDER], range=STATUS_COLORS),
            ),
            tooltip=['Trạng thái:N', 'Số hồ sơ:Q'],
        )
        labels = base.mark_text(align='left', dx=5, font=CHART_FONT, fontWeight='bold').encode(text='Số hồ sơ:Q')
        _show((bars + labels).properties(height=250))

# ── Hàng 2: Xu hướng theo ngày + Cơ cấu loại hư hỏng theo ngày ──────────────
trend_col, type_col = st.columns(2, gap='large')
today = pd.Timestamp.now().normalize()
days = pd.date_range(end=today, periods=TREND_DAYS)

with trend_col:
    st.subheader('📈 Xu hướng phản ánh theo ngày')
    if recorded.empty:
        st.info('Chưa có dữ liệu để thống kê.')
    else:
        daily = recorded.groupby('day').size().reindex(days, fill_value=0)
        trend = pd.DataFrame({'Ngày': days, 'Số phản ánh': daily.values})
        trend['Trung bình trượt 3 ngày'] = trend['Số phản ánh'].rolling(3, min_periods=1).mean().round(2)
        x_enc = alt.X('Ngày:T', title=None, axis=alt.Axis(format='%d/%m', labelAngle=0, tickCount=7))
        area = alt.Chart(trend).mark_area(
            color='#2563EB',
            opacity=0.18,
            line={'color': '#2563EB', 'strokeWidth': 2.5},
            point={'color': '#2563EB', 'filled': True, 'size': 55},
        ).encode(
            x=x_enc,
            y=alt.Y('Số phản ánh:Q', title=None, axis=alt.Axis(tickMinStep=1)),
            tooltip=[alt.Tooltip('Ngày:T', format='%d/%m/%Y'), 'Số phản ánh:Q', 'Trung bình trượt 3 ngày:Q'],
        )
        avg = alt.Chart(trend).mark_line(color='#F59E0B', strokeDash=[6, 4], strokeWidth=2.5).encode(
            x=x_enc, y='Trung bình trượt 3 ngày:Q'
        )
        _show((area + avg).properties(height=280))
        st.caption(f'Vùng xanh: số phản ánh mới mỗi ngày · Đường cam nét đứt: trung bình trượt 3 ngày ({TREND_DAYS} ngày gần nhất).')

with type_col:
    st.subheader('📊 Cơ cấu loại hư hỏng theo ngày')
    if recorded.empty:
        st.info('Chưa có dữ liệu để thống kê.')
    else:
        num = recorded[list(DEFECT_LABELS)].apply(pd.to_numeric, errors='coerce').fillna(0)
        num['day'] = recorded['day']
        by_day = num.groupby('day').sum().reindex(days, fill_value=0).rename(columns=DEFECT_LABELS)
        if int(by_day.to_numpy().sum()) == 0:
            st.info('AI chưa phát hiện vùng hư hỏng nào trong các hồ sơ hiện có.')
        else:
            by_day.index.name = 'Ngày'
            long_df = by_day.reset_index().melt(id_vars='Ngày', var_name='Loại hư hỏng', value_name='Số vùng')
            long_df['Nhãn'] = long_df['Ngày'].dt.strftime('%d/%m')
            order = [d.strftime('%d/%m') for d in days]
            stacked = alt.Chart(long_df).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                x=alt.X('Nhãn:N', sort=order, title=None, axis=alt.Axis(labelAngle=0, labelOverlap='parity')),
                y=alt.Y('Số vùng:Q', title=None, axis=alt.Axis(tickMinStep=1)),
                color=alt.Color(
                    'Loại hư hỏng:N',
                    scale=alt.Scale(domain=list(DEFECT_LABELS.values()), range=DEFECT_COLORS),
                ),
                tooltip=['Nhãn:N', 'Loại hư hỏng:N', 'Số vùng:Q'],
            ).properties(height=280)
            _show(stacked)
            st.caption('Số vùng hư hỏng do AI phát hiện, xếp chồng theo loại D00, D10, D20, D40.')

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
