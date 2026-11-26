"""Cổng tra cứu tiến độ xử lý phản ánh công khai cho người dân (Citizen Tracking Portal)."""
import streamlit as st

from core import db
from core.constants import STATUS_LABELS
from core.geo import maps_link
from core.ui import df_show, disclaimer, image_url_or_file, img_show, page_intro, steps

page_intro(
    'TRA CỨU TIẾN ĐỘ',
    'Theo dõi hồ sơ phản ánh mặt đường',
    'Nhập mã hồ sơ (ví dụ: RW-20261114...) hoặc quét mã QR sau khi gửi phản ánh để xem trạng thái xử lý.',
)

prefill_id = str(
    st.query_params.get('id')
    or st.session_state.get('_track_id')
    or st.session_state.get('_last_submitted_id')
    or ''
).strip()

with st.form('track_lookup_form'):
    col_in, col_btn = st.columns([3, 1])
    code = col_in.text_input(
        'Mã hồ sơ phản ánh',
        value=prefill_id,
        placeholder='Ví dụ: RW-20261114213000-a1b2',
        label_visibility='collapsed',
    )
    submitted = col_btn.form_submit_button('Tra cứu ngay', type='primary', use_container_width=True)

if submitted:
    st.session_state['_track_id'] = code.strip()
target_id = (code.strip() if submitted else prefill_id).strip()
if not target_id:
    st.markdown(
        '<div class="rw-empty"><b>Nhập mã hồ sơ để bắt đầu tra cứu.</b><br>'
        'Mã hồ sơ có dạng <code>RW-YYYYMMDDHHMMSS-xxxx</code> được cấp ngay sau khi bạn gửi phản ánh thành công.</div>',
        unsafe_allow_html=True,
    )
    disclaimer()
    st.stop()

rec = db.get_report(target_id)
if not rec:
    st.error(f'Không tìm thấy hồ sơ mang mã **{target_id}**. Vui lòng kiểm tra lại chính xác từng ký tự.')
    disclaimer()
    st.stop()

status = rec.get('status') or 'pending'
parent_id = rec.get('merged_into')

# Xác định bước tiến độ trên thanh Stepper 4 nấc
step_map = {'pending': 0, 'merged': 1, 'verified': 1, 'assigned': 2, 'fixed': 3, 'rejected': 1}
steps(
    '1. Đã tiếp nhận',
    '2. Đã thẩm định',
    '3. Đã giao duy tu',
    '4. Hoàn thành sửa chữa',
    active=step_map.get(status, 0),
)

if status == 'rejected':
    st.warning(
        f"Hồ sơ **{rec['id']}** không đủ điều kiện đưa vào danh sách duy tu. "
        f"Lý do: **{rec.get('reject_reason') or 'Ảnh chưa rõ hoặc không thuộc phạm vi mặt đường'}**."
    )
elif status == 'merged' and parent_id:
    st.info(
        f"Hồ sơ **{rec['id']}** đã được gộp vào điểm phản ánh hiện hữu **{parent_id}** để tăng mức độ ưu tiên xử lý."
    )
elif status == 'fixed':
    st.success(f"Điểm hư hỏng thuộc hồ sơ **{rec['id']}** đã được sửa chữa và nghiệm thu hoàn tất vào `{rec.get('fixed_at')}`!")
elif status == 'assigned':
    st.info(
        f"Phản ánh **{rec['id']}** đã được giao cho **{rec.get('assigned_to') or 'Đội duy tu chuyên trách'}** "
        f"(Hạn kiểm tra dự kiến: {str(rec.get('due_date') or 'Đang cập nhật').strip()})."
    )
elif status == 'verified':
    st.success(f"Hồ sơ **{rec['id']}** đã được cán bộ xác minh và đưa vào bảng xếp hạng ưu tiên kiểm tra.")
else:
    st.info(f"Hồ sơ **{rec['id']}** đang nằm trong hàng chờ để cán bộ chuyên môn rà soát hình ảnh và tọa độ.")

m1, m2, m3, m4 = st.columns(4)
m1.metric('Trạng thái hiện tại', STATUS_LABELS.get(status, status))
m2.metric('Mức độ đánh giá', rec.get('final_level') or rec.get('ai_level') or '—')
m3.metric('Số vùng phát hiện AI', int(rec.get('total_boxes') or 0))
dmg = float(rec.get('damage_area_m2') or 0.0)
m4.metric('Diện tích ước tính', f'{dmg:.2f} m²' if dmg > 0 else '—')

st.markdown(f"**Vị trí ghi nhận:** {rec.get('location_name')} (`{rec.get('latitude')}, {rec.get('longitude')}`) · Thời gian gửi: `{rec.get('created_at')}`")
if rec.get('latitude') is not None and rec.get('longitude') is not None:
    st.link_button('Xem vị trí trên Google Maps', maps_link(rec['latitude'], rec['longitude']))

# Chỉ hiển thị hình ảnh công khai sau khi hồ sơ đã được cán bộ xác minh (bảo vệ quyền riêng tư ảnh chưa duyệt)
if status in ('verified', 'assigned', 'fixed'):
    st.subheader('Hình ảnh hiện trường đã xác minh')
    col_before, col_after = st.columns(2)
    with col_before:
        ann_src = image_url_or_file(rec.get('annotated_file'), public_only=True)
        if ann_src:
            img_show(ann_src, caption='Ảnh phân tích hư hỏng ban đầu')
    with col_after:
        if rec.get('after_image_file'):
            after_src = image_url_or_file(rec.get('after_image_file'), public_only=True)
            if after_src:
                img_show(after_src, caption=f"Ảnh nghiệm thu sau sửa chữa ({rec.get('fixed_at')})")
        elif status != 'fixed':
            st.caption('Ảnh sau sửa chữa sẽ được cập nhật tại đây ngay khi đội duy tu nghiệm thu hiện trường.')

hist = db.get_history(rec['id'])
if not hist.empty:
    st.subheader('Nhật ký xử lý hồ sơ')
    pub_hist = hist.copy()
    pub_hist['status'] = pub_hist['status'].map(lambda s: STATUS_LABELS.get(s, s))
    pub_hist['actor'] = pub_hist['actor'].map(
        lambda a: 'Người gửi' if str(a) in ('citizen', '') else 'Cán bộ chuyên trách'
    )
    pub_hist.columns = ['Thời điểm', 'Trạng thái', 'Thực hiện bởi', 'Ghi chú']
    df_show(pub_hist, hide_index=True)

disclaimer()
