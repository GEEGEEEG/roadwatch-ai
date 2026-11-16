from html import escape
import json

import folium
import streamlit as st
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium

from core import db, storage
from core.constants import LEVELS
from core.corridor_hotspot import analyze_corridor_clusters
from core.priority import DEFAULT_WEIGHTS, build_hotspots
from core.ui import add_legal_map_layers, disclaimer, is_officer, page_intro, weights_sidebar

page_intro(
    'BẢN ĐỒ GIS CÔNG KHAI',
    'Bản đồ điểm hư hỏng & hành lang xuống cấp',
    'Hiển thị các vị trí đã được cán bộ xác minh, vùng cảnh báo xuống cấp diện rộng và chế độ hỗ trợ lái xe an toàn.',
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
        f"🚨 **CẢNH BÁO QUY HOẠCH TUYẾN:** **{top_c['location_summary']}** xuất hiện cụm **{top_c['cluster_size']} điểm hư hỏng liên hoàn** "
        f"(trải dài ~{top_c['span_length_m']} m). **{top_c['proposal']}** · Dự toán: ~{top_c['formatted_cost']}."
    )

with st.expander('🚗 Chế độ Lái xe An toàn (Cảnh báo giọng nói & âm thanh thời gian thực)', expanded=False):
    st.caption('Bật định vị trên điện thoại khi di chuyển. Khi tiến gần điểm hư hỏng nghiêm trọng trong phạm vi 100m, hệ thống tự động phát âm báo và giọng nói tiếng Việt.')
    hazard_pts = [
        {
            'lat': float(r['latitude']),
            'lon': float(r['longitude']),
            'name': str(r['location_name']),
            'score': float(r['priority_score']),
        }
        for _, r in hs.iterrows()
        if r['severity_label'] == 'Cần kiểm tra sớm' or r.get('has_pothole')
    ]
    hazards_json = json.dumps(hazard_pts, ensure_ascii=False)

    import streamlit.components.v1 as components
    driver_html = f"""
    <div id="driver-box" style="font-family: sans-serif; background: #0F172A; color: #F8FAFC; padding: 18px; border-radius: 12px; border: 1px solid #334155;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <span style="font-weight: 700; font-size: 1.05rem; display: flex; align-items: center; gap: 8px;">
          <span id="radar-icon" style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: #22C55E;"></span>
          RADAR CẢNH BÁO MẶT ĐƯỜNG ({len(hazard_pts)} điểm chú ý)
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
          <div style="font-size: 0.75rem; color: #94A3B8;">Điểm nguy hiểm gần nhất</div>
          <div id="min-dist" style="font-weight: 700; font-size: 1rem; color: #22C55E;">-- m</div>
        </div>
        <div style="background: #1E293B; padding: 10px; border-radius: 8px;">
          <div style="font-size: 0.75rem; color: #94A3B8;">Trạng thái làn đường</div>
          <div id="safety-status" style="font-weight: 700; font-size: 0.95rem; color: #22C55E;">AN TOÀN</div>
        </div>
      </div>
      <div id="alert-banner" style="display: none; background: #DC2626; color: #fff; padding: 12px; border-radius: 8px; font-weight: 700; text-align: center;">
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
          osc.connect(gain); gain.connect(ctx.destination);
          osc.start(); osc.stop(ctx.currentTime + 0.2);
        }} catch(e) {{}}
      }}
      function speakAlert(text) {{
        const now = Date.now();
        if (now - lastSpokenTime < 15000) return;
        lastSpokenTime = now;
        playBeep();
        if ('speechSynthesis' in window) {{
          const u = new SpeechSynthesisUtterance(text);
          u.lang = 'vi-VN'; u.rate = 1.05;
          window.speechSynthesis.speak(u);
        }}
      }}
      function updatePosition(pos) {{
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        document.getElementById('live-coords').innerText = lat.toFixed(5) + ', ' + lon.toFixed(5);
        let minDist = 999999;
        for (const h of HAZARDS) {{
          const d = haversineDist(lat, lon, h.lat, h.lon);
          if (d < minDist) minDist = d;
        }}
        const distEl = document.getElementById('min-dist');
        const statusEl = document.getElementById('safety-status');
        const bannerEl = document.getElementById('alert-banner');
        const radarIcon = document.getElementById('radar-icon');
        if (minDist < 99999) distEl.innerText = Math.round(minDist) + ' m';
        if (minDist <= 100) {{
          distEl.style.color = '#EF4444'; statusEl.style.color = '#EF4444';
          statusEl.innerText = 'NGUY HIỂM'; bannerEl.style.display = 'block'; radarIcon.style.background = '#EF4444';
          speakAlert('Cảnh báo! Phía trước cách ' + Math.round(minDist) + ' mét có ổ gà nguy hiểm, hãy giảm tốc độ!');
        }} else if (minDist <= 300) {{
          distEl.style.color = '#F59E0B'; statusEl.style.color = '#F59E0B';
          statusEl.innerText = 'CẢNH GIÁC'; bannerEl.style.display = 'none'; radarIcon.style.background = '#F59E0B';
        }} else {{
          distEl.style.color = '#22C55E'; statusEl.style.color = '#22C55E';
          statusEl.innerText = 'AN TOÀN'; bannerEl.style.display = 'none'; radarIcon.style.background = '#22C55E';
        }}
      }}
      function toggleRadar() {{
        const btn = document.getElementById('btn-toggle-radar');
        if (!watchId) {{
          if (navigator.geolocation) {{
            watchId = navigator.geolocation.watchPosition(updatePosition, function(err) {{
              alert('Lỗi lấy GPS: ' + err.message);
            }}, {{ enableHighAccuracy: true, maximumAge: 1000 }});
            btn.innerText = '⏹ Dừng giám sát'; btn.style.background = '#DC2626';
            speakAlert('Hệ thống cảnh báo an toàn đường bộ đã kích hoạt.');
          }} else alert('Trình duyệt không hỗ trợ GPS Geolocation.');
        }} else {{
          navigator.geolocation.clearWatch(watchId); watchId = null;
          btn.innerText = '▶ Bật giám sát hành trình'; btn.style.background = '#2563EB';
          document.getElementById('safety-status').innerText = 'TẠM DỪNG';
        }}
      }}
    </script>
    """
    components.html(driver_html, height=210)

col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
levels = col_f1.multiselect('Lọc theo mức độ', LEVELS, default=LEVELS)
heat = col_f2.checkbox('Hiện bản đồ nhiệt (Heatmap)')
show_corridors = col_f3.checkbox('Hiện hành lang xuống cấp', value=True)

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
            f"<b>🚨 Hành lang xuống cấp diện rộng</b><br>"
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
                tooltip=f"🚨 Cụm xuống cấp ({cor['cluster_size']} điểm)",
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

st_folium(m, height=540, returned_objects=[], width=None)
st.caption('Bản đồ công khai chỉ hiển thị các vị trí đã được cán bộ xác minh. Vùng khoanh đỏ biểu thị cụm hư hỏng liên hoàn khuyến nghị thảm lại toàn phần.')
disclaimer()
