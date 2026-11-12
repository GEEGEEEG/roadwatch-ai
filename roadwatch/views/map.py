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
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <span style="font-weight: 700; font-size: 1.05rem; display: flex; align-items: center; gap: 8px;">
          <span id="radar-icon" style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: #22C55E;"></span>
          HỆ THỐNG CẢNH BÁO VA CHẠM MẶT ĐƯỜNG
        </span>
        <button id="btn-toggle-radar" onclick="toggleRadar()" style="background: #2563EB; color: #fff; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-weight: 600;">
          ▶ Bật giám sát hành trình
        </button>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-bottom: 14px;">
        <div style="background: #1E293B; padding: 10px; border-radius: 8px;">
          <div style="font-size: 0.75rem; color: #94A3B8;">Tọa độ hiện tại</div>
          <div id="live-coords" style="font-weight: 600; font-size: 0.9rem; color: #38BDF8;">Chưa bật định vị</div>
        </div>
        <div style="background: #1E293B; padding: 10px; border-radius: 8px;">
          <div style="font-size: 0.75rem; color: #94A3B8;">Vị trí nguy hiểm gần nhất</div>
          <div id="min-dist" style="font-weight: 700; font-size: 1rem; color: #22C55E;">-- m</div>
        </div>
        <div style="background: #1E293B; padding: 10px; border-radius: 8px;">
          <div style="font-size: 0.75rem; color: #94A3B8;">Trạng thái làn đường</div>
          <div id="safety-status" style="font-weight: 700; font-size: 0.95rem; color: #22C55E;">AN TOÀN</div>
        </div>
      </div>

      <div id="alert-banner" style="display: none; background: #DC2626; color: #fff; padding: 12px; border-radius: 8px; font-weight: 700; text-align: center; animation: pulse 1s infinite;">
        ⚠️ CHÚ Ý: PHÍA TRƯỚC CÓ Ổ GÀ / VÙNG HƯ HỎNG NGUY HIỂM! GIẢM TỐC ĐỘ!
      </div>
    </div>

    <script>
      const HAZARDS = {hazards_json};
      let watchId = null;
      let lastSpokenTime = 0;

      function haversineDist(lat1, lon1, lat2, lon2) {{
        const R = 6371000;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
      }}

      function playBeep() {{
        try {{
          const ctx = new (window.AudioContext || window.webkitAudioContext)();
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = 'triangle';
          osc.frequency.setValueAtTime(880, ctx.currentTime);
          gain.gain.setValueAtTime(0.3, ctx.currentTime);
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start();
          osc.stop(ctx.currentTime + 0.2);
        }} catch(e) {{}}
      }}

      function speakAlert(text) {{
        const now = Date.now();
        if (now - lastSpokenTime < 15000) return;
        lastSpokenTime = now;
        playBeep();
        if ('speechSynthesis' in window) {{
          const u = new SpeechSynthesisUtterance(text);
          u.lang = 'vi-VN';
          u.rate = 1.05;
          window.speechSynthesis.speak(u);
        }}
      }}

      function updatePosition(pos) {{
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        document.getElementById('live-coords').innerText = lat.toFixed(5) + ', ' + lon.toFixed(5);

        let minDist = 999999;
        let nearestHazard = null;
        for (const h of HAZARDS) {{
          const d = haversineDist(lat, lon, h.lat, h.lon);
          if (d < minDist) {{
            minDist = d;
            nearestHazard = h;
          }}
        }}

        const distEl = document.getElementById('min-dist');
        const statusEl = document.getElementById('safety-status');
        const bannerEl = document.getElementById('alert-banner');
        const radarIcon = document.getElementById('radar-icon');

        if (minDist < 99999) {{
          distEl.innerText = Math.round(minDist) + ' m';
        }}

        if (minDist <= 100) {{
          distEl.style.color = '#EF4444';
          statusEl.style.color = '#EF4444';
          statusEl.innerText = 'NGUY HIỂM';
          bannerEl.style.display = 'block';
          radarIcon.style.background = '#EF4444';
          speakAlert('Cảnh báo! Phía trước cách ' + Math.round(minDist) + ' mét có ổ gà nguy hiểm, hãy giảm tốc độ!');
        }} else if (minDist <= 300) {{
          distEl.style.color = '#F59E0B';
          statusEl.style.color = '#F59E0B';
          statusEl.innerText = 'CẢNH GIÁC';
          bannerEl.style.display = 'none';
          radarIcon.style.background = '#F59E0B';
        }} else {{
          distEl.style.color = '#22C55E';
          statusEl.style.color = '#22C55E';
          statusEl.innerText = 'AN TOÀN';
          bannerEl.style.display = 'none';
          radarIcon.style.background = '#22C55E';
        }}
      }}

      function toggleRadar() {{
        const btn = document.getElementById('btn-toggle-radar');
        if (!watchId) {{
          if (navigator.geolocation) {{
            watchId = navigator.geolocation.watchPosition(updatePosition, function(err) {{
              alert('Lỗi lấy GPS: ' + err.message);
            }}, {{ enableHighAccuracy: true, maximumAge: 1000 }});
            btn.innerText = '⏹ Dừng giám sát';
            btn.style.background = '#DC2626';
            speakAlert('Hệ thống cảnh báo an toàn đường bộ đã kích hoạt.');
          }} else {{
            alert('Trình duyệt không hỗ trợ GPS Geolocation.');
          }}
        }} else {{
          navigator.geolocation.clearWatch(watchId);
          watchId = null;
          btn.innerText = '▶ Bật giám sát hành trình';
          btn.style.background = '#2563EB';
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
