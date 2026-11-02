import streamlit as st

from core import db
from core.constants import STATUS_LABELS
from core.ui import disclaimer, df_show

st.title('🛣️ RoadWatch AI — Giám sát & ưu tiên kiểm tra mặt đường')
st.write('Người dân/cán bộ gửi ảnh → mô hình YOLO nhận diện D00/D10/D20/D40 → **cán bộ xác minh** → '
         'gom điểm nóng và xếp hạng ưu tiên → lộ trình kiểm tra → ảnh trước/sau sửa chữa.')
df = db.fetch_df()
c = st.columns(5)
for col, (key, label) in zip(c, STATUS_LABELS.items()):
    col.metric(label, int((df.status == key).sum()) if not df.empty else 0)
with st.expander('Quyền riêng tư & đồng ý dữ liệu'):
    st.write('Khi gửi báo cáo, ảnh và vị trí của bạn được lưu để cán bộ xác minh. Liên hệ (nếu nhập) chỉ cán bộ xem được. '
             'Bản đồ công khai chỉ hiển thị điểm đã được xác minh, không kèm ảnh. Không chụp rõ người/biển số xe.')
disclaimer()
