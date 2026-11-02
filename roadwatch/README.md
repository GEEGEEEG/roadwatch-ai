# RoadWatch AI

Hệ thống Streamlit: gửi ảnh → nhận diện YOLO (D00/D10/D20/D40) → **cán bộ xác minh** → điểm nóng & xếp hạng → lộ trình/giao việc → ảnh trước/sau → báo cáo PDF/MD.

## Tính năng
| Nhóm | Có gì |
|---|---|
| Gửi báo cáo | Tải nhiều ảnh, chụp từ điện thoại, lấy GPS từ EXIF hoặc trình duyệt hoặc nhập tay, đồng ý lưu dữ liệu, chống ảnh trùng (SHA-256), chấm chất lượng ảnh, gắn cờ báo cáo gửi dồn |
| Xác minh | Hàng chờ duyệt/từ chối, sửa mức độ và cấp tuyến, lịch sử trạng thái, thông báo Telegram khi "Cần kiểm tra sớm" |
| Bản đồ | Gom cụm marker, heatmap, lọc mức độ; công khai chỉ hiện điểm đã xác minh |
| Ưu tiên | Gom điểm nóng (bán kính chỉnh được), tần suất tự tính, 50-30-20, so sánh hai bộ trọng số + Spearman, cộng điểm xu hướng nặng thêm, dự báo mưa (Open-Meteo) |
| Hiện trường | Lộ trình láng giềng gần nhất, link Google Maps, mã QR, phiếu giao việc CSV |
| Sau sửa chữa | So sánh ảnh trước/sau, đóng điểm, diễn tiến theo thời gian |
| Báo cáo | Mẫu cố định, Gemini tùy chọn (chỉ diễn giải), xuất .md và .pdf tiếng Việt kèm ảnh |
| Khảo sát | Video + GPX → khung hình có phát hiện kèm tọa độ nội suy → hàng chờ |
| Đánh giá | Precision/Recall/F1/tỷ lệ báo động giả/bỏ sót ở nhiều ngưỡng, từ nhãn người gán |
| Quản trị | Xuất CSV, sao lưu/khôi phục zip |

---

## Chuẩn bị Mô hình YOLO (D00/D10/D20/D40)

1. Tải checkpoint YOLO 4 lớp (ví dụ từ Hugging Face: `yolo-rdd2022-benchmark`, tìm `yolov8s_seed0_best.pt` hoặc checkpoint 4 lớp tương đương).
2. Đặt file vào `models/model.pt` trong thư mục dự án (hoặc tải lên `MyDrive/RoadWatch_AI/models/model.pt` nếu chạy trên Colab).
3. `.gitignore` đã được cấu hình cho phép commit `models/model.pt` lên GitHub.

---

## Chạy cục bộ
```bash
pip install -r requirements.txt
# Đặt checkpoint 4 lớp vào models/model.pt
export ROADWATCH_OFFICER_PASSWORD=mat-khau-cua-ban
streamlit run app.py
```
Kiểm thử tự động: `pytest tests/test_core.py -q` (không cần mô hình hay GPU).

---

## Chạy trên Google Colab
Mở `RoadWatch_Colab_Launcher.ipynb`, làm theo hướng dẫn trong ô đầu:
1. Tạo thư mục `MyDrive/RoadWatch_AI/` trên Google Drive.
2. Nén dự án thành `roadwatch.zip` và upload lên đó.
3. Đặt model tại `MyDrive/RoadWatch_AI/models/model.pt`.
4. Trong Colab → Biểu tượng chìa khóa (Secrets), đặt:
   - `ROADWATCH_OFFICER_PASSWORD` (bắt buộc)
   - `NGROK_AUTHTOKEN` (bắt buộc để tạo tunnel)
   - Tùy chọn: `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
5. Chạy tuần tự từng ô trong notebook. Dữ liệu có thể sao lưu định kỳ về Drive bằng ô "Sao lưu lên Drive".

---

## Deploy lên Streamlit Community Cloud

### Điều kiện tiên quyết
1. **Repo GitHub public** (Streamlit Community Cloud miễn phí).
2. Checkpoint **`models/model.pt`** phải có trong repo (`.gitignore` đã cấu hình cho phép commit file này).
3. Tài khoản [share.streamlit.io](https://share.streamlit.io/) kết nối với GitHub.

### Bước thực hiện
1. Push toàn bộ mã nguồn và `models/model.pt` lên GitHub.
2. Vào **[share.streamlit.io](https://share.streamlit.io/)** → *New app* → chọn repository → Branch: `main` → Main file path: `app.py`.
3. Mở **Advanced settings → Secrets** và thêm:
   ```toml
   ROADWATCH_OFFICER_PASSWORD = "mật-khẩu-cán-bộ"
   # Tùy chọn Gemini & Telegram:
   GEMINI_API_KEY = "AIza..."
   TELEGRAM_BOT_TOKEN = "..."
   TELEGRAM_CHAT_ID = "..."

   # Tùy chọn đồng bộ Google Drive (nếu muốn giữ dữ liệu khi app khởi động lại):
   # GDRIVE_FOLDER_ID = "1AbCdEf..."
   # GDRIVE_SERVICE_ACCOUNT_JSON = '{"type": "service_account", ...}'
   ```
4. Nhấn **Deploy** — app sẽ tự cài đặt thư viện và khởi động.

### Tối ưu PyTorch CPU-only & RAM
Community Cloud cấp **~1 GB RAM free**. 
- Trong `requirements.txt` đã cấu hình `--extra-index-url https://download.pytorch.org/whl/cpu` và ghim `torch>=2.2,<3`, `torchvision>=0.17,<1` để tải bản CPU nhẹ (~300–600 MB) thay vì bản CUDA (~2–3 GB).
- Module nhận diện (`core/detector.py`) tự động giới hạn cạnh dài ảnh đầu vào tối đa `1920 px` trước khi dự đoán để tránh spike bộ nhớ.
- Trọng số mô hình được cache bằng `@st.cache_resource`, chỉ nạp 1 lần duy nhất trong toàn bộ vòng đời ứng dụng.
- Ước tính mức tiêu thụ RAM ổn định: **~500–650 MB**, an toàn trong hạn mức 1 GB.

### Giới hạn của Community Cloud (free tier)
| Giới hạn | Giá trị | Ảnh hưởng |
|---|---|---|
| RAM | ~1 GB | Cần PyTorch CPU-only; ảnh lớn tự scale xuống ≤ 1920 px |
| Ổ đĩa | Ephemeral (tạm thời) | Dữ liệu local mất khi app ngủ/reboot. Cần đồng bộ Drive hoặc Postgres |
| Tự ngủ | Sau 12 giờ không có truy cập | Khởi động lại sau ~30 giây khi có người truy cập |
| Truy cập | Công khai | Tuyệt đối không lưu dữ liệu thật khi app demo công khai |

### Lưu trữ dữ liệu bền vững
1. **Google Drive Sync (đã tích hợp trong code):**
   - Thêm `GDRIVE_FOLDER_ID` và `GDRIVE_SERVICE_ACCOUNT_JSON` vào Streamlit Secrets.
   - Ứng dụng tự động tải `roadwatch.db` về khi khởi động, đồng bộ DB và upload ảnh (gốc, annotated, after) lên Drive sau mỗi lượt ghi.
   - Thích hợp cho thử nghiệm và quy mô nội bộ/vừa phải.
2. **Postgres & Object Storage (khi mở rộng người dùng đồng thời):**
   - Có thể chuyển sang Supabase (Postgres + Storage) hoặc Neon + Cloudflare R2 khi có số lượng người dùng gửi báo cáo đồng thời lớn.

---

## Bảo mật & tuân thủ
- **Không commit** file `.env`, service account key, hay mật khẩu lên GitHub. Dùng Streamlit Secrets hoặc biến môi trường.
- **Không dùng dữ liệu thật của người dân** trên môi trường thử nghiệm công khai.
- Ảnh và vị trí của người gửi là **dữ liệu cá nhân** — luôn yêu cầu người dùng xác nhận đồng ý (`consent`) trước khi lưu.
- Mật khẩu cán bộ dùng để phân quyền ở mức cơ bản cho mô hình demo.

## Giới hạn cần nói rõ (SPEC.md)
- Mức độ hư hỏng và điểm ưu tiên là **quy tắc giả định** do nhóm nghiên cứu thiết kế, không đo đạc cơ học hay phản ánh trực tiếp chi phí thực tế.
- Gemini chỉ hỗ trợ viết **diễn giải ngôn ngữ tự nhiên**; toàn bộ số liệu thống kê đều được trích xuất trực tiếp từ bảng cơ sở dữ liệu.
- Hệ thống không tự ý phát sinh hay điền giả tọa độ GPS khi người dùng không cung cấp.
