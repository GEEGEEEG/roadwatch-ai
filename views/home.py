"""Landing page: thông điệp rõ ràng, CTA một chạm, số liệu cập nhật trực tiếp từ Supabase/DB."""
import streamlit as st
from core import db
from core.constants import STATUS_LABELS
from core.ui import disclaimer, is_officer, safe_page_link

st.markdown("""
<section class="rw-hero" aria-labelledby="roadwatch-title">
  <div class="rw-hero-grid">
    <div>
      <span class="rw-kicker">RoadWatch AI v5.0 · Giám sát hạ tầng đường bộ thông minh</span>
      <h1 id="roadwatch-title">Mỗi phản ánh nhỏ.<br>Một tuyến đường an toàn hơn.</h1>
      <p class="rw-lead">Chụp ảnh mặt đường, định vị GPS chuẩn xác. AI tự động khoanh vùng ổ gà, vết nứt & ước lượng diện tích; cán bộ xác minh và xếp hạng ưu tiên duy tu theo mô hình AHP.</p>
    </div>
    <div class="rw-hero-visual" role="img" aria-label="Minh họa quy trình phản ánh hư hỏng mặt đường đến bản đồ và xác minh">
      <div class="rw-visual-head"><span><span class="rw-visual-dot"></span>Quy trình khép kín</span><span>ROADWATCH v5</span></div>
      <div class="rw-visual-road"><span class="rw-road-line"></span><span class="rw-road-pin"></span></div>
      <div class="rw-visual-flow"><span>01 · Chụp ảnh</span><span>02 · AI phân tích</span><span>03 · Duy tu</span></div>
    </div>
  </div>
</section>
""", unsafe_allow_html=True)

st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
if is_officer():
    c1, c2, c3, c4 = st.columns(4, gap='small')
    with c1:
        safe_page_link('views/submit.py', label='📷  Chụp & gửi phản ánh', icon=None)
    with c2:
        safe_page_link('views/queue.py', label='✅  Hàng chờ thẩm định', icon=None)
    with c3:
        safe_page_link('views/priority.py', label='📊  Xếp hạng AHP & Dự toán', icon=None)
    with c4:
        safe_page_link('views/map.py', label='🗺️  Bản đồ GIS công khai', icon=None)
else:
    a, b, c = st.columns(3, gap='medium')
    with a:
        safe_page_link('views/submit.py', label='📷  Chụp và gửi phản ánh', icon=None)
    with b:
        safe_page_link('views/track.py', label='🔍  Tra cứu mã hồ sơ RW-...', icon=None)
    with c:
        safe_page_link('views/map.py', label='🗺️  Bản đồ điểm đã xác minh', icon=None)

st.markdown("""
<section class="rw-section"><span class="rw-overline">Quy trình minh bạch</span>
<h2>Ba bước để một phản ánh đi vào kế hoạch duy tu</h2>
<p>Người dân gửi nhanh trong 30 giây và nhận mã theo dõi tiến độ. Mọi quyết định kỹ thuật do cán bộ chuyên môn thẩm định.</p></section>
<div class="rw-cards">
  <article class="rw-card"><span class="rw-card-icon" aria-hidden="true">📸</span>
  <h3>01 · Ghi nhận hiện trường</h3><p>Chụp trực tiếp hoặc tải ảnh mặt đường khi đứng ở vị trí an toàn; nhận ngay mã hồ sơ tra cứu.</p></article>
  <article class="rw-card"><span class="rw-card-icon" aria-hidden="true">📍</span>
  <h3>02 · Định vị & Khử trùng lặp</h3><p>Tự động lấy GPS/EXIF, quy đổi địa chỉ đường phố và đối chiếu AI thị giác chống trùng báo cáo.</p></article>
  <article class="rw-card"><span class="rw-card-icon" aria-hidden="true">🛡️</span>
  <h3>03 · Xếp hạng AHP & Nghiệm thu</h3><p>Cán bộ xác minh, xếp hạng ưu tiên đa tiêu chí, giao đội duy tu và cập nhật ảnh trước/sau sửa chữa.</p></article>
</div>
""", unsafe_allow_html=True)

df = db.fetch_df()
counts = {key: int((df.status == key).sum()) if not df.empty else 0 for key in STATUS_LABELS}
verified = counts.get('verified', 0) + counts.get('assigned', 0)
pending = counts.get('pending', 0)
all_count = len(df)
fixed = counts.get('fixed', 0)

st.markdown(
    '<section class="rw-section"><span class="rw-overline">Tình hình tiếp nhận thời gian thực</span>'
    '<h2>Số liệu minh bạch từ cơ sở dữ liệu hệ thống</h2>'
    '<p>Thống kê trực tiếp từ các hồ sơ hiện có trên hệ thống lưu trữ trung tâm.</p></section>',
    unsafe_allow_html=True,
)
st.markdown(f"""<div class="rw-overview">
<div class="rw-kpi"><small>📥 Phản ánh tiếp nhận</small><strong>{all_count}</strong><em>Tất cả trạng thái</em></div>
<div class="rw-kpi"><small>⏳ Đang chờ xác minh</small><strong>{pending}</strong><em>Trong hàng chờ cán bộ</em></div>
<div class="rw-kpi"><small>✅ Đã xác minh / Đang xử lý</small><strong>{verified}</strong><em>Đưa vào bản đồ & kế hoạch</em></div>
<div class="rw-kpi"><small>🛠️ Đã sửa chữa hoàn thành</small><strong>{fixed}</strong><em>Đã đối chiếu ảnh sau xử lý</em></div>
</div>""", unsafe_allow_html=True)

st.markdown("""
<section class="rw-section"><span class="rw-overline">Hai cổng chuyên biệt</span><h2>Đúng thông tin, đúng vai trò, đúng quy trình</h2></section>
<div class="rw-two-col">
 <div class="rw-white-panel"><span class="rw-panel-title">Dành cho cộng đồng</span>
  <h3>Gửi phản ánh & Tra cứu tiến độ</h3>
  <p>Gửi ảnh kèm vị trí GPS, nhận mã hồ sơ <code>RW-...</code> để theo dõi minh bạch từ lúc chờ duyệt đến khi sửa chữa xong.</p></div>
 <div class="rw-white-panel"><span class="rw-panel-title">Dành cho cơ quan quản lý</span>
  <h3>Thẩm định, Quy hoạch Hành lang & Dự toán</h3>
  <p>Phân quyền 3 cấp (Admin / Thẩm định / Đội duy tu), gom cụm tuyến xuống cấp, chấm điểm AHP chuẩn Saaty và xuất phiếu PDF.</p></div>
</div>
<div class="rw-footnote">RoadWatch AI hỗ trợ sàng lọc kỹ thuật và lập kế hoạch duy tu đường bộ. Không sử dụng điện thoại khi đang điều khiển phương tiện giao thông.</div>
""", unsafe_allow_html=True)
with st.expander('Quyền riêng tư & nguyên tắc công khai dữ liệu'):
    st.write(
        'Ảnh chờ duyệt không công khai trên bản đồ chung để bảo đảm tính xác thực và quyền riêng tư. '
        'Vui lòng chỉ chụp mặt đường, hạn chế chụp cận cảnh khuôn mặt hoặc biển số phương tiện cá nhân.'
    )
disclaimer()
