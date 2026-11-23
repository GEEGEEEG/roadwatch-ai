import streamlit as st

from core import db
from core.constants import STATUS_LABELS
from core.geo import maps_link
from core.ui import df_show, disclaimer, image_url_or_file, img_show, page_intro, require_officer

require_officer()
page_intro('HỒ SƠ VỊ TRÍ', 'Chi tiết phản ánh', 'Xem hình ảnh, tọa độ định vị và toàn bộ lịch sử luân chuyển của từng bản ghi.')
df = db.fetch_df()
if df.empty:
    st.info('Chưa có dữ liệu.')
    st.stop()

ids = df.id.tolist()
qid = st.query_params.get('id')
rid = st.selectbox('Mã bản ghi', ids, index=ids.index(qid) if qid in ids else len(ids) - 1)
r = df[df.id == rid].iloc[0]

c = st.columns(4)
c[0].metric('Trạng thái', STATUS_LABELS.get(r.status, r.status))
c[1].metric('Mức xác nhận', r.final_level)
c[2].metric('Điểm mức độ', r.final_score)
c[3].metric('Số vùng AI', int(r.total_boxes))

st.write(f"**{r.location_name}** — `{r.latitude}, {r.longitude}` (Nguồn: {r.gps_source})")
st.link_button('Chỉ đường Google Maps', maps_link(r.latitude, r.longitude))

a, b = st.columns(2)
for col, rel, cap in ((a, r.image_file, 'Ảnh gốc'), (b, r.annotated_file, 'Ảnh khoanh vùng AI')):
    p = image_url_or_file(rel, public_only=False)
    if p:
        with col:
            img_show(p, caption=cap)

if r.after_image_file:
    p = image_url_or_file(r.after_image_file, public_only=False)
    if p:
        img_show(p, caption=f'Ảnh nghiệm thu sau xử lý ({r.fixed_at}), còn {int(r.after_boxes or 0)} vùng phát hiện')

for t in filter(None, (r.quality_flags or '').split('; ')):
    st.warning('Chất lượng ảnh: ' + t)
for t in filter(None, (r.screen_flags or '').split('; ')):
    st.warning('Cờ kiểm tra: ' + t)

near = df[(df.latitude.sub(r.latitude).abs() < 0.0005) & (df.longitude.sub(r.longitude).abs() < 0.0005)]
if len(near) > 1:
    st.subheader('Diễn tiến điểm số theo thời gian (các báo cáo lân cận ~50 m)')
    trend = near.sort_values('created_at').set_index('created_at')[['final_score']]
    st.line_chart(trend)

st.subheader('Nhật ký thẩm định & xử lý (Audit Log)')
df_show(db.get_history(rid), hide_index=True)
disclaimer()
