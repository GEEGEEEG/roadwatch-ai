from core.ui import page_intro
import streamlit as st

from core import db
from core.config import cfg
from core.priority import build_hotspots
from core.report import build_pdf, generate_report, hotspot_record
from core.ui import disclaimer, image_file, require_officer, weights_sidebar

require_officer()
page_intro('HỒ SƠ BÁO CÁO','Báo cáo quản lý','Tổng hợp dữ liệu đã xác minh và rà soát nội dung trước khi tải xuống.')
weights, radius = weights_sidebar()
df = db.fetch_df()
hs = build_hotspots(df, weights, radius)
if hs.empty:
    st.info('Chưa có điểm để lập báo cáo.')
    st.stop()
hid = st.selectbox('Chọn điểm', hs.hotspot_id.tolist(),
                   format_func=lambda h: f"#{hs[hs.hotspot_id == h].priority_rank.iloc[0]} {hs[hs.hotspot_id == h].location_name.iloc[0]}")
row = hs[hs.hotspot_id == hid].iloc[0]
rec = hotspot_record(row, df)
key = cfg('GEMINI_API_KEY')
st.caption('Gemini: ' + ('đã cấu hình (chỉ viết đoạn diễn giải, số liệu luôn từ bảng)' if key else 'chưa cấu hình — dùng mẫu cố định'))
if st.button('Tạo báo cáo'):
    text, method = generate_report(rec, key)
    st.session_state.update(rep_text=text, rep_method=method, rep_for=hid)
if st.session_state.get('rep_for') == hid:
    st.caption('Phương pháp: ' + st.session_state['rep_method'])
    edited = st.text_area('Rà soát và chỉnh sửa trước khi tải', st.session_state['rep_text'], height=420)
    if st.checkbox('Đã đối chiếu số liệu và duyệt bản báo cáo'):
        extra = edited.split('## 4.', 1)[1].split('\n', 1)[-1].strip() if '## 4.' in edited else ''
        c = st.columns(2)
        c[0].download_button('Tải .md', edited.encode('utf-8'), file_name=f"RoadWatch_{rec['id']}.md", mime='text/markdown')
        c[1].download_button('Tải .pdf', build_pdf(rec, image_file(rec.get('annotated_file')), extra),
                             file_name=f"RoadWatch_{rec['id']}.pdf", mime='application/pdf')
disclaimer()
