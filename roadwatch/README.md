# RoadWatch AI — Giao diện Professional v4

**Bản này được chỉnh trực tiếp từ `roadwatch-ai-main.zip` do nhóm cung cấp**, giữ logic YOLO D00/D10/D20/D40, bản đồ, hàng chờ duyệt, ưu tiên 50/30/20, báo cáo, video, quản trị.

## 1. Bắt đầu deploy (không cần Colab)

1. Giải nén gói ZIP; mở thư mục chứa trực tiếp `app.py`, `requirements.txt`, `core/`, `views/`, `.streamlit/`, `models/`.
2. Tạo repository GitHub mới (Private khi chưa kiểm tra giấy phép của checkpoint); tải **nội dung thư mục**, không tải nguyên ZIP. Trong bản này có `models/model.pt` từ file nhóm gửi; kiểm tra giấy phép checkpoint trước khi đưa vào repo công khai.
3. Mở [Streamlit Community Cloud](https://share.streamlit.io/) → **Create app** → **Yup, I have an app**.
4. Chọn repo, branch `main`, **Main file path:** `app.py`. Chọn Python 3.11 hoặc 3.12.
5. Trong **Advanced settings → Secrets** nhập mật khẩu quản trị mạnh:

   ```toml
   ROADWATCH_OFFICER_PASSWORD = "THAY_BANG_MAT_KHAU_DU_MẠNH"
   ```

6. Nhấn **Deploy**. Community Cloud cài `requirements.txt` và apt từ `packages.txt`. Truy cập website qua HTTPS (`*.streamlit.app`).
7. Trên điện thoại: vào **Gửi phản ánh** → cấp quyền **Camera** → chụp → cấp quyền vị trí/nhập tọa độ → đồng ý lưu → gửi.
8. Trên máy tính: **Cổng cán bộ** → nhập mật khẩu → **Hàng chờ xác minh** → kiểm tra ảnh/địa điểm → duyệt → kiểm tra bản đồ, xếp hạng, báo cáo.

## 2. Bố cục mã nguồn và vai trò

| File / Thư mục | Vai trò |
| --- | --- |
| `app.py` | Entrypoint, cấu hình trang và navigation theo quyền. |
| `core/theme.py` | Toàn bộ design system, font, responsive, component styles. |
| `core/ui.py` | Header trang, khối điều hướng chung, nhận diện quyền cán bộ. |
| `views/home.py` | Landing page thông điệp chính, CTA, quy trình, thống kê số liệu thật. |
| `views/submit.py` | Luồng gửi ảnh: công dân camera-only, cán bộ upload/camera, GPS, bản đồ, gửi. |
| `views/map.py` | Bản đồ các vị trí đã xác minh (OpenStreetMap/Folium). |
| `views/queue.py` | Cán bộ duyệt/từ chối phản ánh và ghi lịch sử. |
| `views/priority.py` | Điểm nóng và bảng xếp hạng nhiều tiêu chí. |
| `views/route.py` | Lộ trình kiểm tra và giao việc. |
| `views/detail.py` / `compare.py` | Chi tiết vị trí và ảnh trước–sau sửa chữa. |
| `views/reports.py` | Báo cáo theo mẫu/Gemini tùy chọn và xuất PDF/Markdown. |
| `views/video.py` / `evaluation.py` | Khảo sát video và đánh giá mô hình. |
| `views/login.py` / `admin.py` | Đăng nhập bằng mật khẩu chung và quản trị/sao lưu. |
| `core/detector.py` / `service.py` | Mô hình nhận diện, quy tắc mức độ, sàng lọc và lưu phản ánh. |
| `core/db.py` / `gdrive.py` | SQLite và tùy chọn sao lưu lên Google Drive. |
| `requirements.txt` / `packages.txt` | Các thư viện Python / gói hệ thống khi deploy. |
| `models/model.pt` | Checkpoint do nhóm cung cấp, không cần Colab để inference web. |

## 3. Chỗ thay đổi về UI/UX và hiệu năng

- Trang chủ: H1 lớn và **CTA ở màn hình đầu tiên**, minh họa quy trình ngay trên hero, KPI lấy từ dữ liệu, không chế số.
- Người dân: chỉ camera; không tải ảnh từ máy. Cán bộ: lựa chọn upload khảo sát hoặc chụp tại chỗ.
- Chia rõ 3 bước: ảnh → vị trí → xác nhận. Không mở sẵn bản đồ nặng; chỉ tải Folium khi người dùng bật.
- YOLO được giữ trong cache và chỉ nạp khi thực sự gửi ảnh. Khung ảnh kết quả lưu JPEG chất lượng 83, kích thước tối đa 2000px.
- CSS responsive desktop/tablet/mobile, font Be Vietnam Pro và fallback Segoe UI; heading, màu sắc, khoảng cách và nút thống nhất.
- Thêm escape cho dữ liệu tên cán bộ khi xuất thành HTML; bộ khôi phục ZIP giới hạn kích thước và chặn đường dẫn vượt thư mục/symlink.
- Loại lớp tile Google Maps không chính thức trong app, thay bằng OpenStreetMap.

## 4. Phạm vi thực tế

- **Bảo mật production:** Streamlit Cloud có HTTPS nhưng mẫu này vẫn sử dụng mật khẩu cán bộ *chia sẻ*, không phải xác thực tài khoản cá nhân. Nếu vận hành thật cần đăng nhập từng người, phân quyền và database ngoài.
- **SEO:** title, H1 và cấu trúc nội dung đã cải thiện; Streamlit không phải framework server-side rendering cho SEO mạnh. Cần landing page HTML/SSR riêng nếu muốn lên kết quả tìm kiếm tốt.
- **Lưu trữ:** SQLite + Google Drive sync (tùy chọn) thích hợp demo, chưa phù hợp đa người dùng đồng thời quy mô lớn.
- **Camera/GPS:** camera web không thể loại bỏ mọi ảnh giả; EXIF GPS không xác thực vị trí; người duyệt phải kiểm tra.
- **Kiểm chứng AI:** bản này không tự tạo kết quả Precision/Recall/mAP cho bộ 60 ảnh của nhóm.

Xem `SECURITY_AND_SEO.md` để đọc kỹ giới hạn và khuyến nghị. Không đưa mật khẩu hoặc khóa API vào repository.
