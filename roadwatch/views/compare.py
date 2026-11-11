from core.ui import page_intro
import io
from datetime import datetime

import streamlit as st
from PIL import Image

from core import db
from core.config import data_dir
from core.priority import build_hotspots
from core.ui import detector_or_stop, disclaimer, image_file, img_show, require_officer, weights_sidebar

require_officer()
page_intro('THEO DÕI KHẮC PHỤC','Trước và sau sửa chữa','Đối chiếu ảnh trước/sau và cập nhật trạng thái xử lý.')
weights, radius = weights_sidebar()
df = db.fetch_df()
hs = build_hotspots(df, weights, radius)
if hs.empty:
    st.info('Chưa có điểm đang hoạt động.')
    st.stop()
det = detector_or_stop()
pick = st.selectbox('Điểm', hs.hotspot_id.tolist(),
                    format_func=lambda h: f"#{hs[hs.hotspot_id == h].priority_rank.iloc[0]} {hs[hs.hotspot_id == h].location_name.iloc[0]}")
row = hs[hs.hotspot_id == pick].iloc[0]
before = df[df.id == row.worst_report_id].iloc[0]
after_file = st.file_uploader('Ảnh SAU xử lý (chụp cùng góc, cùng vị trí)', type=['jpg', 'jpeg', 'png'])
thr = st.slider('Ngưỡng tin cậy', 0.10, 0.90, 0.25, 0.05)

a, b = st.columns(2)
with a:
    p = image_file(before.annotated_file)
    if p:
        img_show(p, caption=f'TRƯỚC — {int(before.total_boxes)} vùng, mức {before.final_level}')
if after_file:
    raw = after_file.getvalue()
    out = det.predict_image(Image.open(io.BytesIO(raw)), threshold=thr)
    with b:
        img_show(out['annotated_image'], caption=f"SAU — {len(out['detections'])} vùng, mức sơ bộ {out['severity']['level']}")
    st.metric('Số vùng phát hiện', len(out['detections']), delta=len(out['detections']) - int(before.total_boxes), delta_color='inverse')
    still = len(out['detections']) > 0
    if still:
        st.warning('Ảnh sau vẫn còn vùng phát hiện — cần cán bộ xem lại trước khi đóng.')
    ok = st.checkbox('Cán bộ xác nhận đã xử lý xong' + (' (dù mô hình vẫn phát hiện)' if still else ''))
    if st.button('Đóng điểm này (đã xử lý)', disabled=not ok):
        name = f"after/{row.worst_report_id}.jpg"
        out['annotated_image'].save(data_dir() / name, quality=90)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for rid in row.member_ids:
            db.update_report(rid, status='fixed', fixed_at=now, after_boxes=len(out['detections']),
                             after_image_file=name if rid == row.worst_report_id else None)
            db.add_history(rid, 'fixed', 'cán bộ', f"Sau xử lý còn {len(out['detections'])} vùng")
        st.success('Đã chuyển sang "Đã xử lý"; điểm không còn trong xếp hạng.')
disclaimer()
