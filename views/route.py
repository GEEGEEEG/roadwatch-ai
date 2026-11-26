from datetime import date, timedelta

import pandas as pd
import streamlit as st

from core import db
from core.config import cfg, today_vn
from core.geo import maps_link, maps_multi_link, nearest_neighbor_route
from core.notify import send_telegram, telegram_configured
from core.priority import build_hotspots
from core.ui import (
    current_actor,
    df_show,
    disclaimer,
    page_intro,
    qr_png,
    require_officer,
    safe_csv_export,
    weights_sidebar,
)

require_officer()
page_intro(
    'ĐIỀU PHỐI HIỆN TRƯỜNG',
    'Lộ trình & giao việc',
    'Tối ưu thứ tự kiểm tra hiện trường, theo dõi hạn xử lý SLA và xuất phiếu giao việc.',
)
weights, radius = weights_sidebar()
df = db.fetch_df()
hs = build_hotspots(df, weights, radius)
if hs.empty:
    st.info('Chưa có điểm đã xác minh.')
    st.stop()

# Kiểm tra các nhiệm vụ đã giao bị quá hạn SLA
assigned_df = df[df.status == 'assigned'].copy()
if not assigned_df.empty and 'due_date' in assigned_df.columns:
    due_dates = pd.to_datetime(assigned_df['due_date'], errors='coerce').dt.date
    overdue_df = assigned_df[due_dates < today_vn()]
    if not overdue_df.empty:
        st.error(f'**Cảnh báo quá hạn SLA:** Có **{len(overdue_df)}** hồ sơ đã giao kiểm tra vượt quá hạn hoàn thành!')
        with st.expander('Xem danh sách hồ sơ quá hạn & nhắc việc'):
            df_show(overdue_df[['id', 'location_name', 'assigned_to', 'due_date', 'final_level']], hide_index=True)
            if telegram_configured() and st.button('Gửi nhắc việc SLA qua Telegram'):
                msg = (
                    f'[RoadWatch SLA] Có {len(overdue_df)} hồ sơ duy tu quá hạn xử lý:\n'
                    + '\n'.join(f"- {r.id}: {r.location_name} (Phụ trách: {r.assigned_to}, Hạn: {r.due_date})" for r in overdue_df.head(8).itertuples())
                )
                st.success('Đã gửi nhắc việc Telegram!') if send_telegram(msg) else st.error('Gửi Telegram thất bại.')

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
    rows.append({
        'Thứ tự': order,
        'Điểm hư hỏng': r.location_name,
        'Hạng ưu tiên': r.priority_rank,
        'Mức độ': r.severity_label,
        'Cách điểm trước (m)': leg,
        'Chỉ đường': maps_link(lat, lon),
        'hotspot_id': hid,
    })

table = pd.DataFrame(rows)
df_show(
    table.drop(columns='hotspot_id'),
    hide_index=True,
    column_config={'Chỉ đường': st.column_config.LinkColumn('Chỉ đường', display_text='Mở Google Maps')},
)
st.link_button('Mở toàn bộ lộ trình trong Google Maps', maps_multi_link([(a, b) for _, a, b, _ in route], start))
st.caption('Thứ tự gợi ý theo thuật toán láng giềng gần nhất (Nearest Neighbor).')
st.download_button(
    'Tải phiếu giao việc (.csv)',
    safe_csv_export(table.drop(columns='hotspot_id')),
    file_name='RoadWatch_lo_trinh.csv',
    mime='text/csv',
)

with st.expander('Mã QR cho từng điểm hiện trường'):
    base_url = cfg('ROADWATCH_BASE_URL').rstrip('/')
    st.caption('Có ROADWATCH_BASE_URL → QR mở trang Chi tiết điểm; chưa đặt → QR mở chỉ đường Google Maps.')
    cols = st.columns(3)
    for i, (hid, lat, lon, _) in enumerate(route):
        r = by_id[hid]
        target = f'{base_url}/detail?id={r.worst_report_id}' if base_url else maps_link(lat, lon)
        with cols[i % 3]:
            st.image(qr_png(target), caption=f'{i + 1}. {r.location_name}', width=160)

st.subheader('Giao nhiệm vụ kiểm tra / duy tu')
with st.form('assign'):
    pick = st.multiselect('Chọn điểm', list(by_id), format_func=lambda h: by_id[h].location_name)
    who = st.text_input('Người / Đội phụ trách', placeholder='Ví dụ: Đội Duy tu Đường bộ 1')
    due = st.date_input('Hạn hoàn thành kiểm tra', value=today_vn() + timedelta(days=3))
    go = st.form_submit_button('Giao việc', type='primary')

if go:
    if not pick or not who.strip():
        st.error('Chọn ít nhất một điểm và nhập người phụ trách.')
    else:
        actor = current_actor()
        all_member_ids = [rid for h in pick for rid in by_id[h].member_ids]
        db.update_reports_bulk(all_member_ids, status='assigned', assigned_to=who.strip(), due_date=str(due))
        db.add_history_bulk([(rid, 'assigned', actor, f'Giao {who.strip()} hạn {due}') for rid in all_member_ids])
        st.success(f'Đã giao {len(pick)} điểm ({len(all_member_ids)} hồ sơ) cho **{who.strip()}**!')
disclaimer()
