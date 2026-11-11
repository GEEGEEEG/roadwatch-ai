from core.ui import page_intro
import folium
import streamlit as st
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium

from core import db
from core.constants import ACTIVE_STATUSES, LEVELS
from core.priority import build_hotspots
from core.ui import disclaimer, is_officer, weights_sidebar
from html import escape

page_intro('BẢN ĐỒ CÔNG KHAI', 'Bản đồ điểm hư hỏng', 'Chỉ hiển thị vị trí đã được xác minh. Có thể lọc theo mức độ để xem khu vực cần quan tâm.')
weights, radius = weights_sidebar()
df = db.fetch_df()
hs = build_hotspots(df, weights, radius)
if hs.empty:
    st.info('Chưa có điểm nào được xác minh.')
    st.stop()

levels = st.multiselect('Lọc theo mức độ', LEVELS, default=LEVELS)
heat = st.checkbox('Hiện bản đồ nhiệt (heatmap)')
hs = hs[hs.severity_label.isin(levels)]
if hs.empty:
    st.info('Không có điểm khớp bộ lọc.')
    st.stop()

colors = {'Cần kiểm tra sớm': 'red', 'Trung bình': 'orange', 'Nhẹ': 'green', 'Không phát hiện': 'blue'}
m = folium.Map(location=[hs.latitude.mean(), hs.longitude.mean()], zoom_start=13, tiles=None)

# Lớp Google Maps Vệ tinh kết hợp đường sá (Hybrid)
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google Maps Vệ tinh',
    name='Google Vệ tinh (Hybrid)',
    overlay=False,
    control=True,
).add_to(m)

# Lớp Google Maps Đường sá
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    attr='Google Maps',
    name='Google Bản đồ đường',
    overlay=False,
    control=True,
).add_to(m)

# Lớp OpenStreetMap
folium.TileLayer(
    tiles='OpenStreetMap',
    name='OpenStreetMap',
    overlay=False,
    control=True,
).add_to(m)

folium.LayerControl().add_to(m)

cluster = MarkerCluster().add_to(m)
for _, r in hs.iterrows():
    text = (f"{escape(str(r.location_name))}<br>Mức: {escape(r.severity_label)}<br>Ưu tiên: {r.priority_score} "
            f"(hạng {r.priority_rank})<br>Số báo cáo: {r.report_count}")
    folium.Marker([r.latitude, r.longitude], popup=folium.Popup(text, max_width=280),
                  icon=folium.Icon(color=colors.get(r.severity_label, 'gray'))).add_to(cluster)
if heat:
    HeatMap([[r.latitude, r.longitude, r.priority_score / 100] for _, r in hs.iterrows()], radius=25).add_to(m)
st_folium(m, height=520, returned_objects=[], width=None)
st.caption('Điểm là tọa độ từ EXIF/GPS hoặc do người nhập và đã được cán bộ xác minh; màu theo mức độ.')
disclaimer()
