# HƯỚNG DẪN CẬP NHẬT TRỰC TIẾP LÊN GITHUB (GITHUB DESKTOP) & KẾT NỐI SUPABASE

Tài liệu này hướng dẫn quy trình quản lý mã nguồn **RoadWatch AI v5.0** trực tiếp từ máy tính Windows lên nhánh `main` trên GitHub để **Streamlit Community Cloud** tự động cập nhật giao diện mới.

---

## Phần 1: Đồng bộ mã nguồn lên GitHub bằng GitHub Desktop

### Bước 1: Tải Repository của bạn về máy bằng GitHub Desktop
1. Tải và mở ứng dụng **[GitHub Desktop](https://desktop.github.com/)** → Đăng nhập tài khoản GitHub của bạn.
2. Chọn **File → Clone repository...** → Chọn kho chứa `roadwatch-ai` của bạn → Chọn thư mục lưu trên máy (ví dụ: `D:\GitHub\roadwatch-ai`) → Nhấn **Clone**.

### Bước 2: Chép bản nâng cấp v5.0 vào thư mục vừa Clone
1. Mở thư mục `D:\GitHub\roadwatch-ai` bạn vừa clone về:
   - Xóa các thư mục/file cũ bên trong **ngoại trừ thư mục ẩn `.git`** *(thư mục `.git` lưu lịch sử kết nối với GitHub của bạn)*.
2. Mở thư mục chứa mã nguồn đã nâng cấp:
   `C:\Users\phatt\.gemini\antigravity\scratch\roadwatch-ai`
3. Copy **toàn bộ tất cả file và thư mục** trong đó (bao gồm cả `.github`, `.streamlit`, `.devcontainer`, `.gitignore`, `app.py`, `core`, `views`, `migrations`, `models`, `scripts`, `tests`, `requirements.txt`, `packages.txt`...) dán đè vào `D:\GitHub\roadwatch-ai`.
4. **Mẹo quan trọng để làm việc lâu dài với Antigravity:**
   Trong cửa sổ Antigravity, bấm **File → Open Folder...** và chọn chính thư mục `D:\GitHub\roadwatch-ai` làm Active Workspace. Từ lần sau trở đi, mỗi khi bạn nhờ AI sửa bất kỳ tính năng hay giao diện nào, GitHub Desktop sẽ tự động nhận diện từng dòng thay đổi ngay lập tức!

### Bước 3: Đẩy (Push) lên nhánh `main`
1. Mở lại **GitHub Desktop** → Bạn sẽ thấy danh sách các file vừa được nâng cấp ở cột bên trái.
2. Ở góc dưới bên trái:
   - Ô **Summary (required)**: nhập `Nâng cấp toàn diện RoadWatch AI v5.0 (Supabase PostgreSQL + RBAC + Tracking)`
   - Nhấn nút xanh **Commit to main**.
3. Nhấn nút **Push origin** trên thanh công cụ phía trên cùng.

> **Mẹo sửa nhanh không cần mở phần mềm:** Khi đang xem kho code trên trình duyệt web `github.com`, bạn chỉ cần nhấn phím dấu chấm **`.`** trên bàn phím — GitHub sẽ mở ngay trình soạn thảo **VS Code Web (`github.dev`)** cho phép bạn sửa văn bản/code và bấm Commit trực tiếp trên trình duyệt.

---

## Phần 2: Nâng cấp Cơ sở dữ liệu Supabase (1 phút)

1. Mở [Supabase Dashboard](https://supabase.com/dashboard) → chọn project của bạn.
2. Ở thanh bên trái, bấm **SQL Editor** → **New query**.
3. Mở file `migrations/001_supabase_schema.sql` trong dự án, copy toàn bộ nội dung dán vào khung SQL và bấm **Run**.
   - Lệnh này sẽ tự tạo 4 bảng chuẩn hóa (`officers`, `reports`, `report_history`, `app_settings`), bật tiện ích không gian `PostGIS`, và khởi tạo bucket ảnh `roadwatch-data`.
4. Vào **Project Settings → API**, copy:
   - **Project URL** (`https://...supabase.co`)
   - Khóa **`service_role` (secret)** *(khuyến nghị dùng `service_role` ở phía server Streamlit Secrets để PostgREST ghi dữ liệu an toàn mà không phải mở quyền ghi công khai cho khóa `anon`)*.

---

## Phần 3: Kiểm tra đường dẫn & Secrets trên Streamlit Cloud

Vì cấu trúc thư mục v5.0 đã được làm phẳng gọn chuẩn xác ngay tại gốc dự án (thay vì lồng `roadwatch/app.py` như trước):

1. Mở [share.streamlit.io](https://share.streamlit.io/) → Bấm dấu `⋮` cạnh app của bạn → **Settings**.
2. Tại mục **General**: kiểm tra **Main file path** đổi từ `roadwatch/app.py` thành **`app.py`** (nếu trước đây bạn trỏ vào `roadwatch/app.py`).
3. Tại mục **Secrets**, dán cấu hình:

```toml
SUPABASE_URL = "https://ten-du-an-cua-ban.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "dan-khoa-service-role-vao-day"
SUPABASE_BUCKET = "roadwatch-data"

ROADWATCH_ADMIN_PASSWORD = "MatKhauAdminCuaBan@2026"
ROADWATCH_DEMO_MODE = "true"
```

4. Nhấn **Save** → Trang web sẽ tự động khởi động lại với giao diện v5.0.
5. Nếu bạn từng có dữ liệu cũ lưu trong file `roadwatch.db`, chỉ cần đăng nhập tài khoản `admin` → vào trang **Quản trị hệ thống** → bấm nút **🔄 Đồng bộ & Di trú lên Supabase** là toàn bộ dữ liệu cũ sẽ được đẩy sang bảng PostgreSQL mới tự động!
