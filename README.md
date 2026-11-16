# RoadWatch AI v5.0 — Hệ thống Giám sát & Quản lý Duy tu Mặt đường Thông minh

RoadWatch AI kết hợp **Thị giác máy tính (YOLO / ONNX 4 lớp RDD2022: D00, D10, D20, D40)**, **Phân đoạn hình thái tính diện tích/thể tích hư hỏng**, **Khử trùng lặp đa góc chụp (`dHash` 64-bit + Color Vector)**, **Gom cụm hành lang tuyến xuống cấp GIS** và **Mô hình ra quyết định đa tiêu chí AHP (Saaty)** trên nền tảng **Streamlit Cloud + Supabase PostgreSQL & Storage CDN**.

---

## 1. Những cải tiến cốt lõi ở bản v5.0

1. **Cơ sở dữ liệu Supabase PostgreSQL + PostGIS nguyên bản (`core/supabase_rest.py`, `core/db.py`)**:
   - Ghi/đọc theo từng bản ghi nguyên tử (Atomic Row-level CRUD) vào các bảng `reports`, `report_history`, `officers`, `app_settings` thông qua HTTPS PostgREST — loại bỏ hoàn toàn lỗi ghi đè file `roadwatch.db` khi nhiều người gửi cùng lúc và giữ bền vững tài khoản cán bộ cùng ảnh nghiệm thu sau sửa chữa qua mọi lần Streamlit ngủ/khởi động lại.
   - Tự động fallback mượt mà về SQLite WAL cục bộ khi chạy offline hoặc chạy bộ kiểm thử `pytest`.
2. **Bảo mật & Phân quyền 3 cấp RBAC (`core/auth.py`, `views/login.py`)**:
   - Băm mật khẩu `PBKDF2-HMAC-SHA256` (260.000 vòng), khóa tạm thời 10 phút khi đăng nhập sai 5 lần liên tiếp (chống Brute-force).
   - Phân quyền 3 vai trò: **`admin`** (Quản trị hệ thống, tài khoản, đơn giá, sao lưu), **`officer`** (Cán bộ thẩm định & điều phối lộ trình), **`field_team`** (Đội duy tu hiện trường & cập nhật ảnh nghiệm thu).
   - Chế độ Demo an toàn (`ROADWATCH_DEMO_MODE = "true"`) phục vụ Hội đồng chấm Đồ án mà không phơi bày tài khoản Quản trị.
3. **Cổng Tra cứu Tiến độ Công dân & Tối ưu Trải nghiệm (`views/track.py`, `views/submit.py`, `views/map.py`)**:
   - Cấp mã hồ sơ `RW-...` kèm mã QR để người dân tra cứu tiến độ 4 bước và đối chiếu ảnh Trước/Sau sửa chữa.
   - Bộ nhớ đệm `@st.cache_data` theo SHA-256 cho AI Preview và tái sử dụng kết quả suy luận khi bấm Gửi (giảm 50–80% tải CPU trên Streamlit Cloud).
   - Bản đồ GIS tuân thủ bản quyền (OpenStreetMap, CartoDB Positron, Esri World Imagery) kèm lớp vẽ **Hành lang xuống cấp diện rộng** (`PolyLine` + bán kính bao phủ).
4. **Độ chính xác Khoa học AI & Quy hoạch (`core/damage_analysis.py`, `core/ahp.py`, `core/cost_estimation.py`)**:
   - Mặt nạ pixel hợp nhất (`global_defect_mask`) chống tính trùng diện tích khi các bounding box chồng lấn, kết hợp trọng số phối cảnh theo chiều dọc khung hình.
   - Trình chỉnh sửa Ma trận so sánh cặp Saaty 4x4 kiểm tra trực tiếp tỷ số nhất quán `CR < 0.10` và chuẩn hóa đồng nhất thang điểm `0–100`.
   - Hỗ trợ suy luận siêu nhẹ bằng **ONNX Runtime** (`scripts/export_onnx.py`) song song với PyTorch Ultralytics.

---

## 2. Cấu trúc thư mục chuẩn (Phẳng tại gốc Repository)

```text
roadwatch-ai/
├── app.py                          # Entrypoint chính cho Streamlit Cloud (Main file path: app.py)
├── requirements.txt                # Thư viện Python tối ưu cho Cloud CPU
├── packages.txt                    # Gói hệ thống Linux (libgl1, libglib2.0-0, fonts-dejavu-core)
├── migrations/
│   └── 001_supabase_schema.sql     # Script khởi tạo bảng PostgreSQL + PostGIS + Storage RLS trên Supabase
├── core/                           # Tầng nghiệp vụ, AI, GIS, AHP, Auth RBAC, Supabase PostgREST & Storage
├── views/                          # 13 phân hệ giao diện Công dân & Cán bộ
├── models/                         # Checkpoint mô hình (model.pt hoặc model.onnx)
├── scripts/
│   └── export_onnx.py              # Công cụ chuyển đổi model.pt -> model.onnx nhẹ RAM
├── tests/                          # Bộ kiểm thử tự động pytest (Core + AppTest UI)
└── .github/workflows/              # CI tự động chạy Ruff + Pytest & Keep-Alive chống ngủ app
```

---

## 3. Cài đặt & Triển khai nhanh (Supabase + Streamlit Cloud)

### Bước 1: Khởi tạo bảng trên Supabase (1 lần duy nhất)
1. Đăng nhập [Supabase Dashboard](https://supabase.com/dashboard) → Mở dự án của bạn → chọn **SQL Editor** → **New query**.
2. Dán toàn bộ nội dung file [`migrations/001_supabase_schema.sql`](migrations/001_supabase_schema.sql) và nhấn **Run**.
3. Vào **Project Settings → API** để lấy `Project URL` và khóa `service_role` (secret).

### Bước 2: Cấu hình Streamlit Community Cloud
1. Mở [share.streamlit.io](https://share.streamlit.io/) → chọn ứng dụng (hoặc **Create app**).
2. Thiết lập:
   - **Branch:** `main`
   - **Main file path:** `app.py` *(Lưu ý: `app.py` đã nằm ngay thư mục gốc)*
3. Vào **App settings → Secrets**, dán cấu hình mẫu sau:

```toml
# Kết nối Supabase PostgreSQL & Storage
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
SUPABASE_BUCKET = "roadwatch-data"

# Mật khẩu khởi tạo tài khoản Quản trị viên (username: admin)
ROADWATCH_ADMIN_PASSWORD = "MatKhauAdminManh@2026"

# Chế độ phục vụ Bảo vệ Đồ án / Báo cáo (hiển thị nút đăng nhập nhanh quyền Cán bộ Demo, KHÔNG có quyền Admin)
ROADWATCH_DEMO_MODE = "true"
ROADWATCH_DEMO_USER = "canbo_demo"
ROADWATCH_DEMO_PASSWORD = "Demo@RoadWatch2026"

# Tùy chọn mở rộng (không bắt buộc)
# GEMINI_API_KEY = "AIza..."
# TELEGRAM_BOT_TOKEN = "123456:ABC..."
# TELEGRAM_CHAT_ID = "-100..."
```

---

## 4. Chạy thử nghiệm và Kiểm thử cục bộ

```bash
pip install -r requirements.txt
pytest -q
streamlit run app.py
```

Tài liệu hướng dẫn cập nhật qua **GitHub Desktop** chi tiết xem tại [`HUONG_DAN_CAP_NHAT_VA_TEST.md`](HUONG_DAN_CAP_NHAT_VA_TEST.md).
