import streamlit as st

from core import db
from core.constants import STATUS_LABELS
from core.ui import disclaimer

st.markdown(
    '<div class="rw-hero"><span class="rw-pill">AI hỗ trợ · Cán bộ xác minh</span>'
    '<h1>Báo hư hỏng mặt đường<br>chỉ với một bức ảnh</h1>'
    '<p>AI khoanh vùng nứt và ổ gà, cán bộ xác minh, rồi ưu tiên điểm cần kiểm tra trước.</p>'
    '<div class="rw-chips"><span>🔍 Nhận diện 4 loại hư hỏng</span><span>✅ Có người duyệt</span>'
    '<span>📍 Gắn vị trí GPS</span></div></div>', unsafe_allow_html=True)

a, b = st.columns(2)
try:
    a.page_link('views/submit.py', label='Gửi báo cáo ngay', icon='📷')
    b.page_link('views/map.py', label='Xem bản đồ điểm hư hỏng', icon='🗺️')
except Exception:  # chạy trang riêng lẻ (không qua app.py)
    pass

st.markdown(
    '<div class="rw-steps">'
    '<div class="rw-step"><span class="rw-ico">📸</span><b>1. Chụp hoặc tải ảnh</b><span>Chụp rõ mặt đường, tránh lấy rõ người hay biển số xe.</span></div>'
    '<div class="rw-step"><span class="rw-ico">🤖</span><b>2. AI nhận diện</b><span>Khoanh vùng nứt, ổ gà và gợi ý mức độ sơ bộ.</span></div>'
    '<div class="rw-step"><span class="rw-ico">🧑‍🔧</span><b>3. Cán bộ xác minh</b><span>Chỉ điểm đã duyệt mới lên bản đồ và xếp hạng.</span></div>'
    '</div>', unsafe_allow_html=True)

df = db.fetch_df()
st.subheader('Tiến độ tiếp nhận')
colors = ['#F59E0B', '#16A34A', '#DC2626', '#2563EB', '#0D9488']
cards = ''.join(
    f'<div class="rw-stat" style="--c:{colors[i % 5]}"><small>{label}</small>'
    f'<strong>{int((df.status == key).sum()) if not df.empty else 0}</strong></div>'
    for i, (key, label) in enumerate(STATUS_LABELS.items()))
st.markdown(f'<div class="rw-stats">{cards}</div>', unsafe_allow_html=True)
if df.empty:
    st.markdown('<div class="rw-empty">Chưa có báo cáo nào. Hãy là người đầu tiên gửi ảnh hư hỏng mặt đường.</div>',
                unsafe_allow_html=True)

with st.expander('Quyền riêng tư & đồng ý dữ liệu'):
    st.write('Khi gửi báo cáo, ảnh và vị trí của bạn được lưu để cán bộ xác minh. Liên hệ (nếu nhập) chỉ cán bộ xem được. '
             'Bản đồ công khai chỉ hiển thị điểm đã được xác minh, không kèm ảnh. Không chụp rõ người/biển số xe.')
disclaimer()
