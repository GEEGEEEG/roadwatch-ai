import streamlit as st

from core import db
from core.constants import STATUS_LABELS
from core.geo import maps_link
from core.ui import df_show, disclaimer, image_url_or_file, img_show, kpi_grid, page_intro, require_officer

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

kpi_grid([
    ('Trạng thái', STATUS_LABELS.get(r.status, r.status), 'green' if r.status == 'fixed' else ('amber' if r.status in ('pending', 'assigned') else 'blue')),
    ('Mức xác nhận', r.final_level or 'Chưa phân mức', 'red' if r.final_level == 'Cần kiểm tra sớm' else ('amber' if r.final_level == 'Trung bình' else 'green')),
    ('Điểm mức độ', r.final_score, 'amber'),
    ('Số vùng phát hiện', int(r.total_boxes), 'blue'),
], cols=4)

st.write(f"**{r.location_name}** — `{r.latitude}, {r.longitude}` (Nguồn: {r.gps_source})")
st.link_button('Chỉ đường Google Maps', maps_link(r.latitude, r.longitude))

a, b = st.columns(2)
for col, rel, cap in ((a, r.image_file, 'Ảnh gốc'), (b, r.annotated_file, 'Ảnh khoanh vùng AI')):
    p = image_url_or_file(rel, public_only=False)
    with col:
        if p:
            img_show(p, caption=cap)
        else:
            st.markdown(
                f'<div style="border:1px dashed rgba(148,163,184,0.35);border-radius:14px;'
                f'padding:36px 20px;text-align:center;color:#94A3B8;background:rgba(15,23,42,0.45);">'
                f'<b>{cap}</b><br><span style="font-size:0.85rem;">Không có ảnh hiển thị cho mục này.</span></div>',
                unsafe_allow_html=True,
            )

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

st.subheader('Nhật ký thẩm định & xử lý')
hist = db.get_history(rid)
if hist.empty:
    st.caption('Chưa có lịch sử xử lý.')
else:
    hist_disp = hist.copy()
    hist_disp['status'] = hist_disp['status'].map(lambda s: STATUS_LABELS.get(s, s))
    hist_disp['actor'] = hist_disp['actor'].map(lambda a: 'Người dân' if str(a).strip().lower() == 'citizen' else (a or 'Hệ thống'))
    hist_disp = hist_disp.rename(columns={
        'ts': 'Thời điểm',
        'status': 'Trạng thái',
        'actor': 'Thực hiện bởi',
        'note': 'Ghi chú',
    })
    df_show(hist_disp, hide_index=True)
disclaimer()
