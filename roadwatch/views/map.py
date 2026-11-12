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
    <div id="driver-box" style="font-family: sans-serif; background: #0F172A; color: #F8FAFC; padding: 18px; border-radius: 12px; border: 1px solid #334155;">
