"""Landing page: một thông điệp, CTA rõ ràng, số liệu lấy từ DB thật."""
import streamlit as st
from core import db
from core.constants import STATUS_LABELS
from core.ui import disclaimer, is_officer

st.markdown("""
<section class="rw-hero" aria-labelledby="roadwatch-title">
  <div class="rw-hero-grid">
    <div>
      <span class="rw-kicker">RoadWatch AI · Giám sát hạ tầng đường bộ</span>
      <h1 id="roadwatch-title">Mỗi phản ánh nhỏ.<br>Một tuyến đường an toàn hơn.</h1>
      <p class="rw-lead">Chụp ảnh mặt đường, đánh dấu đúng vị trí. AI hỗ trợ phát hiện ổ gà, vết nứt; cán bộ xác minh trước khi đưa vào danh sách ưu tiên kiểm tra.</p>
    </div>
    <div class="rw-hero-visual" role="img" aria-label="Minh họa quy trình phản ánh hư hỏng mặt đường đến bản đồ và xác minh">
      <div class="rw-visual-head"><span><span class="rw-visual-dot"></span>Quy trình phản ánh</span><span>ROADWATCH</span></div>
      <div class="rw-visual-road"><span class="rw-road-line"></span><span class="rw-road-pin"></span></div>
      <div class="rw-visual-flow"><span>01 · Chụp ảnh</span><span>02 · AI phân tích</span><span>03 · Xác minh</span></div>
    </div>
  </div>
</section>
""", unsafe_allow_html=True)

st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
a,b = st.columns([1,1],gap='medium')
with a:
    st.page_link('views/submit.py',label='📷  Chụp và gửi phản ánh',icon=None)
with b:
    st.page_link('views/map.py',label='🗺️  Khám phá bản đồ đã xác minh',icon=None)
if is_officer():
    st.page_link('views/queue.py', label='✅  Mở hàng chờ cần xác minh')

st.markdown("""
<section class="rw-section"><span class="rw-overline">Quy trình đơn giản</span>
<h2>Ba bước để một phản ánh có giá trị</h2>
<p>Giao diện dành cho người dân được tối giản. Các thao tác chuyên môn được chuyển sang cổng cán bộ.</p></section>
<div class="rw-cards">
  <article class="rw-card"><span class="rw-card-icon" aria-hidden="true">📸</span>
  <h3>01 · Ghi nhận hiện trường</h3><p>Mở camera trên điện thoại, chụp mặt đường khi đang đứng ở vị trí an toàn.</p></article>
  <article class="rw-card"><span class="rw-card-icon" aria-hidden="true">📍</span>
  <h3>02 · Xác nhận vị trí</h3><p>Cho phép GPS hoặc chọn vị trí trên bản đồ, rà soát trước khi gửi.</p></article>
  <article class="rw-card"><span class="rw-card-icon" aria-hidden="true">🛡️</span>
  <h3>03 · Được kiểm tra, xác minh</h3><p>AI khoanh vùng hư hỏng; cán bộ xem xét trước khi công khai thông tin.</p></article>
</div>
""",unsafe_allow_html=True)

df=db.fetch_df()
counts={key:int((df.status==key).sum()) if not df.empty else 0 for key in STATUS_LABELS}
verified = counts.get('verified',0)+counts.get('assigned',0)
pending = counts.get('pending',0)
all_count = len(df)
fixed = counts.get('fixed',0)

st.markdown('<section class="rw-section"><span class="rw-overline">Tình hình tiếp nhận</span><h2>Thông tin minh bạch, cập nhật theo dữ liệu</h2><p>Số liệu dưới đây được lấy từ các bản ghi hiện có, không phải số liệu minh họa.</p></section>', unsafe_allow_html=True)
st.markdown(f"""<div class="rw-overview">
<div class="rw-kpi"><small>Phản ánh tiếp nhận</small><strong>{all_count}</strong><em>Tất cả trạng thái</em></div>
<div class="rw-kpi"><small>Đang chờ xác minh</small><strong>{pending}</strong><em>Cần cán bộ rà soát</em></div>
<div class="rw-kpi"><small>Đã xác minh / giao việc</small><strong>{verified}</strong><em>Đủ điều kiện theo dõi</em></div>
<div class="rw-kpi"><small>Đã xử lý</small><strong>{fixed}</strong><em>Đã cập nhật hoàn tất</em></div>
</div>""",unsafe_allow_html=True)

st.markdown("""
<section class="rw-section"><span class="rw-overline">Hai cổng sử dụng</span><h2>Đúng thông tin, đúng người, đúng quy trình</h2></section>
<div class="rw-two-col">
 <div class="rw-white-panel"><span class="rw-panel-title">Dành cho cộng đồng</span>
  <h3>Gửi phản ánh tại hiện trường</h3>
  <p>Chỉ chụp qua camera web, xác nhận vị trí và đồng ý lưu dữ liệu. Phản ánh được đưa vào hàng chờ xác minh.</p></div>
 <div class="rw-white-panel"><span class="rw-panel-title">Dành cho cán bộ</span>
  <h3>Rà soát và tổ chức kiểm tra</h3>
  <p>Kiểm tra ảnh, xác minh địa điểm, xem bản đồ, xếp hạng ưu tiên và xuất báo cáo theo quyền được cấp.</p></div>
</div>
<div class="rw-footnote">RoadWatch AI là sản phẩm nghiên cứu ứng dụng. Các điểm số chỉ hỗ trợ sàng lọc; không thay thế việc khảo sát và quyết định bảo trì của cơ quan có thẩm quyền. Không chụp ảnh khi đang điều khiển phương tiện.</div>
""",unsafe_allow_html=True)
with st.expander('Quyền riêng tư & dữ liệu phản ánh'):
    st.write('Ảnh và vị trí được lưu để rà soát. Bản đồ công khai chỉ hiển thị vị trí đã được xác minh. Tránh chụp rõ khuôn mặt và biển số xe; chỉ gửi phản ánh khi bạn có quyền cung cấp hình ảnh.')
disclaimer()
