import streamlit as st

from core import db
from core.config import cfg
from core.priority import build_hotspots
from core.report import build_pdf, generate_report, hotspot_record
from core.ui import disclaimer, image_file, page_intro, require_officer, weights_sidebar

require_officer(('admin', 'officer'))
page_intro('HỒ SƠ BÁO CÁO', 'Báo cáo quản lý & Phiếu hiện trường PDF', 'Tổng hợp dữ liệu đã xác minh và rà soát nội dung trước khi xuất biểu mẫu PDF/Markdown.')
weights, radius = weights_sidebar()
df = db.fetch_df()
hs = build_hotspots(df, weights, radius)
if hs.empty:
    st.info('Chưa có điểm để lập báo cáo.')
    st.stop()

hid = st.selectbox(
    'Chọn điểm nóng',
    hs.hotspot_id.tolist(),
    format_func=lambda h: f"#{hs[hs.hotspot_id == h].priority_rank.iloc[0]} {hs[hs.hotspot_id == h].location_name.iloc[0]}",
)
row = hs[hs.hotspot_id == hid].iloc[0]
rec = hotspot_record(row, df)
key = cfg('GEMINI_API_KEY')
st.caption('Gemini AI: ' + ('đã cấu hình (chỉ viết đoạn nhận xét hỗ trợ, số liệu luôn cố định từ DB)' if key else 'chưa cấu hình — dùng biểu mẫu chuẩn cố định'))
if st.button('Tạo bản thảo báo cáo', type='primary'):
    text, method = generate_report(rec, key)
    st.session_state.update(rep_text=text, rep_method=method, rep_for=hid)

if st.session_state.get('rep_for') == hid:
    st.caption('Phương pháp tạo: ' + st.session_state['rep_method'])
    edited = st.text_area('Rà soát và chỉnh sửa trước khi xuất bản', st.session_state['rep_text'], height=420)
    if st.checkbox('Tôi đã đối chiếu số liệu và phê duyệt nội dung phiếu báo cáo'):
        extra = edited.split('## 4.', 1)[1].split('\n', 1)[-1].strip() if '## 4.' in edited else ''
        c = st.columns(2)
        c[0].download_button('Tải Markdown (.md)', edited.encode('utf-8'), file_name=f"RoadWatch_{rec['id']}.md", mime='text/markdown')
        c[1].download_button(
            'Tải Phiếu PDF tiếng Việt (.pdf)',
            build_pdf(rec, image_file(rec.get('annotated_file')), extra),
            file_name=f"RoadWatch_{rec['id']}.pdf",
            mime='application/pdf',
        )
disclaimer()
