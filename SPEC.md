# RoadWatch AI v5.0 — Đặc tả Kỹ thuật Tóm tắt

**Quy trình khép kín:**
Gửi ảnh hiện trường → AI YOLO/ONNX nhận diện 4 lớp (`D00`, `D10`, `D20`, `D40`) + Phân đoạn diện tích/thể tích + Khử trùng lặp `dHash` → Hàng chờ thẩm định cán bộ → Gom điểm nóng & Hành lang xuống cấp GIS → Xếp hạng ưu tiên đa tiêu chí AHP (Saaty) & Dự toán kinh phí → Tối ưu lộ trình & Giao việc → Nghiệm thu ảnh Trước/Sau → Xuất phiếu PDF/Markdown.

**Phân quyền hệ thống (RBAC):**
- **Công dân (Public):** Gửi phản ánh (Camera/Upload có giới hạn chống spam), Tra cứu tiến độ theo mã `RW-...` / QR, Xem bản đồ GIS các điểm đã xác minh.
- **Đội duy tu (`field_team`):** Khảo sát Video/Smart Patrol, xem lộ trình việc được giao, tải ảnh nghiệm thu sau sửa chữa.
- **Cán bộ thẩm định (`officer`):** Thẩm định/gộp báo cáo chờ duyệt, điều chỉnh ma trận AHP, phân tích hành lang, xuất báo cáo PDF/AI.
- **Quản trị viên (`admin`):** Toàn quyền hệ thống, quản lý tài khoản cán bộ, cấu hình đơn giá vật tư, sao lưu/khôi phục `.zip` và di trú dữ liệu Supabase.

**Nguyên tắc toàn vẹn dữ liệu:**
1. Chỉ các hồ sơ trạng thái `verified` và `assigned` mới được hiển thị trên bản đồ công khai và đưa vào tính toán xếp hạng ưu tiên / kinh phí duy tu cần phân bổ (`pending`, `rejected`, `merged`, `fixed` được tách riêng).
2. Không bao giờ tự sinh tọa độ giả; nguồn tọa độ luôn được ghi vết rõ ràng (`EXIF GPS`, `GPS trình duyệt`, `Chọn trên bản đồ`, `Nhập tay`).
3. Ảnh trùng tuyệt đối (`SHA-256`) bị chặn ngay từ đầu; ảnh khác góc chụp nhưng cùng vị trí (`<= 35 m`, độ tương đồng thị giác `>= 0.72` từ `dhash_64` + `color_vec`) được tự động gắn cờ cảnh báo cho cán bộ gộp điểm.
4. Dữ liệu cấu trúc lưu nguyên tử trên **Supabase PostgreSQL (`reports`, `report_history`, `officers`, `app_settings`)**; file hình ảnh lưu trên **Supabase Storage (`roadwatch-data`)**.
