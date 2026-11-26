from datetime import datetime
from html import escape

import streamlit as st

from core.auth import (
    bootstrap_first_admin,
    change_password,
    get_demo_account_hint,
    has_any_admin,
    login_with_status,
)
from core.config import now_vn
from core.ui import clear_officer_session, disclaimer, is_officer, stretch


def _do_login(officer: dict):
    st.session_state['role'] = 'officer'
    st.session_state['officer_username'] = officer['username']
    st.session_state['officer_name'] = officer.get('full_name') or officer['username']
    st.session_state['officer_unit'] = officer.get('unit') or 'RoadWatch AI'
    st.session_state['officer_role_level'] = officer.get('role') or 'officer'
    st.session_state['officer_login_time'] = now_vn().strftime('%H:%M:%S %d/%m/%Y')


def _role_badge(role_lv: str) -> str:
    if role_lv == 'admin':
        return 'Quản trị viên hệ thống'
    if role_lv == 'field_team':
        return 'Đội duy tu hiện trường'
    return 'Cán bộ kỹ thuật thẩm định'


def show():
    st.markdown("""
    <div class="rw-page-intro">
      <span class="rw-overline">Cổng nội bộ phân quyền RBAC</span>
      <h1>Xác thực &amp; Điều hành Cán bộ RoadWatch AI</h1>
      <p>Hệ thống tiếp nhận, thẩm định hư hỏng mặt đường, chấm điểm đa tiêu chí AHP và điều phối duy tu đô thị.</p>
    </div>
    """, unsafe_allow_html=True)

    if is_officer():
        name = escape(str(st.session_state.get('officer_name', 'Cán bộ')))
        uname = escape(str(st.session_state.get('officer_username', '')))
        unit = escape(str(st.session_state.get('officer_unit', '')))
        login_time = escape(str(st.session_state.get('officer_login_time', '')))
        role_lv = st.session_state.get('officer_role_level', 'officer')
        badge = _role_badge(role_lv)

        st.success(f'**Phiên đang mở** — Chào **{name}** (`{uname}` · {badge})')

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"""
            <div class="rw-glass-card" style="padding:20px;margin-bottom:16px;">
              <h3 style="margin-top:0;font-size:1.1rem;color:#FFFFFF;">Thông tin phiên làm việc</h3>
              <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
                <tr style="border-bottom:1px solid rgba(255,255,255,0.12);">
                  <td style="padding:8px 0;color:#CBD5E1;width:38%;">Họ tên & Tài khoản:</td>
                  <td style="padding:8px 0;font-weight:600;color:#FFFFFF;">{name} (<code>{uname}</code>)</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.12);">
                  <td style="padding:8px 0;color:#CBD5E1;">Đơn vị chuyên môn:</td>
                  <td style="padding:8px 0;font-weight:600;color:#FFFFFF;">{unit}</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.12);">
                  <td style="padding:8px 0;color:#CBD5E1;">Cấp phân quyền:</td>
                  <td style="padding:8px 0;font-weight:600;color:#7DD3FC;">{badge}</td>
                </tr>
                <tr>
                  <td style="padding:8px 0;color:#CBD5E1;">Đăng nhập lúc:</td>
                  <td style="padding:8px 0;color:#FFFFFF;">{login_time}</td>
                </tr>
              </table>
            </div>
            """, unsafe_allow_html=True)

            st.subheader('Điều hướng nhanh')
            q1, q2, q3 = st.columns(3)
            with q1:
                target_p1 = 'views/route.py' if role_lv == 'field_team' else 'views/queue.py'
                lbl_p1 = 'Lộ trình được giao' if role_lv == 'field_team' else 'Hàng chờ xác minh'
                if st.button(lbl_p1, **stretch(st.button)):
                    st.switch_page(target_p1)
            with q2:
                target_p2 = 'views/compare.py' if role_lv == 'field_team' else 'views/priority.py'
                lbl_p2 = 'Nghiệm thu sửa chữa' if role_lv == 'field_team' else 'Ưu tiên AHP & Dự toán'
                if st.button(lbl_p2, **stretch(st.button)):
                    st.switch_page(target_p2)
            with q3:
                if st.button('Tuần đường & Video', **stretch(st.button)):
                    st.switch_page('views/video.py')

            with st.expander('Đổi mật khẩu cá nhân'):
                with st.form('change_pw_form'):
                    old_pw = st.text_input('Mật khẩu hiện tại', type='password')
                    new_pw = st.text_input('Mật khẩu mới (tối thiểu 6 ký tự)', type='password')
                    new_pw2 = st.text_input('Xác nhận mật khẩu mới', type='password')
                    if st.form_submit_button('Cập nhật mật khẩu'):
                        if new_pw != new_pw2:
                            st.error('Mật khẩu xác nhận không khớp.')
                        else:
                            err = change_password(st.session_state.get('officer_username', ''), old_pw, new_pw)
                            if not err:
                                st.success('Đổi mật khẩu thành công!')
                            else:
                                st.error(err)

        with col2:
            st.markdown("""
            <div class="rw-glass-card" style="padding:20px;margin-bottom:12px;">
              <h4 style="margin:0 0 10px 0;font-size:1rem;color:#FFFFFF;">Kết thúc ca trực</h4>
              <p style="font-size:0.85rem;color:#CBD5E1;margin-bottom:16px;line-height:1.5;">
                Mọi thao tác duyệt, gộp và nghiệm thu đều được ghi nhận gắn với mã tài khoản của bạn.
              </p>
            </div>
            """, unsafe_allow_html=True)
            if st.button('Đăng xuất an toàn', key='logout_main_page', **stretch(st.button)):
                clear_officer_session()
                st.rerun()

        disclaimer()
        return

    # ── Nếu hệ thống mới triển khai chưa có tài khoản Admin nào ───────────
    if not has_any_admin():
        st.info('**Thiết lập lần đầu:** Hệ thống chưa có Quản trị viên. Hãy tạo tài khoản Quản trị viên đầu tiên (hoặc đặt `ROADWATCH_ADMIN_PASSWORD` trong Streamlit Secrets).')
        with st.form('bootstrap_admin_form'):
            b_user = st.text_input('Tên đăng nhập Quản trị viên', value='admin')
            b_name = st.text_input('Họ và tên', value='Quản trị viên hệ thống')
            b_pw1 = st.text_input('Mật khẩu Quản trị viên (tối thiểu 8 ký tự)', type='password')
            b_pw2 = st.text_input('Nhập lại mật khẩu', type='password')
            if st.form_submit_button('Khởi tạo Quản trị viên & Đăng nhập', type='primary'):
                if b_pw1 != b_pw2:
                    st.error('Mật khẩu nhập lại không khớp.')
                else:
                    err = bootstrap_first_admin(b_user, b_pw1, b_name)
                    if err:
                        st.error(err)
                    else:
                        officer, _ = login_with_status(b_user, b_pw1)
                        if officer:
                            _do_login(officer)
                            st.rerun()

    col_info, col_form = st.columns([1.1, 1], gap='large')

    with col_info:
        st.markdown("""
        <div class="rw-glass-card" style="padding:24px;margin-bottom:16px;">
          <h3 style="margin-top:0;font-size:1.15rem;color:#FFFFFF;">Phân quyền Nghiệp vụ Cán bộ</h3>
          <ul style="font-size:0.9rem;color:#E2E8F0;line-height:1.9;padding-left:20px;margin-bottom:0;">
            <li><strong>Cán bộ thẩm định:</strong> Duyệt/từ chối ảnh D00/D10/D20/D40, gộp báo cáo trùng và xuất báo cáo PDF.</li>
            <li><strong>Quy hoạch & Xếp hạng AHP:</strong> Tinh chỉnh ma trận Saaty 4 tiêu chí, phát hiện hành lang xuống cấp và dự toán kinh phí.</li>
            <li><strong>Đội duy tu hiện trường:</strong> Nhận lộ trình giao việc, chạy chế độ Tuần đường GPS và cập nhật ảnh nghiệm thu Trước/Sau.</li>
            <li><strong>Bảo mật tự động:</strong> Khóa tạm thời 10 phút nếu nhập sai mật khẩu quá 5 lần liên tiếp.</li>
          </ul>
        </div>
        """, unsafe_allow_html=True)

        demo_hint = get_demo_account_hint()
        if demo_hint:
            demo_user, demo_pw = demo_hint
            st.markdown('---')
            st.markdown('**Chế độ Trình diễn Đồ án / Hội đồng Đánh giá**')
            st.caption(f'Đang bật qua cấu hình demo · Tài khoản thử nghiệm: `{demo_user}`')
            if st.button('Đăng nhập Nhanh (Dành cho Hội đồng Chấm thi)', type='secondary', use_container_width=True):
                officer, err = login_with_status(demo_user, demo_pw)
                if officer:
                    _do_login(officer)
                    st.session_state['_post_login_target'] = 'route' if officer.get('role') == 'field_team' else 'queue'
                    st.rerun()
                else:
                    st.error(err or 'Không thể đăng nhập tài khoản Demo.')

    with col_form:
        st.markdown("""
        <div class="rw-glass-card" style="border-top:4px solid #38BDF8 !important;padding:24px;margin-bottom:14px;">
          <h3 style="margin-top:0;font-size:1.2rem;color:#FFFFFF;">Đăng nhập Tài khoản Cán bộ</h3>
          <p style="font-size:0.85rem;color:#CBD5E1;margin-bottom:4px;">Sử dụng tài khoản cá nhân được Quản trị viên cấp trên hệ thống Supabase.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form('officer_login_form', clear_on_submit=False):
            username = st.text_input('Tên đăng nhập', placeholder='Ví dụ: admin hoặc cb_duytu01')
            entered_pw = st.text_input('Mật khẩu', type='password', placeholder='Nhập mật khẩu')
            submitted = st.form_submit_button(
                'Xác thực & Truy cập Cổng Cán bộ',
                type='primary',
                **stretch(st.form_submit_button),
            )
            if submitted:
                officer, err_msg = login_with_status(username, entered_pw)
                if officer:
                    _do_login(officer)
                    st.session_state['_post_login_target'] = 'route' if officer.get('role') == 'field_team' else 'queue'
                    st.rerun()
                else:
                    st.error(err_msg)

        st.caption('Chưa có tài khoản? Liên hệ **Quản trị viên RoadWatch AI** để được cấp quyền.')

    disclaimer()


show()
