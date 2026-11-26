from datetime import datetime
from html import escape

import pandas as pd
import streamlit as st

from core import db
from core.config import now_vn
from core.constants import ACTIVE_STATUSES, DUP_FLAG_M, LEVELS, MERGE_MAX_M, ROAD_TYPES
from core.cost_estimation import estimate_maintenance_cost
from core.geo import nearby_points
from core.notify import alert_text, send_telegram, telegram_configured
from core.priority import final_score
from core.ui import current_actor, disclaimer, image_url_or_file, img_show, page_intro, require_officer

require_officer(('admin', 'officer'))
page_intro(
    'QUẢN LÝ PHẢN ÁNH',
    'Hàng chờ xác minh',
    'Xem ảnh, đối chiếu tọa độ và điều chỉnh thông tin trước khi phê duyệt công khai.',
)
pending = db.fetch_df(['pending'])
if pending.empty:
    st.success('Tuyệt vời! Hiện không có báo cáo nào đang chờ duyệt.')
    st.stop()

# Cảnh báo SLA nếu có hồ sơ khẩn cấp tồn đọng quá 48 giờ
created_ts = pd.to_datetime(pending['created_at'], errors='coerce')
age_hours = (pd.Timestamp(now_vn()) - created_ts).dt.total_seconds() / 3600.0
overdue_urgent = int(((pending['ai_level'] == 'Cần kiểm tra sớm') & (age_hours > 48)).sum())
if overdue_urgent > 0:
    st.error(f'**Cảnh báo SLA:** Có **{overdue_urgent}** hồ sơ mức "Cần kiểm tra sớm" đã chờ quá 48 giờ cần ưu tiên thẩm định ngay!')

col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)
n_urgent = sum(1 for x in pending.itertuples() if getattr(x, 'ai_level', '') == 'Cần kiểm tra sớm')
n_med = sum(1 for x in pending.itertuples() if getattr(x, 'ai_level', '') == 'Trung bình')
n_low = sum(1 for x in pending.itertuples() if getattr(x, 'ai_level', '') == 'Nhẹ')
n_none = sum(1 for x in pending.itertuples() if getattr(x, 'ai_level', '') == 'Không phát hiện')
col_kpi1.metric('Tổng hồ sơ chờ', len(pending))
col_kpi2.metric('Khẩn cấp', n_urgent)
col_kpi3.metric('Trung bình', n_med)
col_kpi4.metric('Mức độ nhẹ', n_low)
col_kpi5.metric('Không phát hiện', n_none)

active = db.fetch_df(list(ACTIVE_STATUSES))
labels = {
    r.id: f"{r.id} — {r.location_name} ({r.ai_level})"
    + (' · Có cờ kiểm tra' if r.screen_flags or r.quality_flags else '')
    + (' · Nghi trùng điểm' if nearby_points(active, r.latitude, r.longitude, DUP_FLAG_M) else '')
    for r in pending.itertuples()
}
rid = st.selectbox('Chọn hồ sơ cần thẩm định', list(labels), format_func=labels.get)
r = pending[pending.id == rid].iloc[0]

_ai_lvl = str(getattr(r, 'ai_level', '') or 'Chưa phân mức')
_pill_cls = 'rw-badge-danger' if _ai_lvl == 'Cần kiểm tra sớm' else ('rw-badge-warning' if _ai_lvl == 'Trung bình' else 'rw-badge-success')
_border_hex = '#EF4444' if _ai_lvl == 'Cần kiểm tra sớm' else ('#F59E0B' if _ai_lvl == 'Trung bình' else '#10B981')
st.markdown(
    f'<div class="rw-case-banner" style="border-left-color: {_border_hex};">'
    f'<div><div class="rw-case-title">{escape(str(r.id))} · {escape(str(r.location_name))}</div>'
    f'<div class="rw-case-meta">{r.latitude}, {r.longitude} ({escape(str(r.gps_source))}) · {escape(str(r.created_at))}</div></div>'
    f'<span class="rw-badge-pill {_pill_cls}">AI đề xuất: {escape(_ai_lvl)} · {r.ai_score}/100</span>'
    f'</div>',
    unsafe_allow_html=True,
)

left, right = st.columns(2)
with left:
    p = image_url_or_file(r.image_file, public_only=False)
    if p:
        img_show(p, caption='Ảnh gốc')
with right:
    p = image_url_or_file(r.annotated_file, public_only=False)
    if p:
        img_show(p, caption='Ảnh có đánh dấu AI')

custom_prices = db.get_setting('unit_prices')
raw_dmg_m2 = float(getattr(r, 'damage_area_m2', 0.0) or 0.0)
raw_dmg_vol = float(getattr(r, 'damage_volume_l', 0.0) or 0.0)
dmg_m2 = raw_dmg_m2 if raw_dmg_m2 > 0 else 0.15
dmg_vol = raw_dmg_vol if raw_dmg_vol > 0 else (5.0 if int(getattr(r, 'count_D40', 0) or 0) > 0 else 0.0)
cost_est = estimate_maintenance_cost(dmg_m2, dmg_vol, custom_prices=custom_prices)

c = st.columns(5)
c[0].metric('Số vùng', int(r.total_boxes))
c[1].metric('Mức sơ bộ', r.ai_level)
c[2].metric('Điểm quy tắc', r.ai_score)
c[3].metric('Diện tích AI', f'{raw_dmg_m2:.2f} m²' if raw_dmg_m2 > 0 else f'~{dmg_m2:.2f} m²')
c[4].metric('Dự toán sửa chữa', cost_est['formatted_total'])
cls_parts = [
    f"{code}: {int(getattr(r, f'count_{code}', 0) or 0)}"
    for code in ('D00', 'D10', 'D20', 'D40')
    if int(getattr(r, f'count_{code}', 0) or 0) > 0
]
cls_line = f" · **Phân loại AI:** {', '.join(cls_parts)} (độ tin cậy TB {float(getattr(r, 'avg_confidence', 0) or 0) * 100:.0f}%)" if cls_parts else ''
st.caption(f"**Vật tư dự trù:** {cost_est['material_detail']}{cls_line}")

for text in filter(None, (r.quality_flags or '').split('; ')):
    st.warning('Chất lượng ảnh: ' + text)
for text in filter(None, (r.screen_flags or '').split('; ')):
    st.warning('Cờ kiểm tra: ' + text)
st.caption(
    f"Tọa độ: {r.latitude}, {r.longitude} | Nguồn ảnh: {getattr(r, 'capture_method', None) or 'chưa ghi nhận'} "
    f"| Nguồn GPS: {r.gps_source} | Thời điểm gửi: {r.created_at}"
)

actor = current_actor()
cands = nearby_points(active, r.latitude, r.longitude, MERGE_MAX_M)
if cands:
    near_id, near_m, _ = cands[0]
    if near_m <= DUP_FLAG_M:
        st.warning(f'Có thể trùng điểm với hồ sơ {near_id} (cách {near_m:.0f} m).')
    with st.container(border=True, key='rw_glass_queue_merge'):
        st.markdown('**Gộp vào điểm hiện hữu** — không tạo ghim mới, cộng lượt phản ánh vào điểm gốc.')
        pick = st.selectbox(
            'Điểm gốc',
            [c_item[0] for c_item in cands],
            key=f'merge_{rid}',
            format_func=lambda i: next(f'{x[0]} — {x[2]} (cách {x[1]:.0f} m)' for x in cands if x[0] == i),
        )
        if st.button('Gộp vào điểm hiện hữu', key=f'mergebtn_{rid}'):
            dist = next(x[1] for x in cands if x[0] == pick)
            parent_status = active.loc[active.id == pick, 'status'].iloc[0]
            now_s = now_vn().strftime('%Y-%m-%d %H:%M:%S')
            db.update_report(rid, status='merged', merged_into=pick, reviewed_by=actor, reviewed_at=now_s)
            db.add_history(rid, 'merged', actor, f'Gộp vào {pick} (cách {dist:.0f} m)')
            db.add_history(pick, parent_status, actor, f'Nhận gộp phản ánh {rid}')
            st.success(f'Đã gộp {rid} vào {pick}. Tần suất của điểm gốc tăng thêm 1.')
            st.rerun()

with st.form('review'):
    loc = st.text_input('Tên tuyến / điểm', value=r.location_name)
    road = st.selectbox('Cấp tuyến', list(ROAD_TYPES), index=list(ROAD_TYPES).index(r.road_type) if r.road_type in ROAD_TYPES else 2)
    level = st.selectbox('Mức độ sau khi xem ảnh', LEVELS, index=LEVELS.index(r.ai_level) if r.ai_level in LEVELS else 0)
    note = st.text_area('Ghi chú', value=r.note or '')
    reason = st.text_input('Lý do (nếu từ chối)')
    ok = st.checkbox('Tôi đã xem lại ảnh và xác nhận đây chỉ là đánh giá sơ bộ')
    a, b = st.columns(2)
    approve = a.form_submit_button('Duyệt', type='primary')
    reject = b.form_submit_button('Từ chối')

if approve:
    if not ok or not loc.strip():
        st.error('Cần tên vị trí và đánh dấu đã xem lại ảnh.')
    else:
        fs = final_score(r.ai_level, r.ai_score, level)
        db.update_report(
            rid,
            location_name=loc.strip(),
            road_type=road,
            road_score=ROAD_TYPES[road],
            final_level=level,
            final_score=fs,
            note=note,
            status='verified',
            reviewed_by=actor,
            reviewed_at=now_vn().strftime('%Y-%m-%d %H:%M:%S'),
        )
        db.add_history(rid, 'verified', actor, f'Mức {level}')
        st.success('Đã duyệt.')
        if level == 'Cần kiểm tra sớm' and telegram_configured():
            sent = send_telegram(alert_text({**r.to_dict(), 'location_name': loc, 'final_score': fs}))
            st.info('Đã gửi thông báo Telegram.' if sent else 'Không gửi được thông báo Telegram.')
        st.rerun()
if reject:
    if not reason.strip():
        st.error('Hãy ghi lý do từ chối.')
    else:
        db.update_report(
            rid,
            status='rejected',
            reject_reason=reason.strip(),
            reviewed_by=actor,
            reviewed_at=now_vn().strftime('%Y-%m-%d %H:%M:%S'),
        )
        db.add_history(rid, 'rejected', actor, reason.strip())
        st.success('Đã từ chối.')
        st.rerun()
disclaimer()
