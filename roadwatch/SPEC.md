# RoadWatch AI — đặc tả ngắn

**Quy trình:** gửi ảnh → nhận diện YOLO (D00/D10/D20/D40) → hàng chờ xác minh → gom điểm nóng → xếp hạng →
lộ trình & giao việc → ảnh trước/sau → đóng điểm → báo cáo.

**Vai trò:** người dân (gửi báo cáo, xem bản đồ công khai) · cán bộ (đăng nhập bằng mật khẩu: duyệt, xếp hạng, giao việc, báo cáo, quản trị).

**Quy tắc bắt buộc**
1. Chỉ báo cáo `verified`/`assigned` được tính vào bản đồ và xếp hạng; `pending`, `rejected`, `fixed` thì không.
2. Không bao giờ tự điền tọa độ. Nguồn tọa độ: EXIF GPS / GPS trình duyệt / nhập tay (có ghi nhãn).
3. Nhãn lớp phải xác minh được là D00/D10/D20/D40; không gán theo index.
4. Điểm mức độ, điểm ưu tiên là quy tắc giả định của nhóm — không phải đo đạc.
5. Gemini chỉ viết đoạn diễn giải; số liệu luôn lấy từ bảng. Không có Gemini vẫn có báo cáo mẫu đầy đủ.
6. Ảnh trùng (SHA-256) không lưu hai lần; báo cáo gửi dồn / ảnh kém chất lượng bị gắn cờ cho người duyệt.

**Điểm ưu tiên** = a·mức độ + b·tần suất(min(n,10)·10) + c·cấp tuyến, mặc định 50-30-20 (tự chuẩn hóa),
+ tùy chọn: xu hướng nặng thêm (≤ +5), dự báo mưa cho điểm có ổ gà (≤ +5).
Điểm nóng = các báo cáo cách "hạt giống" ≤ bán kính (mặc định 40 m), không nối chuỗi.
