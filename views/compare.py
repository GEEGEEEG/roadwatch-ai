import io
import json
from datetime import datetime

import streamlit as st
from PIL import Image

from core import db, storage
from core.config import data_dir, now_vn
from core.damage_analysis import analyze_image_damage
from core.detector import fast_prepare_rgb
from core.priority import build_hotspots
from core.ui import (
    current_actor,
    detector_or_stop,
    disclaimer,
    image_file,
    image_url_or_file,
    img_show,
    page_intro,
    require_officer,
    weights_sidebar,
)

require_officer()
page_intro(
    'THEO DÕI KHẮC PHỤC',
    'Đối chiếu Trước và Sau sửa chữa',
    'Tải ảnh hiện trường sau khi vá/thảm lại để AI kiểm tra độc lập và đóng điểm hư hỏng.',
)
weights, radius = weights_sidebar()
df = db.fetch_df()
hs = build_hotspots(df, weights, radius)
if hs.empty:
    st.info('Chưa có điểm đang hoạt động.')
    st.stop()

det = detector_or_stop()
pick = st.selectbox(
    'Điểm cần nghiệm thu',
    hs.hotspot_id.tolist(),
    format_func=lambda h: f"#{hs[hs.hotspot_id == h].priority_rank.iloc[0]} {hs[hs.hotspot_id == h].location_name.iloc[0]}",
)
row = hs[hs.hotspot_id == pick].iloc[0]
before = df[df.id == row.worst_report_id].iloc[0]
after_file = st.file_uploader('Ảnh SAU xử lý (chụp cùng góc, cùng vị trí)', type=['jpg', 'jpeg', 'png'])
thr = st.slider('Ngưỡng tin cậy', 0.10, 0.90, 0.25, 0.05)

a, b = st.columns(2)
with a:
    p = image_url_or_file(before.annotated_file, public_only=False)
    if p:
        img_show(p, caption=f'TRƯỚC — {int(before.total_boxes)} vùng, mức {before.final_level}')
    if st.button('Quét lại AI ảnh TRƯỚC (bản mới)', key=f'rescan_before_{before.id}', use_container_width=True):
        orig_path = image_file(before.image_file) or image_file(before.annotated_file)
        if not orig_path:
            st.error('Không tìm thấy tệp ảnh gốc để quét lại.')
        else:
            with Image.open(orig_path) as raw_im:
                prep_b = fast_prepare_rgb(raw_im, max_side=1280)
            out_b = det.predict_image(prep_b, threshold=thr, tta=True, enhance_glare=True)
            dmg_b = analyze_image_damage(prep_b, out_b['detections'])

            ann_rel = before.annotated_file or f'annotated/{before.id}.jpg'
            ann_buf = io.BytesIO()
            ann_im = out_b['annotated_image'].copy()
            ann_im.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
            ann_im.convert('RGB').save(ann_buf, 'JPEG', quality=85, optimize=True)
            ann_bytes = ann_buf.getvalue()

            ann_path = data_dir() / ann_rel
            ann_path.parent.mkdir(parents=True, exist_ok=True)
            ann_path.write_bytes(ann_bytes)
            if storage.is_enabled():
                storage.upload(ann_rel, ann_bytes, 'image/jpeg')

            dets_b = out_b['detections']
            sev_b = out_b['severity']
            avg_c = round(sum(d['confidence'] for d in dets_b) / len(dets_b), 4) if dets_b else 0.0
            db.update_report(
                before.id,
                annotated_file=ann_rel,
                total_boxes=len(dets_b),
                count_D00=sev_b['counts']['D00'],
                count_D10=sev_b['counts']['D10'],
                count_D20=sev_b['counts']['D20'],
                count_D40=sev_b['counts']['D40'],
                avg_confidence=avg_c,
                bbox_union_pct=sev_b['bbox_proxy_pct'],
                damage_area_m2=dmg_b['total_damage_m2'],
                damage_volume_l=dmg_b['estimated_volume_liters'],
                damage_depth_desc=dmg_b.get('damage_severity_desc', ''),
                ai_level=sev_b['level'],
                ai_score=sev_b['score'],
                detections_json=json.dumps(dets_b, ensure_ascii=False),
            )
            st.success('Đã quét lại ảnh TRƯỚC bằng mô hình mới!')
            st.rerun()

if not after_file:
    with b:
        st.markdown(
            '<div class="rw-empty" style="min-height: 240px; display: flex; flex-direction: column; '
            'align-items: center; justify-content: center; gap: 6px;">'
            '<b>Chưa có ảnh SAU sửa chữa</b>'
            '<span>Tải ảnh mặt đường sau khi vá/thảm lại ở ô phía trên để AI kiểm tra và đối chiếu tự động.</span>'
            '</div>',
            unsafe_allow_html=True,
        )

if after_file:
    raw = after_file.getvalue()
    out = det.predict_image(Image.open(io.BytesIO(raw)), threshold=thr, tta=True, enhance_glare=True)
    with b:
        img_show(out['annotated_image'], caption=f"SAU — {len(out['detections'])} vùng, mức sơ bộ {out['severity']['level']}")
    st.metric(
        'Số vùng phát hiện còn lại',
        len(out['detections']),
        delta=len(out['detections']) - int(before.total_boxes),
        delta_color='inverse',
    )
    still = len(out['detections']) > 0
    if still:
        st.warning('Ảnh sau sửa chữa vẫn còn vùng nghi ngờ hư hỏng — cán bộ cần kiểm tra kỹ trước khi nghiệm thu.')
    ok = st.checkbox('Xác nhận hiện trường đã khắc phục đạt yêu cầu' + (' (dù mô hình còn đánh dấu)' if still else ''))
    if st.button('Nghiệm thu & Đóng điểm này (Đã xử lý)', type='primary', disabled=not ok):
        name = f'after/{row.worst_report_id}.jpg'
        buf = io.BytesIO()
        ann_after = out['annotated_image'].copy()
        ann_after.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
        ann_after.convert('RGB').save(buf, 'JPEG', quality=85, optimize=True)
        after_bytes = buf.getvalue()

        (data_dir() / name).write_bytes(after_bytes)
        if storage.is_enabled():
            storage.upload(name, after_bytes, 'image/jpeg')

        now = now_vn().strftime('%Y-%m-%d %H:%M:%S')
        actor = current_actor()
        other_ids = [rid for rid in row.member_ids if rid != row.worst_report_id]

        db.update_report(
            row.worst_report_id,
            status='fixed',
            fixed_at=now,
            after_boxes=len(out['detections']),
            after_image_file=name,
        )
        if other_ids:
            db.update_reports_bulk(other_ids, status='fixed', fixed_at=now, after_boxes=len(out['detections']))
        db.add_history_bulk([
            (rid, 'fixed', actor, f"Nghiệm thu hoàn thành (còn {len(out['detections'])} vùng AI)")
            for rid in row.member_ids
        ])
        st.success('Đã nghiệm thu & lưu ảnh sau sửa chữa lên Cloud vĩnh viễn!')
disclaimer()
