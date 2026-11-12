from core.ui import page_intro
import streamlit as st

from core import db
from core.auth import (create_officer, is_admin, list_officers,
                       reset_password, toggle_active)
from core.backup import make_backup, restore_backup
from core.config import cfg, data_dir, model_path
from core.notify import send_telegram, telegram_configured
from core.priority import build_hotspots
from core.ui import df_show, disclaimer, require_officer, safe_csv_export
from datetime import datetime

require_officer()
page_intro('QUẢN TRỊ HỆ THỐNG', 'Cấu hình & sao lưu',
           'Theo dõi dữ liệu và quản lý tài khoản cán bộ, sao lưu hoặc khôi phục cấu hình.')

admin_tabs = st.tabs(['📊 Dữ liệu & Sao lưu', '👥 Quản lý Tài khoản Cán bộ'])

# ── Tab 1: Dữ liệu & Sao lưu ──────────────────────────────────────────────
with admin_tabs[0]:
    df = db.fetch_df()
    st.write(f'Thư mục dữ liệu: `{data_dir()}` — **{len(df)}** bản ghi.')
    st.write(f'Mô hình: `{model_path()}` — {"✅ có" if model_path().is_file() else "❌ THIẾU"}')
    st.write('Telegram: ' + ('✅ đã cấu hình' if telegram_configured() else '—'))
    if telegram_configured() and st.button('Gửi thử Telegram'):
        st.success('OK') if send_telegram('RoadWatch: tin nhắn thử') else st.error('Gửi thất bại')

    if not df.empty:
        df_show(df.drop(columns=['detections_json']))
        st.download_button('⬇️ Tải toàn bộ bản ghi (.csv)',
                           safe_csv_export(df.drop(columns=['detections_json'])),
                           file_name='RoadWatch_all_reports.csv', mime='text/csv')

    st.subheader('Sao lưu / khôi phục')
    st.download_button('⬇️ Tải bản sao lưu (.zip: CSDL + ảnh)', make_backup(),
                       file_name=f"roadwatch_backup_{datetime.now():%Y%m%d_%H%M}.zip",
                       mime='application/zip')
    up = st.file_uploader('Khôi phục từ file .zip', type=['zip'])
    if up and st.button('Khôi phục (ghi đè dữ liệu cùng tên)'):
        try:
            restore_backup(up.getvalue())
            st.success('Đã khôi phục.')
        except Exception as exc:
            st.error(f'Không khôi phục được: {exc}')

# ── Tab 2: Quản lý Tài khoản Cán bộ ──────────────────────────────────────
with admin_tabs[1]:
    current_user = st.session_state.get('officer_username', '')
    _is_admin = is_admin(current_user)

    if not _is_admin:
        st.warning('⚠️ Chỉ **Quản trị viên** (role = admin) mới có quyền quản lý tài khoản cán bộ.')
        st.info(f'Tài khoản hiện tại: `{current_user}` — không có quyền admin.')
        disclaimer()
        st.stop()

    # Danh sách tài khoản hiện có
    officers = list_officers()
    st.subheader(f'Danh sách tài khoản ({len(officers)} tài khoản)')

    if officers:
        import pandas as pd
        df_off = pd.DataFrame(officers)[['username', 'full_name', 'unit', 'role', 'active', 'created_at', 'last_login']]
        df_off.columns = ['Tên đăng nhập', 'Họ tên', 'Đơn vị', 'Vai trò', 'Hoạt động', 'Ngày tạo', 'Đăng nhập cuối']
        df_off['Hoạt động'] = df_off['Hoạt động'].map({1: '✅ Hoạt động', 0: '🔴 Vô hiệu'})
        st.dataframe(df_off, hide_index=True, use_container_width=True)

    st.markdown('---')
    act_col1, act_col2 = st.columns(2)

    # Tạo tài khoản mới
    with act_col1:
        st.subheader('➕ Tạo tài khoản mới')
        with st.form('create_officer_form', clear_on_submit=True):
            new_uname = st.text_input('Tên đăng nhập *', placeholder='vd: nguyenvana hoặc cb02')
            new_fullname = st.text_input('Họ và tên đầy đủ', placeholder='Nguyễn Văn A')
            new_unit = st.selectbox('Đơn vị / Phòng ban', [
                'Đội Quản lý & Duy tu Đường bộ 1',
                'Đội Quản lý & Duy tu Đường bộ 2',
                'Ban Quản lý Dự án Giao thông Đô thị',
                'Thanh tra Sở Giao thông Vận tải',
                'Trung tâm Quản lý Điều hành Giao thông',
                'Đội Tuần tra & Phản ứng nhanh',
                'Khác (Cán bộ độc lập)',
            ])
            new_role = st.selectbox('Vai trò', ['officer', 'admin'],
                                    format_func=lambda x: '🛡️ Cán bộ kỹ thuật' if x == 'officer' else '👑 Quản trị viên')
            new_pw = st.text_input('Mật khẩu tạm thời *', type='password',
                                   placeholder='Tối thiểu 6 ký tự, cán bộ đổi sau')
            new_pw2 = st.text_input('Xác nhận mật khẩu *', type='password')
            if st.form_submit_button('✅ Tạo tài khoản', type='primary'):
                if new_pw != new_pw2:
                    st.error('Mật khẩu xác nhận không khớp.')
                else:
                    err = create_officer(new_uname, new_pw, new_fullname, new_unit, new_role)
                    if err:
                        st.error(err)
                    else:
                        st.success(f'✅ Đã tạo tài khoản **{new_uname}** thành công! Thông báo mật khẩu tạm cho cán bộ.')
                        st.rerun()

    # Reset mật khẩu / bật-tắt tài khoản
    with act_col2:
        st.subheader('🔧 Quản lý tài khoản')
        if officers:
            usernames = [o['username'] for o in officers if o['username'] != current_user]
            if not usernames:
                st.info('Không có tài khoản nào khác để quản lý.')
            else:
                sel_user = st.selectbox('Chọn tài khoản', usernames)

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    cur_active = next((o['active'] for o in officers if o['username'] == sel_user), 1)
                    btn_label = '🔴 Vô hiệu hoá' if cur_active else '✅ Kích hoạt lại'
                    if st.button(btn_label, use_container_width=True):
                        new_state = toggle_active(sel_user)
                        label = 'kích hoạt' if new_state else 'vô hiệu hoá'
                        st.success(f'Đã {label} tài khoản **{sel_user}**.')
                        st.rerun()

                with col_btn2:
                    if 'confirm_delete' not in st.session_state:
                        st.session_state['confirm_delete'] = False

                with st.form('reset_pw_form'):
                    st.markdown(f'**Reset mật khẩu cho: `{sel_user}`**')
                    reset_pw = st.text_input('Mật khẩu mới (tối thiểu 6 ký tự)', type='password')
                    reset_pw2 = st.text_input('Xác nhận mật khẩu mới', type='password')
                    if st.form_submit_button('🔑 Reset mật khẩu'):
                        if reset_pw != reset_pw2:
                            st.error('Mật khẩu xác nhận không khớp.')
                        else:
                            err = reset_password(sel_user, reset_pw)
                            if err:
                                st.error(err)
                            else:
                                st.success(f'✅ Đã reset mật khẩu cho **{sel_user}**. Thông báo cho cán bộ mật khẩu mới.')

disclaimer()
