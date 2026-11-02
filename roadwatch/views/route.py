from datetime import date, timedelta

import streamlit as st

from core import db
from core.config import cfg
from core.geo import maps_link, maps_multi_link, nearest_neighbor_route
from core.priority import build_hotspots
from core.ui import df_show, disclaimer, qr_png, require_officer, weights_sidebar

require_officer()
st.header('🚗 Lộ trình kiểm tra & giao việc')
weights, radius = weights_sidebar()
df = db.fetch_df()
hs = build_hotspots(df, weights, radius)
if hs.empty:
    st.info('Chưa có điểm đã xác minh.')
    st.stop()

top_n = st.slider('Số điểm ưu tiên cao nhất đưa vào lộ trình', 1, min(15, len(hs)), min(5, len(hs)))
c1, c2 = st.columns(2)
s_lat, s_lon = c1.text_input('Vĩ độ xuất phát (tùy chọn)'), c2.text_input('Kinh độ xuất phát (tùy chọn)')
start = None
try:
    start = (float(s_lat), float(s_lon)) if s_lat and s_lon else None
except ValueError:
    st.warning('Tọa độ xuất phát không hợp lệ; bỏ qua.')

sel = hs.head(top_n)
route = nearest_neighbor_route([(int(r.hotspot_id), r.latitude, r.longitude) for r in sel.itertuples()], start)
by_id = {int(r.hotspot_id): r for r in sel.itertuples()}
rows = []
for order, (hid, lat, lon, leg) in enumerate(route, 1):
    r = by_id[hid]
    rows.append({'thứ tự': order, 'điểm': r.location_name, 'hạng ưu tiên': r.priority_rank, 'mức': r.severity_label,
                 'cách điểm trước (m)': leg, 'chỉ đường': maps_link(lat, lon), 'hotspot_id': hid})
import pandas as pd
table = pd.DataFrame(rows)
st.dataframe(table.drop(columns='hotspot_id'), hide_index=True,
             column_config={'chỉ đường': st.column_config.LinkColumn('chỉ đường', display_text='Mở Google Maps')})
st.link_button('Mở toàn bộ lộ trình trong Google Maps', maps_multi_link([(a, b) for _, a, b, _ in route], start))
st.caption('Thứ tự theo láng giềng gần nhất (đường chim bay) — chỉ là gợi ý, không tối ưu theo mạng lưới đường.')
st.download_button('Tải phiếu giao việc (.csv)', table.drop(columns='hotspot_id').to_csv(index=False).encode('utf-8-sig'),
                   file_name='RoadWatch_lo_trinh.csv', mime='text/csv')

with st.expander('Mã QR cho từng điểm'):
    base_url = cfg('ROADWATCH_BASE_URL').rstrip('/')
    st.caption('Có ROADWATCH_BASE_URL → QR mở trang Chi tiết điểm; chưa đặt → QR mở chỉ đường Google Maps.')
    cols = st.columns(3)
    for i, (hid, lat, lon, _) in enumerate(route):
        r = by_id[hid]
        target = f'{base_url}/detail?id={r.worst_report_id}' if base_url else maps_link(lat, lon)
        with cols[i % 3]:
            st.image(qr_png(target), caption=f'{i + 1}. {r.location_name}', width=160)

st.subheader('Giao kiểm tra')
with st.form('assign'):
    pick = st.multiselect('Chọn điểm', list(by_id), format_func=lambda h: by_id[h].location_name)
    who = st.text_input('Người/đội phụ trách')
    due = st.date_input('Hạn kiểm tra', value=date.today() + timedelta(days=3))
    go = st.form_submit_button('Giao việc')
if go:
    if not pick or not who.strip():
        st.error('Chọn ít nhất một điểm và nhập người phụ trách.')
    else:
        for h in pick:
            for rid in by_id[h].member_ids:
                db.update_report(rid, status='assigned', assigned_to=who.strip(), due_date=str(due))
                db.add_history(rid, 'assigned', 'cán bộ', f'Giao {who.strip()} hạn {due}')
        st.success(f'Đã giao {len(pick)} điểm.')
disclaimer()
