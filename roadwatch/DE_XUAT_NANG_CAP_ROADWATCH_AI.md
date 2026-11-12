# 🚀 ĐỀ XUẤT ĐỊNH HƯỚNG NÂNG CẤP ĐỀ TÀI: ROADWATCH AI
**Hệ thống Giám sát, Quản lý & Cảnh báo Tình trạng Hư hỏng Mặt đường Đô thị**

---

## I. TỔNG QUAN HIỆN TRẠNG DỰ ÁN (AS-IS)

Hiện tại, hệ thống **RoadWatch AI** đã hoàn thiện các module nền tảng cốt lõi:
1. **Kiến trúc Web:** Xây dựng trên nền tảng Streamlit, phân chia rõ 2 luồng trải nghiệm: **Người dân** (tối giản, gửi ảnh/định vị) và **Cán bộ quản lý** (thẩm định hàng chờ, duyệt, tra cứu).
2. **Thị giác máy tính (Computer Vision):** Mô hình YOLOv8 phát hiện các loại hư hỏng phổ biến (ổ gà, vết nứt, vũng lún).
3. **Bản đồ GIS:** Tích hợp Folium với lớp bản đồ Google Vệ tinh (Hybrid), hỗ trợ kéo thả ghim (`dragend`) cập nhật tọa độ & reverse-geocoding điền tên đường tự động.
4. **Hạ tầng Dữ liệu:** SQLite nội bộ kết hợp **cơ chế tự động đồng bộ 2 chiều với Google Drive** qua Service Account (không lo mất dữ liệu khi reboot server).
5. **Đánh giá sơ bộ:** Áp dụng ma trận trọng số cơ bản 50-30-20 (Mức độ hư hại - Cấp đường - Tần suất tái lặp).

---

## II. 4 TRỤ CỘT NÂNG CẤP CHI TIẾT (TO-BE)

### 1. 🧠 Nâng cấp AI & Computer Vision (Tăng hàm lượng công nghệ)

* **Ước lượng diện tích hư hại thực tế (YOLOv8-Segmentation):**
  * *Vấn đề:* Bounding box hình chữ nhật hiện tại chỉ cho biết vị trí, không thể hiện diện tích tổn thương mặt đường.
  * *Giải pháp:* Chuyển sang mô hình phân đoạn đối tượng (Instance Segmentation). Hệ thống sẽ tách chính xác đường viền vết nứt/ổ gà, từ đó tính tỷ lệ pixel hư hại trên tổng diện tích lòng đường quan sát được -> ước lượng diện tích hư hại ($m^2$).
* **Phát hiện trùng lặp đa góc chụp (Visual Deduplication):**
  * *Vấn đề:* Cùng một ổ gà nhưng hai người dân chụp ở hai góc lệch nhau 10m hoặc ánh sáng khác nhau sẽ bị tính thành 2 lỗi riêng biệt.
  * *Giải pháp:* Trích xuất vector đặc trưng ảnh (Image Embedding qua MobileNet / ResNet / CLIP). Khi có ảnh mới trong cùng bán kính GPS hẹp (<= 15m), thuật toán so sánh độ tương đồng Cosine: nếu trùng khớp -> tự động gộp vào báo cáo cũ và tăng "Số lượt cử tri phản ánh" (Upvotes).
* **Đánh giá chất lượng ảnh đầu vào (Image Quality Assessment):**
  * Tự động cảnh báo nếu ảnh chụp quá mờ (Laplacian blur), chụp ban đêm thiếu sáng, hoặc góc chụp quá nghiêng trước khi cho phép gửi.

---

### 2. 🗺️ Nâng cấp Quản trị Hạ tầng & Quy hoạch Bảo trì (Tăng tính thực tiễn)

* **Gom cụm hư hỏng theo tuyến đường (Hotspot & Spatial Clustering):**
  * *Ứng dụng:* Sử dụng thuật toán học máy phi giám sát **DBSCAN** hoặc **K-Means** trên tọa độ không gian.
  * *Giá trị:* Nếu trên một đoạn 300m có tới 8 ổ gà xuất hiện đồng thời, hệ thống không báo cáo 8 vụ riêng lẻ mà tự động đóng khung cả đoạn: **"Cụm hư hỏng diện rộng (Hotspot) – Khuyến nghị thảm nhựa toàn phần thay vì chắp vá cục bộ"**.
* **Chuẩn hóa mô hình ra quyết định AHP (Analytic Hierarchy Process):**
  * Nâng cấp công thức 50-30-20 thành mô hình toán học AHP chuẩn khoa học để xếp hạng thứ tự ưu tiên sửa chữa dựa trên ma trận so sánh cặp:
    1. Mức độ hư hại và kích thước ổ gà ($C_1$)
    2. Cấp độ đường: Quốc lộ, Tỉnh lộ, Đường nội bộ ($C_2$)
    3. Mật độ giao thông và bán kính gần các địa điểm trọng yếu: Trường học, Bệnh viện, Khu công nghiệp ($C_3$)
    4. Tốc độ lưu thông tối đa cho phép trên tuyến ($C_4$)
* **Dự toán sơ bộ khối lượng vật liệu & chi phí bảo trì:**
  * Dựa trên loại tổn thương và diện tích ước tính, hệ thống tự động xuất bảng dự trù: khối lượng nhựa đường nguội (Carboncor Asphalt) hoặc bê tông cần dùng, cùng kinh phí ước tính theo đơn giá định mức nhà nước.

---

### 3. 🚗 Thu thập dữ liệu Tự động & Đa kênh Tiếp cận (Mở rộng quy mô)

* **Chế độ Tuần đường Thông minh (Smart Patrol / Dashcam Mode):**
  * Thay vì người dân phải dừng lại bấm chụp từng tấm, cho phép cán bộ tuần tra gắn smartphone lên kính chắn gió xe ô tô/xe máy, bật camera và chạy dọc tuyến đường.
  * Video stream được cắt khung hình định kỳ (1-2 fps), AI tự quét nhận diện ổ gà kèm tọa độ GPS hành trình liên tục theo thời gian thực.
* **Tích hợp Kênh phản ánh qua Bot Zalo / Telegram:**
  * Người dân không cần truy cập web hoặc cài đặt ứng dụng: Chỉ cần mở Zalo/Telegram, bấm **"Gửi vị trí hiện tại"** + **"Gửi ảnh chụp"** cho Chatbot. Webhook sẽ tự động nạp dữ liệu vào hàng chờ RoadWatch AI.

---

### 4. 📢 Cảnh báo Nguy cơ Thời gian thực cho Tài xế

* **Chế độ Lái xe An toàn (Real-time Hazard Audio Warning):**
  * Người tham gia giao thông bật bản đồ khi di chuyển. Khi phương tiện tiến gần một điểm hư hỏng nghiêm trọng chưa được khắc phục trong phạm vi $50m - 100m$, hệ thống tự động phát âm thanh cảnh báo bằng giọng nói: *"Chú ý: Phía trước có ổ gà nguy hiểm, giảm tốc độ!"*.

---

## III. MA TRẬN ĐÁNH GIÁ TÍNH KHẢ THI (FEASIBILITY MATRIX)

| Tính năng đề xuất | Mức độ khó | Thời gian ước tính | Giá trị ăn điểm (Hội đồng/Ban giám khảo) | Đề xuất triển khai |
| :--- | :---: | :---: | :---: | :---: |
| **1. Gom cụm hư hỏng (Hotspot Map / DBSCAN)** | Vừa phải | 2 - 3 ngày | ⭐⭐⭐⭐⭐ (Trực quan, thực tiễn cao) | **Ưu tiên số 1** |
| **2. Chuẩn hóa lý thuyết chấm điểm AHP** | Dễ | 1 - 2 ngày | ⭐⭐⭐⭐⭐ (Rất vững về mặt học thuật) | **Ưu tiên số 1** |
| **3. Dự toán khối lượng vật tư & chi phí** | Vừa phải | 2 ngày | ⭐⭐⭐⭐ (Cán bộ quản lý rất thích) | **Ưu tiên số 2** |
| **4. AI Phân đoạn diện tích (YOLO-Seg)** | Nâng cao | 4 - 6 ngày | ⭐⭐⭐⭐⭐ (Đột phá công nghệ CV) | **Ưu tiên số 2** |
| **5. Cảnh báo giọng nói khi lái xe** | Dễ | 1 - 2 ngày | ⭐⭐⭐⭐ (Trải nghiệm người dùng tốt) | **Ưu tiên số 3** |
| **6. Tuần đường tự động (Dashcam mode)** | Nâng cao | 5 - 7 ngày | ⭐⭐⭐⭐⭐ (Rất ấn tượng khi demo) | **Ưu tiên số 3** |
| **7. Bot Zalo / Telegram tiếp nhận** | Vừa phải | 3 - 4 ngày | ⭐⭐⭐⭐ (Tiếp cận cộng đồng thực tế) | Dự phòng |

---

## IV. PHÂN CHIA NHIỆM VỤ GỢI Ý CHO THÀNH VIÊN NHÓM

* **Thành viên 1 (Phụ trách AI & Xử lý ảnh):**
  * Nghiên cứu triển khai phân đoạn diện tích (Segmentation) hoặc bộ lọc kiểm tra ảnh mờ/ảnh ngược sáng.
  * Tinh chỉnh ngưỡng Confidence và đo lường độ chính xác (mAP, Precision, Recall) để đưa vào bảng số liệu báo cáo.
* **Thành viên 2 (Phụ trách Bản đồ & Không gian địa lý - GIS):**
  * Viết module thuật toán gom cụm không gian (DBSCAN/K-Means) trên tọa độ GPS để hiển thị các vùng cảnh báo đỏ trên bản đồ Folium.
  * Tích hợp tính năng cảnh báo âm thanh/khoảng cách an toàn cho người điều khiển phương tiện.
* **Thành viên 3 (Phụ trách Thuật toán Nghiệp vụ & Backend):**
  * Thiết lập mô hình ma trận trọng số AHP, bảng tính định mức chi phí bảo trì dự kiến theo loại hư hại.
  * Kiểm tra và duy trì luồng đồng bộ Google Drive, hoàn thiện xuất phiếu thẩm định hiện trường PDF chuẩn hóa.
* **Thành viên 4 (Phụ trách Báo cáo, Đánh giá & Khảo sát):**
  * Viết thuyết minh đề tài: Tổng quan nghiên cứu, cơ sở toán học AHP, quy trình nghiệp vụ kiểm định đường bộ.
  * Thu thập thêm dữ liệu thực tế tại địa phương để tạo tập kiểm thử (Test set) cho slide thuyết trình.

---

## V. KHUYẾN NGHỊ KHI BẢO VỆ ĐỀ TÀI / ĐỒ ÁN

Nhóm nên tập trung vào **2 điểm nhấn chiến lược** để gây ấn tượng mạnh với hội đồng:
1. **Điểm nhấn Thị giác:** Bản đồ khoanh vùng cụm hư hỏng (Hotspot Cluster) theo từng đoạn đường, cho thấy hệ thống có khả năng hỗ trợ quy hoạch vĩ mô chứ không dừng lại ở việc xem từng cái ổ gà lẻ tẻ.
2. **Điểm nhấn Phương pháp luận:** Thay thế công thức điểm số định tính bằng mô hình ra quyết định đa tiêu chí chuẩn mực **AHP (Analytic Hierarchy Process)**.
