from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from core import db, storage, supabase_rest
from core.auth import create_officer, is_admin, list_officers, reset_password, toggle_active
from core.backup import make_backup, restore_backup
from core.config import PROJECT_ROOT, data_dir, model_path
from core.cost_estimation import UNIT_PRICES
from core.notify import send_telegram, telegram_configured
from core.ui import current_actor, df_show, disclaimer, page_intro, require_officer, safe_csv_export

require_officer(('admin', 'officer'))
page_intro(
    'QUẢN TRỊ HỆ THỐNG',
    'Hạ tầng Supabase, Tài khoản RBAC & Định mức',
    'Chẩn đoán cơ sở dữ liệu PostgreSQL + Storage CDN, quản lý phân quyền cán bộ và đơn giá duy tu.',
)

current_user = st.session_state.get('officer_username', '')
_is_admin = is_admin(current_user)

admin_tabs = st.tabs([
    '☁️ Hạ tầng Supabase & Dữ liệu',
    '👥 Quản lý Tài khoản Cán bộ (RBAC)',
    '💰 Định mức Đơn giá Vật tư',
])

# ── Tab 1: Hạ tầng Supabase & Sao lưu ─────────────────────────────────────
with admin_tabs[0]:
    df = db.fetch_df()
    pg_active = db.using_postgres()
    m_path = model_path()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric('Tổng bản ghi hồ sơ', len(df))
    k2.metric('Engine CSDL hiện hành', 'Supabase PostgreSQL' if pg_active else 'SQLite (Cục bộ)')
    k3.metric('Lưu trữ ảnh Cloud', storage.get_backend_type().upper())
    k4.metric('Mô hình AI', f"{'ONNX' if m_path.suffix == '.onnx' else 'PyTorch'} ({'Có' if m_path.is_file() else 'Thiếu'})")

    if telegram_configured() and st.button('📲 Gửi tin nhắn kiểm tra Telegram'):
        st.success('Đã gửi Telegram thành công!') if send_telegram('RoadWatch AI v5.0: Kết nối Telegram hoạt động tốt.') else st.error('Gửi Telegram thất bại.')

    st.markdown('---')
    st.subheader('☁️ Trạng thái Kết nối Supabase (PostgreSQL + Storage CDN)')

    col_diag1, col_diag2 = st.columns(2)
    with col_diag1:
        if st.button('🔍 Chẩn đoán toàn diện Supabase (DB + Storage)', use_container_width=True, type='primary'):
            with st.spinner('Đang kiểm tra bảng PostgreSQL và Bucket lưu trữ...'):
                pg_diag = supabase_rest.diagnose_postgres()
                st_diag = storage.test_connection()
                if pg_diag['all_ready']:
                    st.success(pg_diag['message'])
                else:
                    st.warning(pg_diag['message'])
                if st_diag['ok']:
                    st.success(st_diag['message'])
                else:
                    st.error(st_diag['message'])

    with col_diag2:
        if storage.is_enabled():
            if st.button('🔄 Đồng bộ dữ liệu cục bộ & ảnh lên Supabase', use_container_width=True):
                with st.spinner('Đang đồng bộ ảnh và chuyển tiếp dữ liệu lên Supabase...'):
                    n_ok, n_total, errs = storage.sync_all_to_cloud()
                    if errs:
                        st.warning(f'Đã tải {n_ok}/{n_total} tệp. Chi tiết lưu ý:\n' + '\n'.join(errs[:5]))
                    else:
                        st.success(f'🎉 Đồng bộ thành công {n_ok}/{n_total} tệp & bản ghi lên Supabase vĩnh viễn!')

    sql_file = PROJECT_ROOT / 'migrations' / '001_supabase_schema.sql'
    with st.expander('📖 Hướng dẫn cấu hình chuẩn Supabase PostgreSQL + Secrets (1 phút)'):
        st.markdown("""
        **Bước 1 — Tạo bảng PostgreSQL + PostGIS trên Supabase:**
        1. Mở trang quản trị [Supabase Dashboard](https://supabase.com/dashboard) → chọn Project của bạn.
        2. Mở **SQL Editor** ở thanh bên trái → nhấn **New query**.
        3. Sao chép đoạn mã SQL dưới đây dán vào ô soạn thảo và nhấn **Run**:
        """)
        if sql_file.is_file():
            st.code(sql_file.read_text(encoding='utf-8'), language='sql')
        st.markdown("""
        **Bước 2 — Cấu hình Streamlit Cloud Secrets (`App settings → Secrets`):**
        ```toml
        SUPABASE_URL = "https://xxxx.supabase.co"
        SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOi..."   # Lấy tại Project Settings -> API -> service_role (secret)
        SUPABASE_BUCKET = "roadwatch-data"
        ROADWATCH_ADMIN_PASSWORD = "MatKhauAdminManhCuaBan"
        ROADWATCH_DEMO_MODE = "true"                  # Đặt "false" nếu muốn ẩn nút đăng nhập Demo của Hội đồng
        ```
        """)

    st.markdown('---')
    if not df.empty:
        st.subheader('Danh sách bản ghi dữ liệu')
        df_show(df.drop(columns=['detections_json', 'color_vec'], errors='ignore'), hide_index=True)
        st.download_button(
            '⬇️ Xuất toàn bộ dữ liệu (.csv)',
            safe_csv_export(df.drop(columns=['detections_json', 'color_vec'], errors='ignore')),
            file_name='RoadWatch_all_reports.csv',
            mime='text/csv',
        )

    st.subheader('Sao lưu & Khôi phục (.zip)')
    st.download_button(
        '⬇️ Tải gói sao lưu cục bộ (.zip)',
        make_backup(),
        file_name=f"roadwatch_backup_{datetime.now():%Y%m%d_%H%M}.zip",
        mime='application/zip',
    )
    if _is_admin:
        up = st.file_uploader('Khôi phục từ gói sao lưu .zip (Chỉ dành cho Quản trị viên)', type=['zip'])
        if up and st.button('⚠️ Khôi phục dữ liệu từ file .zip'):
            try:
                restore_backup(up.getvalue())
                st.success('Đã khôi phục dữ liệu cục bộ. Nhấn "Đồng bộ dữ liệu cục bộ & ảnh lên Supabase" nếu muốn đẩy lên Cloud.')
            except Exception as exc:
                st.error(f'Không khôi phục được: {exc}')
    else:
        st.caption('🔒 Chức năng ghi đè khôi phục file `.zip` chỉ mở cho vai trò Quản trị viên (`admin`).')

# ── Tab 2: Quản lý Tài khoản Cán bộ (RBAC) ────────────────────────────────
with admin_tabs[1]:
    if not _is_admin:
        st.warning('⚠️ Chỉ **Quản trị viên (`admin`)** mới có quyền tạo hoặc thay đổi tài khoản cán bộ.')
        st.info(f'Tài khoản hiện tại: `{current_user}`.')
    else:
        officers = list_officers()
        st.subheader(f'Danh sách tài khoản hệ thống ({len(officers)} tài khoản)')
        if officers:
            df_off = pd.DataFrame(officers)[['username', 'full_name', 'unit', 'role', 'active', 'created_at', 'last_login']]
            role_names = {'admin': '👑 Quản trị viên', 'officer': '🛡️ Thẩm định', 'field_team': '🚧 Đội duy tu'}
            df_off['role'] = df_off['role'].map(lambda r: role_names.get(r, r))
            df_off['active'] = df_off['active'].map({1: '✅ Hoạt động', 0: '🔴 Đã khóa'})
            df_off.columns = ['Tên đăng nhập', 'Họ tên', 'Đơn vị', 'Vai trò', 'Trạng thái', 'Ngày tạo', 'Đăng nhập cuối']
            df_show(df_off, hide_index=True)

        st.markdown('---')
        act_col1, act_col2 = st.columns(2)
        with act_col1:
            st.subheader('➕ Cấp tài khoản cán bộ mới')
            with st.form('create_officer_form', clear_on_submit=True):
                new_uname = st.text_input('Tên đăng nhập *', placeholder='vd: cb_tham_dinh_01')
                new_fullname = st.text_input('Họ và tên đầy đủ', placeholder='Nguyễn Văn A')
                new_unit = st.selectbox('Đơn vị chuyên môn', [
                    'Đội Quản lý & Duy tu Đường bộ 1',
                    'Đội Quản lý & Duy tu Đường bộ 2',
                    'Ban Quản lý Dự án Giao thông Đô thị',
                    'Thanh tra Sở Xây dựng / Giao thông',
                    'Trung tâm Điều hành Giao thông Thông minh',
                    'Đội Tuần tra & Phản ứng nhanh',
                ])
                new_role = st.selectbox(
                    'Nhóm phân quyền (RBAC)',
                    ['officer', 'field_team', 'admin'],
                    format_func=lambda x: {
                        'officer': '🛡️ Cán bộ kỹ thuật thẩm định',
                        'field_team': '🚧 Đội duy tu hiện trường',
                        'admin': '👑 Quản trị viên hệ thống',
                    }[x],
                )
                new_pw = st.text_input('Mật khẩu khởi tạo *', type='password', placeholder='Tối thiểu 6 ký tự')
                new_pw2 = st.text_input('Xác nhận mật khẩu *', type='password')
                if st.form_submit_button('✅ Tạo tài khoản trên hệ thống', type='primary'):
                    if new_pw != new_pw2:
                        st.error('Mật khẩu xác nhận không khớp.')
                    else:
                        err = create_officer(new_uname, new_pw, new_fullname, new_unit, new_role)
                        if err:
                            st.error(err)
                        else:
                            st.success(f'✅ Đã cấp tài khoản **{new_uname}** thành công!')
                            st.rerun()

        with act_col2:
            st.subheader('🔧 Khóa / Mở khóa & Đặt lại mật khẩu')
            usernames = [o['username'] for o in officers if o['username'] != current_user]
            if not usernames:
                st.info('Chưa có tài khoản cán bộ nào khác ngoài bạn.')
            else:
                sel_user = st.selectbox('Chọn tài khoản cần thao tác', usernames)
                cur_active = next((o['active'] for o in officers if o['username'] == sel_user), 1)
                btn_label = '🔴 Vô hiệu hóa tài khoản này' if cur_active else '✅ Kích hoạt lại tài khoản này'
                if st.button(btn_label, use_container_width=True):
                    new_state = toggle_active(sel_user)
                    st.success(f"Đã {'kích hoạt' if new_state else 'vô hiệu hóa'} tài khoản **{sel_user}**.")
                    st.rerun()

                with st.form('reset_pw_form'):
                    st.markdown(f'**Đặt lại mật khẩu cho `{sel_user}`** *(đồng thời mở khóa nếu bị khóa tạm)*')
                    reset_pw = st.text_input('Mật khẩu mới', type='password')
                    reset_pw2 = st.text_input('Xác nhận mật khẩu mới', type='password')
                    if st.form_submit_button('🔑 Xác nhận đặt lại mật khẩu'):
                        if reset_pw != reset_pw2:
                            st.error('Mật khẩu xác nhận không khớp.')
                        else:
                            err = reset_password(sel_user, reset_pw)
                            st.error(err) if err else st.success(f'✅ Đã đặt lại mật khẩu cho **{sel_user}**.')

# ── Tab 3: Định mức Đơn giá Vật tư ─────────────────────────────────────────
with admin_tabs[2]:
    cur_prices = {**UNIT_PRICES, **(db.get_setting('unit_prices') or {})}
    st.subheader('💰 Cấu hình Đơn giá Tham chiếu Duy tu Đường bộ (VNĐ)')
    st.caption('Áp dụng trực tiếp cho bảng Dự toán kinh phí tại Hàng chờ thẩm định, Quy hoạch hành lang và Báo cáo.')
    with st.form('unit_prices_form'):
        c_p1, c_p2 = st.columns(2)
        p_bag = c_p1.number_input('Nhựa nguội Carboncor (VNĐ / bao 25kg)', min_value=10000, max_value=2000000, value=int(cur_prices['carboncor_bag_25kg']), step=5000)
        p_btn = c_p2.number_input('Thảm bê tông nhựa nóng BTN (VNĐ / m²)', min_value=50000, max_value=5000000, value=int(cur_prices['btn_hot_mix_m2']), step=10000)
        p_conc = c_p1.number_input('Bê tông xi măng M250 (VNĐ / m³)', min_value=200000, max_value=10000000, value=int(cur_prices['concrete_m3']), step=50000)
        p_lab = c_p2.number_input('Nhân công & máy đầm cơ sở (VNĐ / điểm)', min_value=20000, max_value=3000000, value=int(cur_prices['labor_per_point']), step=10000)
        save_p = st.form_submit_button('💾 Lưu định mức đơn giá', type='primary', disabled=not _is_admin)
        if save_p and _is_admin:
            db.set_setting(
                'unit_prices',
                {
                    'carboncor_bag_25kg': int(p_bag),
                    'btn_hot_mix_m2': int(p_btn),
                    'concrete_m3': int(p_conc),
                    'labor_per_point': int(p_lab),
                },
                actor=current_actor(),
            )
            st.success('✅ Đã cập nhật bảng đơn giá duy tu trên hệ thống!')
    if not _is_admin:
        st.caption('🔒 Chỉ Quản trị viên (`admin`) mới được phép thay đổi định mức đơn giá.')

disclaimer()
