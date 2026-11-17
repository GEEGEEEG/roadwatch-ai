"""Trang chủ: Dashboard bố cục 2x2 phong cách Solcast (Cột giới thiệu + KPI bên trái, 4 thẻ dữ liệu bên phải)."""
from html import escape

import altair as alt
import folium
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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
    'count_D20': 'D20 · Nứt lưới',
    'count_D40': 'D40 · Ổ gà',
}
STATUS_ORDER = ['pending', 'verified', 'assigned', 'fixed']
CHART_FONT = 'Arial'
TREND_DAYS = 14
CARD_VISUAL_HEIGHT = 205
MAP_VISUAL_HEIGHT = 250
MAP_MAX_ZOOM = 16

st.markdown("""
<style>
.sol-title {
  font-size: clamp(1.35rem, 1.8vw, 1.6rem) !important;
  font-weight: 800 !important;
  line-height: 1.25 !important;
  color: #0F172A !important;
  letter-spacing: -0.02em;
  margin: 0 0 12px 0;
}
.sol-desc {
  font-size: 0.94rem;
  line-height: 1.55;
  color: #475569;
  margin: 0 0 16px 0;
}
.sol-kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin: 14px 0 18px 0;
}
.sol-kpi {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  padding: 12px 14px;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.03);
}
.sol-kpi small {
  display: block;
  font-size: 0.76rem;
  font-weight: 600;
  color: #64748B;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sol-kpi strong {
  display: block;
  font-size: 1.45rem;
  font-weight: 800;
  color: #0F172A;
  line-height: 1.15;
}
.sol-card-foot {
  padding-top: 8px;
  margin-top: 4px;
}
.sol-card-foot h4 {
  font-size: 1.02rem;
  font-weight: 700;
  color: #0F172A;
  margin: 0 0 8px 0;
}
.sol-card-foot p {
  font-size: 0.85rem;
  line-height: 1.48;
  color: #475569;
  border-left: 3px solid #38BDF8;
  padding-left: 12px;
  margin: 0;
  min-height: 2.95em;
}
[data-testid="stVerticalBlockBorderWrapper"] {
  background: #FFFFFF !important;
  border: 1px solid #E2E8F0 !important;
  border-radius: 12px !important;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04) !important;
}
</style>
""", unsafe_allow_html=True)


def _style(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure(font=CHART_FONT, background='transparent')
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelFont=CHART_FONT,
            titleFont=CHART_FONT,
            labelColor='#64748B',
            gridColor='#E2E8F0',
            domainColor='#CBD5E1',
        )
        .configure_legend(
            labelFont=CHART_FONT,
            titleFont=CHART_FONT,
            title=None,
            orient='bottom',
            labelFontSize=11,
        )
    )


def _show_chart(chart: alt.Chart) -> None:
    st.altair_chart(_style(chart), **stretch(st.altair_chart))


def _card_footer(title: str, desc: str) -> None:
    st.markdown(
        f'<div class="sol-card-foot"><h4>{escape(title)}</h4><p>{escape(desc)}</p></div>',
        unsafe_allow_html=True,
    )


# ── Chuẩn bị dữ liệu tổng hợp ──────────────────────────────────────────────
df = db.fetch_df()
if df.empty:
    recorded = df.copy()
else:
    recorded = df[~df.status.isin(['rejected', 'merged'])].copy()
    recorded['day'] = pd.to_datetime(recorded['created_at'], errors='coerce').dt.normalize()
    level = recorded['final_level'].fillna('')
    level = level.where(level != '', recorded['ai_level'].fillna(''))
    recorded['level'] = level.replace('', 'Chưa phân mức')

total_recorded = len(recorded)
pending_count = int((df.status == 'pending').sum()) if not df.empty else 0
if recorded.empty:
    new_today = 0
    severe_count = 0
else:
    new_today = int((recorded['day'] == pd.Timestamp.now().normalize()).sum())
    severe_count = int((recorded['level'] == SEVERE_LEVEL).sum())

st.markdown("""
<section class="rw-hero" aria-labelledby="roadwatch-title">
  <div class="rw-hero-grid">
    <div>
      <span class="rw-kicker">RoadWatch AI v5.0 · Giám sát hạ tầng đường bộ thông minh</span>
      <h1 id="roadwatch-title">Mỗi phản ánh nhỏ.<br>Một tuyến đường an toàn hơn.</h1>
      <p class="rw-lead">Chụp ảnh mặt đường, định vị GPS chuẩn xác. AI tự động khoanh vùng ổ gà, vết nứt &amp; ước lượng diện tích; cán bộ xác minh và xếp hạng ưu tiên duy tu theo mô hình AHP.</p>
    </div>
    <div class="rw-hero-visual" role="img" aria-label="Minh họa quy trình phản ánh hư hỏng mặt đường đến bản đồ và xác minh">
      <div class="rw-visual-head"><span><span class="rw-visual-dot"></span>Quy trình khép kín</span><span>ROADWATCH v5</span></div>
      <div class="rw-visual-road"><span class="rw-road-line"></span><span class="rw-road-pin"></span></div>
      <div class="rw-visual-flow"><span>01 · Chụp ảnh</span><span>02 · AI phân tích</span><span>03 · Duy tu</span></div>
    </div>
  </div>
</section>
<div style="height: 18px;"></div>
""", unsafe_allow_html=True)

# ── Bố cục Solcast: Trái (Giới thiệu + KPI + Điều hướng) | Phải (Lưới 2x2) ──
left_col, right_col = st.columns([1.05, 2.15], gap='large')

with left_col:
    st.markdown(
        '<div class="sol-title">Dữ liệu &amp; AI phục vụ quản lý duy tu đường bộ</div>'
        '<p class="sol-desc">RoadWatch AI tiếp nhận ảnh mặt đường kèm tọa độ GPS, tự động phát hiện ổ gà, '
        'vết nứt bằng mô hình thị giác máy tính và hỗ trợ cán bộ xác minh, xếp hạng ưu tiên kiểm tra.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(f"""
    <div class="sol-kpi-grid">
      <div class="sol-kpi"><small>📍 Đã ghi nhận</small><strong>{total_recorded}</strong></div>
      <div class="sol-kpi"><small>🆕 Mới hôm nay</small><strong>{new_today}</strong></div>
      <div class="sol-kpi"><small>🚨 Nghiêm trọng</small><strong>{severe_count}</strong></div>
      <div class="sol-kpi"><small>⏳ Chờ xác minh</small><strong>{pending_count}</strong></div>
    </div>
    """, unsafe_allow_html=True)

    safe_page_link('views/submit.py', label='📷 Gửi phản ánh mặt đường', icon=None)
    safe_page_link('views/track.py', label='🔍 Tra cứu mã hồ sơ RW-...', icon=None)
    safe_page_link('views/map.py', label='🗺️ Mở bản đồ GIS toàn trang', icon=None)
    if is_officer():
        safe_page_link('views/queue.py', label='✅ Vào hàng chờ thẩm định', icon=None)

with right_col:
    r1c1, r1c2 = st.columns(2, gap='medium')
    r2c1, r2c2 = st.columns(2, gap='medium')

    # ── Thẻ 1: Phân loại khuyết tật mặt đường (Bar + Line + Ngưỡng TB) ─────
    with r1c1:
        with st.container(border=True):
            if recorded.empty:
                st.info('Chưa có dữ liệu khuyết tật để hiển thị.')
            else:
                counts_df = recorded[list(DEFECT_LABELS)].apply(pd.to_numeric, errors='coerce').fillna(0)
                verified_mask = recorded['status'].isin(MAP_STATUSES)
                all_vals = [int(counts_df[c].sum()) for c in DEFECT_LABELS]
                ver_vals = [int(counts_df.loc[verified_mask, c].sum()) for c in DEFECT_LABELS]
                if sum(all_vals) == 0:
                    st.info('AI chưa phát hiện vùng hư hỏng trong các hồ sơ.')
                else:
                    codes = ['D00', 'D10', 'D20', 'D40']
                    full_names = list(DEFECT_LABELS.values())
                    bar_df = pd.DataFrame({'Mã': codes, 'Tên': full_names, 'Số vùng': all_vals, 'Chuỗi': 'Tất cả hợp lệ'})
                    line_df = pd.DataFrame({'Mã': codes, 'Tên': full_names, 'Số vùng': ver_vals, 'Chuỗi': 'Đã xác minh'})
                    mean_val = round(sum(all_vals) / len(all_vals), 1)
                    rule_df = pd.DataFrame({'Ngưỡng': [mean_val]})

                    x_enc = alt.X('Mã:N', sort=codes, title=None, axis=alt.Axis(labelAngle=0))
                    bars = alt.Chart(bar_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, width=28, opacity=0.45).encode(
                        x=x_enc,
                        y=alt.Y('Số vùng:Q', title=None, axis=alt.Axis(tickMinStep=1)),
                        color=alt.Color('Chuỗi:N', scale=alt.Scale(domain=['Tất cả hợp lệ', 'Đã xác minh'], range=['#38BDF8', '#0F172A'])),
                        tooltip=['Tên:N', 'Số vùng:Q'],
                    )
                    line = alt.Chart(line_df).mark_line(point=alt.OverlayMarkDef(filled=True, size=60), strokeWidth=2.4).encode(
                        x=x_enc,
                        y='Số vùng:Q',
                        color=alt.Color('Chuỗi:N', scale=alt.Scale(domain=['Tất cả hợp lệ', 'Đã xác minh'], range=['#38BDF8', '#0F172A'])),
                        tooltip=['Tên:N', 'Số vùng:Q'],
                    )
                    rule = alt.Chart(rule_df).mark_rule(color='#0284C7', strokeDash=[5, 4], strokeWidth=1.8).encode(
                        y='Ngưỡng:Q',
                        tooltip=[alt.Tooltip('Ngưỡng:Q', title='Trung bình vùng/loại')],
                    )
                    _show_chart((bars + line + rule).properties(height=CARD_VISUAL_HEIGHT))
            _card_footer(
                'Phân loại khuyết tật mặt đường',
                'So sánh số vùng D00, D10, D20, D40 giữa hồ sơ hợp lệ (cột), đã xác minh (đường) và mức trung bình.',
            )

    # ── Thẻ 2: Bản đồ phân bố hư hỏng ────────────────────────────────────────
    with r1c2:
        with st.container(border=True):
            points = pd.DataFrame()
            if not recorded.empty:
                points = recorded[recorded.status.isin(MAP_STATUSES)].dropna(subset=['latitude', 'longitude'])
                points = points[points.latitude.between(-90, 90) & points.longitude.between(-180, 180)]
            if points.empty:
                st.info('Chưa có điểm đã xác minh để hiển thị trên bản đồ.')
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
                        radius=8,
                        color='#FFFFFF',
                        weight=2,
                        fill=True,
                        fill_color=color,
                        fill_opacity=0.95,
                        tooltip=str(r.location_name),
                        popup=folium.Popup(popup, max_width=240),
                    ).add_to(fmap)
                fmap.fit_bounds(
                    [[points.latitude.min(), points.longitude.min()], [points.latitude.max(), points.longitude.max()]],
                    padding=(28, 28),
                    max_zoom=MAP_MAX_ZOOM,
                )
                components.html(fmap.get_root().render(), height=MAP_VISUAL_HEIGHT, scrolling=False)
            _card_footer(
                'Bản đồ phân bố hư hỏng',
                f'Hiển thị {len(points)} điểm đã xác minh trên nền Google Maps, phân màu đỏ, cam, xanh theo mức độ.',
            )

    # ── Thẻ 3: Xu hướng phản ánh theo ngày (Area + Line + Trung bình trượt) ─
    with r2c1:
        with st.container(border=True):
            if recorded.empty:
                st.info('Chưa có dữ liệu theo ngày để vẽ xu hướng.')
            else:
                today = pd.Timestamp.now().normalize()
                days = pd.date_range(end=today, periods=TREND_DAYS)
                daily = recorded.groupby('day').size().reindex(days, fill_value=0)
                trend = pd.DataFrame({
                    'Ngày': days,
                    'Số phản ánh': daily.values,
                    'TB trượt 3 ngày': daily.rolling(3, min_periods=1).mean().round(2).values,
                })
                x_t = alt.X('Ngày:T', title=None, axis=alt.Axis(format='%d/%m', labelAngle=0, tickCount=6))
                area = alt.Chart(trend).mark_area(
                    color='#38BDF8',
                    opacity=0.22,
                    line={'color': '#0F172A', 'strokeWidth': 2.2},
                    point={'color': '#0F172A', 'filled': True, 'size': 36},
                ).encode(
                    x=x_t,
                    y=alt.Y('Số phản ánh:Q', title=None, axis=alt.Axis(tickMinStep=1)),
                    tooltip=[alt.Tooltip('Ngày:T', format='%d/%m/%Y'), 'Số phản ánh:Q', 'TB trượt 3 ngày:Q'],
                )
                ma_line = alt.Chart(trend).mark_line(color='#0284C7', strokeDash=[5, 4], strokeWidth=2).encode(
                    x=x_t,
                    y='TB trượt 3 ngày:Q',
                )
                _show_chart((area + ma_line).properties(height=CARD_VISUAL_HEIGHT))
            _card_footer(
                'Xu hướng phản ánh theo ngày',
                f'Theo dõi lượng báo cáo mới trong {TREND_DAYS} ngày gần nhất kèm đường trung bình trượt 3 ngày.',
            )

    # ── Thẻ 4: Tiến độ xử lý hồ sơ (Horizontal Bar bắt đầu từ 0) ────────────
    with r2c2:
        with st.container(border=True):
            if df.empty:
                st.info('Chưa có hồ sơ để thống kê tiến độ xử lý.')
            else:
                sc = df['status'].value_counts()
                status_labels = [STATUS_LABELS[k] for k in STATUS_ORDER]
                status_colors = ['#F59E0B', '#2563EB', '#0EA5E9', '#16A34A']
                status_df = pd.DataFrame({
                    'Trạng thái': status_labels,
                    'Số hồ sơ': [int(sc.get(k, 0)) for k in STATUS_ORDER],
                })
                max_val = max(int(status_df['Số hồ sơ'].max()), 1)
                base = alt.Chart(status_df).encode(
                    y=alt.Y('Trạng thái:N', sort=status_labels, title=None, axis=alt.Axis(labelLimit=140)),
                    x=alt.X('Số hồ sơ:Q', title=None, scale=alt.Scale(domain=[0, max_val + 1]), axis=alt.Axis(tickMinStep=1)),
                )
                hbar = base.mark_bar(cornerRadiusEnd=5, size=24).encode(
                    color=alt.Color(
                        'Trạng thái:N',
                        legend=None,
                        scale=alt.Scale(domain=status_labels, range=status_colors),
                    ),
                    tooltip=['Trạng thái:N', 'Số hồ sơ:Q'],
                )
                labels_txt = base.mark_text(align='left', dx=6, font=CHART_FONT, fontWeight='bold', color='#0F172A').encode(
                    text='Số hồ sơ:Q'
                )
                _show_chart((hbar + labels_txt).properties(height=CARD_VISUAL_HEIGHT))
            _card_footer(
                'Tiến độ xử lý hồ sơ',
                'Số lượng hồ sơ qua 4 bước từ chờ xác minh, đã duyệt, đang giao xử lý đến đã hoàn thành.',
            )

st.markdown(
    '<div class="rw-footnote">RoadWatch AI hỗ trợ sàng lọc kỹ thuật và lập kế hoạch duy tu đường bộ. '
    'Không sử dụng điện thoại khi đang điều khiển phương tiện giao thông.</div>',
    unsafe_allow_html=True,
)
disclaimer()
