import hmac
from html import escape
from datetime import datetime

import streamlit as st

from core.auth import change_password, login
from core.config import cfg
from core.ui import disclaimer, is_officer, stretch


# ─── Hằng: TK test nhanh ───────────────────────────────────────────────────
_DEMO_USER = 'canbo01'
_DEMO_PASS = 'canbo123'


def _do_login(officer: dict):
    """Ghi session sau khi xác thực thành công."""
    st.session_state['role'] = 'officer'
    st.session_state['officer_username'] = officer['username']
    st.session_state['officer_name'] = officer['full_name'] or officer['username']
    st.session_state['officer_unit'] = officer['unit'] or 'RoadWatch AI'
    st.session_state['officer_role_level'] = officer['role']   # 'admin' | 'officer'
    st.session_state['officer_login_time'] = datetime.now().strftime('%H:%M:%S %d/%m/%Y')


def show():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1E3A8A 0%, #1D4ED8 60%, #2563EB 100%);
                color: #fff; border-radius: 16px; padding: clamp(24px, 4vw, 36px); margin-bottom: 24px;
                box-shadow: 0 10px 25px -5px rgba(29, 78, 216, 0.4);">
      <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 8px;">
        <span style="font-size: 2.2rem; background: rgba(255,255,255,0.18); border-radius: 50%; width: 54px; height: 54px; display: inline-flex; align-items: center; justify-content: center;">🏛️</span>
        <div>
          <span style="display: inline-block; background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.35); padding: 2px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;">Cổng nội bộ chuyên trách</span>
          <h2 style="color: #fff; margin: 4px 0 0 0; font-size: clamp(1.4rem, 2.5vw, 1.8rem); font-weight: 700;">Xác thực & Điều hành Cán bộ RoadWatch AI</h2>
        </div>
      </div>
      <p style="color: #DBEAFE; margin: 8px 0 0 0; font-size: 0.95rem; max-width: 70ch; line-height: 1.5;">
        Hệ thống tiếp nhận, thẩm định hư hỏng mặt đường và điều phối công tác duy tu hạ tầng giao thông đô thị.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Đã đăng nhập ─────────────────────────────────────────────────────
    if is_officer():
        name = escape(str(st.session_state.get('officer_name', 'Cán bộ')))
        unit = escape(str(st.session_state.get('officer_unit', '')))
        login_time = escape(str(st.session_state.get('officer_login_time', '')))
        role_lv = st.session_state.get('officer_role_level', 'officer')
        badge = '👑 Quản trị viên' if role_lv == 'admin' else '🛡️ Cán bộ kỹ thuật'

        st.success(f"🟢 **Phiên đang mở** — Chào **{name}** ({badge})")

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #E2E8F0;border-radius:12px;padding:20px;margin-bottom:16px;">
              <h3 style="margin-top:0;font-size:1.1rem;color:#0F172A;">📋 Thông tin phiên làm việc</h3>
              <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
                <tr style="border-bottom:1px solid #F1F5F9;">
                  <td style="padding:8px 0;color:#64748B;width:38%;">Tên / Mã cán bộ:</td>
                  <td style="padding:8px 0;font-weight:600;color:#0F172A;">{name}</td>
                </tr>
                <tr style="border-bottom:1px solid #F1F5F9;">
                  <td style="padding:8px 0;color:#64748B;">Đơn vị:</td>
                  <td style="padding:8px 0;font-weight:600;color:#0F172A;">{unit}</td>
                </tr>
                <tr style="border-bottom:1px solid #F1F5F9;">
                  <td style="padding:8px 0;color:#64748B;">Phân quyền:</td>
                  <td style="padding:8px 0;font-weight:600;color:#1D4ED8;">{badge}</td>
                </tr>
                <tr>
                  <td style="padding:8px 0;color:#64748B;">Đăng nhập lúc:</td>
                  <td style="padding:8px 0;color:#0F172A;">{login_time}</td>
                </tr>
              </table>
            </div>
            """, unsafe_allow_html=True)

            st.subheader('Thao tác nhanh')
            q1, q2, q3 = st.columns(3)
            with q1:
                if st.button('✅ Hàng chờ xác minh', **stretch(st.button)):
                    try:
                        st.switch_page('views/queue.py')
                    except Exception:
                        st.rerun()
            with q2:
                if st.button('📊 Ưu tiên kiểm tra', **stretch(st.button)):
                    try:
                        st.switch_page('views/priority.py')
                    except Exception:
                        st.rerun()
            with q3:
                if st.button('🚗 Lộ trình & giao việc', **stretch(st.button)):
                    try:
                        st.switch_page('views/route.py')
                    except Exception:
                        st.rerun()

            # Đổi mật khẩu cá nhân
            with st.expander('🔑 Đổi mật khẩu cá nhân'):
                with st.form('change_pw_form'):
                    old_pw = st.text_input('Mật khẩu hiện tại', type='password')
                    new_pw = st.text_input('Mật khẩu mới (tối thiểu 6 ký tự)', type='password')
                    new_pw2 = st.text_input('Xác nhận mật khẩu mới', type='password')
                    if st.form_submit_button('Lưu mật khẩu mới'):
                        uname = st.session_state.get('officer_username', '')
                        if new_pw != new_pw2:
                            st.error('Mật khẩu xác nhận không khớp.')
                        else:
                            err = change_password(uname, old_pw, new_pw)
                            st.success('✅ Đổi mật khẩu thành công!') if not err else st.error(err)

        with col2:
            st.markdown("""
            <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:20px;">
              <h4 style="margin:0 0 10px 0;font-size:1rem;color:#0F172A;">Đóng phiên làm việc</h4>
              <p style="font-size:0.85rem;color:#64748B;margin-bottom:16px;line-height:1.5;">
                Đăng xuất khi hoàn thành ca trực để bảo đảm an toàn dữ liệu.
              </p>
            </div>
            """, unsafe_allow_html=True)
            if st.button('🚪 Đăng xuất ngay', key='logout_main_page', **stretch(st.button)):
                for k in ['role', 'officer_username', 'officer_name', 'officer_unit',
                          'officer_role_level', 'officer_login_time']:
                    st.session_state.pop(k, None)
                st.rerun()

        disclaimer()
        return

    # ── Chưa đăng nhập ───────────────────────────────────────────────────
    col_info, col_form = st.columns([1.1, 1], gap='large')

    with col_info:
        st.markdown("""
        <div style="background:#fff;border:1px solid #E2E8F0;border-radius:12px;padding:24px;margin-bottom:16px;">
          <h3 style="margin-top:0;font-size:1.15rem;color:#0F172A;">📋 Quyền hạn & Chức năng Cán bộ</h3>
          <ul style="font-size:0.9rem;color:#334155;line-height:1.9;padding-left:20px;margin-bottom:0;">
            <li><strong>Thẩm định báo cáo hư hỏng:</strong> Duyệt/từ chối ảnh D00/D10/D20/D40 do người dân gửi lên.</li>
            <li><strong>Gộp điểm trùng lặp:</strong> Phát hiện phản ánh cùng vị trí để tránh chồng chéo.</li>
            <li><strong>Xếp hạng AHP (đa tiêu chí):</strong> Phân bổ nguồn lực khoa học theo 4 tiêu chí.</li>
            <li><strong>Lập lộ trình tuần tra:</strong> Gom cụm điểm và xuất lộ trình kiểm tra thực địa.</li>
            <li><strong>Đối chiếu trước/sau sửa chữa:</strong> Lưu hồ sơ hoàn thành để nghiệm thu.</li>
          </ul>
        </div>
        """, unsafe_allow_html=True)

        # Nút đăng nhập test nhanh
        st.markdown('---')
        st.markdown('**🧪 Đăng nhập nhanh để test hệ thống**')
        st.caption(f'Tài khoản demo: `{_DEMO_USER}` / `{_DEMO_PASS}`')
        if st.button('⚡ Đăng nhập Demo (Test nhanh)', type='secondary', use_container_width=True):
            officer = login(_DEMO_USER, _DEMO_PASS)
            if officer:
                _do_login(officer)
                st.success('✅ Đăng nhập demo thành công!')
                try:
                    st.switch_page('views/queue.py')
                except Exception:
                    st.rerun()
            else:
                st.error('Tài khoản demo chưa được khởi tạo. Reload lại trang.')

    with col_form:
        st.markdown("""
        <div style="background:#fff;border:1px solid #CBD5E1;border-top:4px solid #2563EB;border-radius:12px;padding:24px;box-shadow:0 4px 12px rgba(15,23,42,0.04);">
          <h3 style="margin-top:0;font-size:1.2rem;color:#0F172A;">🔐 Đăng nhập Tài khoản Cán bộ</h3>
          <p style="font-size:0.85rem;color:#64748B;margin-bottom:4px;">Mỗi cán bộ có tài khoản riêng do Quản trị viên cấp.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form('officer_login_form', clear_on_submit=False):
            username = st.text_input('👤 Tên đăng nhập', placeholder='Ví dụ: nguyenvana hoặc cb01')
            entered_pw = st.text_input('🔑 Mật khẩu', type='password', placeholder='Nhập mật khẩu được cấp')
            submitted = st.form_submit_button('Xác thực & Truy cập Cổng Cán bộ',
                                              type='primary', **stretch(st.form_submit_button))
            if submitted:
                if not username or not entered_pw:
                    st.error('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.')
                else:
                    officer = login(username, entered_pw)
                    if officer:
                        _do_login(officer)
                        st.success('✅ Đăng nhập thành công!')
                        try:
                            st.switch_page('views/queue.py')
                        except Exception:
                            st.rerun()
                    else:
                        st.error('❌ Tên đăng nhập hoặc mật khẩu không đúng, hoặc tài khoản đã bị vô hiệu hoá.')

        st.caption('Chưa có tài khoản? Liên hệ **Quản trị viên RoadWatch AI** để được cấp.')

    disclaimer()


show()
