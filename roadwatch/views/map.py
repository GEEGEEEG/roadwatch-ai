from core.ui import page_intro
import folium
import streamlit as st
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium
from html import escape
import json
from core import db
from core.constants import ACTIVE_STATUSES, LEVELS
from core.corridor_hotspot import analyze_corridor_clusters
from core.priority import build_hotspots
from core.ui import disclaimer, is_officer, page_intro, weights_sidebar
page_intro('BẢN ĐỒ CÔNG KHAI', 'Bản đồ điểm hư hỏng', 'Chỉ hiển thị vị trí đã được xác minh. Có thể lọc theo mức độ để xem khu vực cần quan tâm.')
weights, radius = weights_sidebar()
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
# Phân tích cảnh báo hành lang xuống cấp diện rộng (Pavement Hotspots)
corridors = analyze_corridor_clusters(df, max_distance_m=250.0, min_cluster_size=3)
wide_degradations = [c for c in corridors if c['is_wide_degradation']]
if wide_degradations:
    top_c = wide_degradations[0]
    st.error(f"🚨 **CẢNH BÁO QUY HOẠCH:** Tuyến **{top_c['location_summary']}** có cụm {top_c['cluster_size']} điểm hư hỏng liên hoàn (chiều dài ~{top_c['span_length_m']} m). "
             f"**{top_c['proposal']}** · Dự toán: ~{top_c['formatted_cost']}.")
# Chế độ Lái xe An toàn (Driver Alert Mode)
with st.expander('🚗 Chế độ Lái xe An toàn (Cảnh báo giọng nói & âm thanh theo thời gian thực)', expanded=False):
    st.caption('Bật định vị trên điện thoại. Khi phương tiện tiến gần điểm hư hỏng nguy hiểm trong bán kính 100m, hệ thống tự động phát âm thanh và giọng nói cảnh báo.')
    # Lấy danh sách các điểm nguy hiểm (Cần kiểm tra sớm hoặc có ổ gà)
    hazard_pts = []
    for _, r in hs.iterrows():
        if r['severity_label'] == 'Cần kiểm tra sớm' or r.get('has_pothole'):
            hazard_pts.append({
                'lat': float(r['latitude']),
                'lon': float(r['longitude']),
                'name': str(r['location_name']),
                'score': float(r['priority_score']),
            })
    hazards_json = json.dumps(hazard_pts, ensure_ascii=False)
    import streamlit.components.v1 as components
    driver_html = f"""
              document.getElementById('safety-status').innerText = 'TẠM DỪNG';
        }}
      }}
    </script>
    """
    components.html(driver_html, height=210)
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
    <div id="driver-box" style="font-family: sans-serif; background: #0F172A; color: #F8FAFC; padding: 18px; border-radius: 12px; border: 1px solid #334155;">
