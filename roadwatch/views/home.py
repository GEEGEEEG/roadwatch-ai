import streamlit as st

from core import db
from core.constants import STATUS_LABELS
from core.ui import disclaimer, is_officer

st.markdown(
    '<div class="rw-hero"><h1>RoadWatch AI</h1>'
    '<p>Báo hư hỏng mặt đường chỉ với một bức ảnh. AI khoanh vùng, cán bộ xác minh '
    'và ưu tiên điểm cần kiểm tra trước.</p></div>', unsafe_allow_html=True)

a, b = st.columns(2)
try:
    a.page_link('views/submit.py', label='Gửi báo cáo ngay', icon='📷')
    b.page_link('views/map.py', label='Xem bản đồ điểm hư hỏng', icon='🗺️')
except Exception:  # chạy trang riêng lẻ (không qua app.py)
    pass

st.markdown(
    '<div class="rw-steps">'
    '<div class="rw-step"><span class="rw-num">1</span><b>Chụp hoặc tải ảnh</b><span>Chụp rõ mặt đường, không lấy rõ người hay biển số.</span></div>'
    '<div class="rw-step"><span class="rw-num">2</span><b>AI nhận diện</b><span>Khoanh vùng nứt, ổ gà và gợi ý mức độ sơ bộ.</span></div>'
    '<div class="rw-step"><span class="rw-num">3</span><b>Cán bộ xác minh</b><span>Chỉ điểm đã duyệt mới lên bản đồ và xếp hạng.</span></div>'
    '</div>', unsafe_allow_html=True)

df = db.fetch_df()
st.subheader('Tiến độ tiếp nhận')
cols = st.columns(len(STATUS_LABELS))
for col, (key, label) in zip(cols, STATUS_LABELS.items()):
    col.metric(label, int((df.status == key).sum()) if not df.empty else 0)

with st.expander('Quyền riêng tư & đồng ý dữ liệu'):
    st.write('Khi gửi báo cáo, ảnh và vị trí của bạn được lưu để cán bộ xác minh. Liên hệ (nếu nhập) chỉ cán bộ xem được. '
             'Bản đồ công khai chỉ hiển thị điểm đã được xác minh, không kèm ảnh. Không chụp rõ người/biển số xe.')
disclaimer()
