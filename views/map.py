from html import escape

import folium
import streamlit as st
import streamlit.components.v1 as components
from folium.plugins import HeatMap, MarkerCluster

from core import db, storage
from core.constants import LEVELS
from core.corridor_hotspot import analyze_corridor_clusters
from core.priority import DEFAULT_WEIGHTS, build_hotspots
from core.ui import add_legal_map_layers, disclaimer, is_officer, page_intro, weights_sidebar

page_intro(
    'BẢN ĐỒ GIS CÔNG KHAI',
    'Bản đồ điểm hư hỏng & hành lang xuống cấp',
    'Hiển thị các vị trí đã được cán bộ xác minh và vùng cảnh báo xuống cấp diện rộng phục vụ quy hoạch bảo trì.',
)

if is_officer():
    weights, radius = weights_sidebar()
else:
    weights, radius = DEFAULT_WEIGHTS, 40.0

df = db.fetch_df()
if df.empty:
    st.info('Chưa có điểm nào được xác minh.')
    disclaimer()
    st.stop()

hs = build_hotspots(df, weights, radius)
if hs.empty:
    st.info('Chưa có điểm nào được xác minh.')
    disclaimer()
    st.stop()

corridors = analyze_corridor_clusters(df, max_distance_m=250.0, min_cluster_size=3)
wide_degradations = [c for c in corridors if c['is_wide_degradation']]
if wide_degradations:
    top_c = wide_degradations[0]
    st.error(
        f"**CẢNH BÁO QUY HOẠCH TUYẾN:** **{top_c['location_summary']}** xuất hiện cụm **{top_c['cluster_size']} điểm hư hỏng liên hoàn** "
        f"(trải dài ~{top_c['span_length_m']} m). **{top_c['proposal']}** · Dự toán: ~{top_c['formatted_cost']}."
    )

with st.container(border=True, key='rw_glass_map_filter'):
    levels = st.multiselect('Lọc theo mức độ', LEVELS, default=LEVELS)
    col_f1, col_f2 = st.columns(2)
    heat = col_f1.checkbox('Hiện bản đồ nhiệt')
    show_corridors = col_f2.checkbox('Hiện hành lang xuống cấp', value=True)

hs = hs[hs.severity_label.isin(levels)]
if hs.empty:
    st.info('Không có điểm khớp bộ lọc.')
    st.stop()

colors = {'Cần kiểm tra sớm': 'red', 'Trung bình': 'orange', 'Nhẹ': 'green', 'Không phát hiện': 'blue'}
m = folium.Map(location=[hs.latitude.mean(), hs.longitude.mean()], zoom_start=13, control_scale=True, tiles=None)
add_legal_map_layers(m)

# Vẽ trực tiếp các Hành lang Xuống cấp Diện rộng (Corridors) lên bản đồ GIS
if show_corridors and wide_degradations:
    for cor in wide_degradations:
        coords = cor.get('ordered_coords') or []
        pop_cor = (
            f"<b>Hành lang xuống cấp diện rộng</b><br>"
            f"Tuyến: {escape(cor['location_summary'])}<br>"
            f"Quy mô: {cor['cluster_size']} điểm (~{cor['span_length_m']} m)<br>"
            f"Tổng diện tích hư hại: {cor['total_area_m2']} m²<br>"
            f"Dự toán thảm lại: <b>{escape(cor['formatted_cost'])}</b>"
        )
        if len(coords) >= 2:
            folium.PolyLine(
                locations=coords,
                color='#DC2626',
                weight=8,
                opacity=0.65,
                dash_array='10, 8',
                popup=folium.Popup(pop_cor, max_width=300),
                tooltip=f"Cụm xuống cấp ({cor['cluster_size']} điểm)",
            ).add_to(m)
        folium.Circle(
            location=[cor['center_lat'], cor['center_lon']],
            radius=max(60.0, cor['span_length_m'] / 2.0 + 25.0),
            color='#DC2626',
            weight=2,
            fill=True,
            fill_color='#EF4444',
            fill_opacity=0.12,
            popup=folium.Popup(pop_cor, max_width=300),
        ).add_to(m)

by_report_id = df.set_index('id').to_dict('index') if not df.empty else {}
cluster = MarkerCluster(name='Điểm hư hỏng đã xác minh').add_to(m)

for _, r in hs.iterrows():
    worst_rec = by_report_id.get(r.worst_report_id, {})
    thumb_html = ''
    ann_rel = worst_rec.get('annotated_file')
    if ann_rel:
        cdn_url = storage.get_public_url(ann_rel)
        if cdn_url:
            thumb_html = (
                f'<div style="margin-top:6px;">'
                f'<img src="{escape(cdn_url)}" alt="Ảnh AI" style="width:100%;max-width:230px;border-radius:6px;border:1px solid #CBD5E1;">'
                f'</div>'
            )

    text = (
        f"<b>{escape(str(r.location_name))}</b><br>"
        f"Mức: <b>{escape(r.severity_label)}</b><br>"
        f"Điểm ưu tiên: {r.priority_score} (Hạng #{r.priority_rank})<br>"
        f"Số phản ánh: {r.report_count} lượt"
        f"{thumb_html}"
    )
    folium.Marker(
        [r.latitude, r.longitude],
        popup=folium.Popup(text, max_width=260),
        tooltip=f"#{r.priority_rank} · {r.location_name}",
        icon=folium.Icon(color=colors.get(r.severity_label, 'gray')),
    ).add_to(cluster)

if heat:
    HeatMap([[r.latitude, r.longitude, r.priority_score / 100] for _, r in hs.iterrows()], radius=25).add_to(m)

with st.container(border=True, key='rw_glass_map_frame'):
    components.html(m.get_root().render(), height=540, scrolling=False)
st.caption('Bản đồ công khai chỉ hiển thị các vị trí đã được cán bộ xác minh. Vùng khoanh đỏ biểu thị cụm hư hỏng liên hoàn khuyến nghị thảm lại toàn phần.')
disclaimer()
