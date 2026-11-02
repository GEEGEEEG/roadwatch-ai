import streamlit as st

from core import db
from core.config import cfg
from core.constants import LEVELS, ROAD_TYPES
from core.notify import alert_text, send_telegram, telegram_configured
from core.priority import final_score
from core.ui import disclaimer, df_show, image_file, img_show, require_officer
from datetime import datetime

require_officer()
st.header('✅ Hàng chờ xác minh')
pending = db.fetch_df(['pending'])
if pending.empty:
    st.success('Không có báo cáo nào đang chờ.')
    st.stop()
st.write(f'**{len(pending)}** báo cáo đang chờ.')
labels = {r.id: f"{r.id} — {r.location_name} ({r.ai_level})" + (' ⚠️' if r.screen_flags or r.quality_flags else '')
          for r in pending.itertuples()}
rid = st.selectbox('Chọn báo cáo', list(labels), format_func=labels.get)
r = pending[pending.id == rid].iloc[0]

left, right = st.columns(2)
with left:
    p = image_file(r.image_file)
    if p:
        img_show(p, caption='Ảnh gốc')
with right:
    p = image_file(r.annotated_file)
    if p:
        img_show(p, caption='Ảnh có đánh dấu')
c = st.columns(4)
c[0].metric('Số vùng', int(r.total_boxes))
c[1].metric('Mức sơ bộ', r.ai_level)
c[2].metric('Điểm quy tắc', r.ai_score)
c[3].metric('Nguồn tọa độ', r.gps_source)
for text in filter(None, (r.quality_flags or '').split('; ')):
    st.warning('Chất lượng ảnh: ' + text)
for text in filter(None, (r.screen_flags or '').split('; ')):
    st.warning('Cờ kiểm tra: ' + text)
st.caption(f"Tọa độ: {r.latitude}, {r.longitude} | Người gửi: {r.source} | Liên hệ: {r.contact or '—'}")

with st.form('review'):
    loc = st.text_input('Tên tuyến / điểm', value=r.location_name)
    road = st.selectbox('Cấp tuyến', list(ROAD_TYPES), index=list(ROAD_TYPES).index(r.road_type) if r.road_type in ROAD_TYPES else 2)
    level = st.selectbox('Mức độ sau khi xem ảnh', LEVELS, index=LEVELS.index(r.ai_level))
    note = st.text_area('Ghi chú', value=r.note or '')
    reason = st.text_input('Lý do (nếu từ chối)')
    ok = st.checkbox('Tôi đã xem lại ảnh và xác nhận đây chỉ là đánh giá sơ bộ')
    a, b = st.columns(2)
    approve = a.form_submit_button('✅ Duyệt')
    reject = b.form_submit_button('❌ Từ chối')

if approve:
    if not ok or not loc.strip():
        st.error('Cần tên vị trí và đánh dấu đã xem lại ảnh.')
    else:
        fs = final_score(r.ai_level, r.ai_score, level)
        db.update_report(rid, location_name=loc.strip(), road_type=road, road_score=ROAD_TYPES[road], final_level=level,
                         final_score=fs, note=note, status='verified', reviewed_by='cán bộ',
                         reviewed_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        db.add_history(rid, 'verified', 'cán bộ', f'Mức {level}')
        st.success('Đã duyệt.')
        if level == 'Cần kiểm tra sớm' and telegram_configured():
            sent = send_telegram(alert_text({**r.to_dict(), 'location_name': loc, 'final_score': fs}))
            st.info('Đã gửi thông báo Telegram.' if sent else 'Không gửi được thông báo Telegram.')
        st.rerun()
if reject:
    if not reason.strip():
        st.error('Hãy ghi lý do từ chối.')
    else:
        db.update_report(rid, status='rejected', reject_reason=reason.strip(), reviewed_by='cán bộ',
                         reviewed_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        db.add_history(rid, 'rejected', 'cán bộ', reason.strip())
        st.success('Đã từ chối.')
        st.rerun()
disclaimer()
