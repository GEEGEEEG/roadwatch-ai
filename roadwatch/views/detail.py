import streamlit as st

from core import db
from core.geo import maps_link
from core.ui import df_show, disclaimer, image_file, img_show, require_officer

require_officer()
st.header('🔎 Chi tiết điểm')
df = db.fetch_df()
if df.empty:
    st.info('Chưa có dữ liệu.')
    st.stop()
ids = df.id.tolist()
qid = st.query_params.get('id')
rid = st.selectbox('Mã bản ghi', ids, index=ids.index(qid) if qid in ids else len(ids) - 1)
r = df[df.id == rid].iloc[0]

c = st.columns(4)
c[0].metric('Trạng thái', r.status)
c[1].metric('Mức xác nhận', r.final_level)
c[2].metric('Điểm mức độ', r.final_score)
c[3].metric('Số vùng', int(r.total_boxes))
st.write(f"**{r.location_name}** — {r.latitude}, {r.longitude} ({r.gps_source})")
st.link_button('Chỉ đường', maps_link(r.latitude, r.longitude))
a, b = st.columns(2)
for col, rel, cap in ((a, r.image_file, 'Ảnh gốc'), (b, r.annotated_file, 'Ảnh có đánh dấu')):
    p = image_file(rel)
    if p:
        with col:
            img_show(p, caption=cap)
if r.after_image_file:
    p = image_file(r.after_image_file)
    if p:
        img_show(p, caption=f'Ảnh sau xử lý ({r.fixed_at}), còn {int(r.after_boxes or 0)} vùng phát hiện')
for t in filter(None, (r.quality_flags or '').split('; ')):
    st.warning('Chất lượng ảnh: ' + t)
for t in filter(None, (r.screen_flags or '').split('; ')):
    st.warning('Cờ kiểm tra: ' + t)

near = df[(df.latitude.sub(r.latitude).abs() < 0.0005) & (df.longitude.sub(r.longitude).abs() < 0.0005)]
if len(near) > 1:
    st.subheader('Diễn tiến theo thời gian (các báo cáo lân cận ~50 m)')
    trend = near.sort_values('created_at').set_index('created_at')[['final_score']]
    st.line_chart(trend)
st.subheader('Lịch sử trạng thái')
df_show(db.get_history(rid))
disclaimer()
