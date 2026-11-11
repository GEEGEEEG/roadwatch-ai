# RoadWatch AI — Ghi chú SEO, tốc độ, bảo mật

**Giao diện:** Trang chủ có thông điệp H1, CTA ở vùng đầu trang; bố cục tự co giãn với CSS grid và native Streamlit; nhãn và trợ giúp rõ ràng. Be Vietnam Pro tải bằng Google Fonts với `display=swap`, có font hệ thống dự phòng. Nếu cần không gửi truy vấn font ra bên ngoài, bỏ dòng `@import` trong `core/theme.py`.

**SEO:** Streamlit là web app thiên về tương tác, HTML được tạo phía client; không thể hứa tối ưu SEO như một trang React/Next SSR hoặc HTML tĩnh. Tựa trang và heading được cải thiện. Muốn SEO sâu, làm landing HTML/Next.js riêng cùng domain và đặt nút dẫn vào ứng dụng.

**HTTPS/SSL:** Không tạo SSL trong code. Streamlit Community Cloud cung cấp HTTPS cho ứng dụng trên `*.streamlit.app`; SSL cho domain riêng phụ thuộc cấu hình hosting/domain.

**Quyền riêng tư:** Mặc định bản đồ công khai chỉ dùng dữ liệu được xác minh và không xuất ảnh gốc. Camera web **không** chứng minh ảnh xác thực; EXIF GPS **không** chứng minh vị trí xác thực. Tránh thu thông tin cá nhân không cần thiết.

**Xác thực cán bộ:** Hiện chỉ dùng một mật khẩu chung qua Streamlit Secrets, *không* đủ cho môi trường production. Nếu dùng thật cần tài khoản từng cán bộ, RBAC, rate-limit, audit log chống sửa đổi, quy trình đặt lại mật khẩu.

**Lưu trữ:** SQLite + sao lưu Drive trong bản gốc phù hợp demo, chưa phù hợp cho nhiều người dùng đồng thời (nguy cơ ghi đè snapshot giữa các phiên). Khi dùng thật nên chuyển PostgreSQL/Supabase có bảng dữ liệu và storage riêng, kiểm soát truy cập.

**Tile bản đồ:** Bỏ các URL Google Maps tile không chính thức, dùng OpenStreetMap có ghi công trong Folium. Bản đồ công khai cho địa điểm, không hiển thị dữ liệu danh tính.

**Tối ưu:** Chỉ tải YOLO khi thực sự gửi ảnh, dùng cache cho checkpoint, bản đồ sửa tọa độ mở theo nhu cầu; ảnh dự đoán lưu JPEG chất lượng 83 và giới hạn 2000px để giảm dung lượng. `MAX_BYTES=12MB` được kiểm tra trên server.
