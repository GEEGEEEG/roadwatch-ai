# HƯỚNG DẪN CẬP NHẬT ROADWATCH AI PRO LÊN GITHUB / STREAMLIT

## 0. Bản này làm được gì?

Bản Professional chỉnh trực tiếp project nhóm gửi, không huấn luyện lại mô hình. Các chức năng cũ như YOLO 4 lớp, bản đồ, xác minh, xếp hạng, báo cáo, kiểm tra ảnh trước/sau, video + GPX vẫn nằm trong code.

### Thay đổi chính

- Trang đầu có thông điệp chính, hình minh họa bằng CSS, hai CTA rõ ràng.
- Cổng công dân: **chụp qua camera web**, không có nút `file_uploader`.
- Cổng cán bộ: được lựa chọn **tải ảnh lên** hoặc **chụp qua camera**.
- Form đơn giản theo trình tự **chụp → GPS → xác nhận → gửi**; bản đồ chọn điểm chỉ tải khi cần.
- Model YOLO chỉ được nạp khi bấm gửi ảnh, giúp trang đầu nhẹ hơn. Checkpoint được cache trong phiên chạy.
- Ghi thêm `capture_method` và `gps_accuracy_m` nếu có (độ chính xác ước tính, không phải GPS đã xác minh).
- Bản đồ dùng OpenStreetMap có attribution thay vì gọi tile Google không chính thức.
- Tối ưu lưu JPEG ảnh có bounding box (tối đa 2000px, quality 83), giới hạn upload 12MB.
- Chuẩn hóa màu, font, spacing, responsive; thêm hiển thị rõ nguồn dữ liệu và cảnh báo an toàn.
- Bảo vệ thêm trường HTML cán bộ, giới hạn file khôi phục và phòng CSV injection cho xuất file quản trị.

## 1. Đưa code lên GitHub

1. Giải nén file `ROADWATCH_AI_PRO_WEB.zip`.
2. Trong thư mục vừa giải nén phải có **trực tiếp** `app.py`, `requirements.txt`, `core/`, `views/`, `models/`, `.streamlit/config.toml`, `packages.txt`. **Không** upload nguyên ZIP lên GitHub.
3. Trước khi thay thế repo hiện tại, **sao lưu repo/nhánh cũ**. Nếu có dữ liệu khảo sát thực, sao lưu từ khu vực quản trị trước khi nâng cấp.
4. Trên GitHub, tạo branch mới `redesign-v4` rồi tải hoặc commit toàn bộ file code mới lên branch (không đưa `.env`, secrets hay `data/` vào repo).
5. Mở file `requirements.txt` trên GitHub để xác nhận có Ultralytics, Streamlit, folium, Pillow, torch và các thư viện liên quan.
6. Checkpoint `models/model.pt` đã được đóng trong bản nhận từ nhóm; **đối chiếu giấy phép trước khi để repo public**. Nếu repo Private, cấp quyền repo cho Streamlit khi kết nối GitHub.

## 2. Triển khai Streamlit Community Cloud

1. Mở `https://share.streamlit.io/` → **Create app** → chọn mã nguồn từ GitHub.
2. Chọn repository, branch `redesign-v4` hoặc `main` (sau khi đã chốt), main file path là **`app.py`**.
3. Chọn Python **3.11 hoặc 3.12**.
4. Trong **Advanced settings → Secrets**, đặt:

```toml
ROADWATCH_OFFICER_PASSWORD = "mật_khẩu_riêng_dài_và_mạnh"
```

Nếu có sử dụng các chức năng tùy chọn, nhập secret tương ứng vào Streamlit, **không thêm vào GitHub**. Các khóa ngoài có thể gồm `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GDRIVE_FOLDER_ID`, `GDRIVE_SERVICE_ACCOUNT_JSON`. Phải làm đúng cấu trúc trong tài liệu cũ khi muốn dùng Google Drive.

5. Nhấn **Deploy** và xem Logs. Nếu báo lỗi thiếu thư viện hoặc thiếu checkpoint, xem file/path trên GitHub, không lặp lại bước ngrok/Colab.
6. Mở link `https://<ten-app>.streamlit.app`. SSL/HTTPS được nền tảng cung cấp, code không tự cấu hình SSL.

## 3. Checklist kiểm tra thực tế trên điện thoại

- [ ] Truy cập trang chủ trên iPhone/Android, hero hiển thị đẹp; không kéo ngang.
- [ ] Hai CTA ở vùng đầu trang bấm được: Gửi phản ánh / Bản đồ.
- [ ] Cổng công dân **không có file uploader**, chỉ camera. Trình duyệt cấp quyền Camera được.
- [ ] Không chụp ảnh: trang không bắt tải YOLO hay mở bản đồ nặng.
- [ ] Chụp ảnh: xem preview, bật quyền GPS; nếu sai vị trí thì chỉnh bằng tọa độ/bản đồ.
- [ ] Không có GPS: form không tự tạo vị trí giả.
- [ ] Gửi ảnh: trạng thái **Chờ xác minh**, không tự công khai.
- [ ] Đăng nhập cán bộ: hàng chờ hiển thị ảnh, nguồn ảnh và nguồn GPS.
- [ ] Duyệt ảnh: vị trí hiện trên bản đồ, điểm nóng/xếp hạng tính trên bản ghi đã xác minh.
- [ ] Xuất PDF tiếng Việt: font lấy từ `fonts-dejavu-core` cài qua `packages.txt` trên Cloud.
- [ ] Kiểm tra chức năng xếp hạng 50/30/20, lộ trình, video/GPX và backup trên dữ liệu mẫu.

## 4. Hạn chế nên ghi trong báo cáo

- **Mobile responsive:** CSS đã được xem ở 390px và 1440px, nhưng vẫn cần kiểm tra thực tế qua Streamlit với trình duyệt Android/iOS.
- **SEO:** Streamlit không hỗ trợ SEO/SSR mạnh như một landing page chuyên dụng. Bản này cải thiện heading, tiêu đề, nội dung; muốn Google indexing tốt nên thêm trang tiếp thị HTML/Next.js độc lập.
- **Bảo mật:** Chỉ có mật khẩu cán bộ dùng chung, phù hợp demo. Muốn sử dụng thật cần Auth cá nhân, phân quyền, database tập trung, log và rate limiting.
- **Lưu trữ:** SQLite + tùy chọn sao lưu Drive dễ bị vấn đề ghi đồng thời, không phải hệ thống nhiều người dùng production.
- **Chất lượng AI:** Giao diện mới không có nghĩa mô hình chính xác hơn; vẫn cần 60 ảnh đã gán nhãn để đánh giá độc lập.
- **GPS:** độ chính xác là ước lượng của thiết bị; EXIF không phải xác thực; cần người kiểm tra.

## 5. Khi deploy gặp lỗi

| Vấn đề | Cách kiểm tra |
|---|---|
| Trang trắng, traceback | Mở **Manage app → Logs**, xác định module/line lỗi |
| `ModuleNotFoundError` | `requirements.txt` có ở root, đúng tên package? |
| `Missing model.pt` | `models/model.pt` có trên GitHub và kích thước đúng? |
| Cài torch quá nặng | Xem log pip và khả năng RAM Community Cloud; cân nhắc inference CPU/ONNX sau khi kiểm tra thực nghiệm |
| Camera không lên | Dùng HTTPS, kiểm tra quyền camera của website và điện thoại |
| GPS báo thiếu | Cấp quyền vị trí; nếu không, nhập hoặc chọn vị trí đã xác minh trên bản đồ |
| PDF lỗi font | Kiểm tra `packages.txt` đã cài `fonts-dejavu-core` |
| Dữ liệu mất khi restart | Dùng database ngoài; SQLite của Community Cloud không bảo đảm tồn tại lâu dài |

**Lưu ý kiểm thử:** Đã chạy 27 unit tests phần xử lý thuần thành công. Chưa test được giao diện Streamlit trực tiếp trong môi trường tạo file do không thể cài package Streamlit ở đây; các tương tác thật cần kiểm tra sau khi deploy.
