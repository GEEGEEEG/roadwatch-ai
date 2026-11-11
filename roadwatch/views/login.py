import hmac
from html import escape
from datetime import datetime

import streamlit as st

from core.config import cfg
from core.ui import disclaimer, is_officer, stretch


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

    if is_officer():
        name = escape(str(st.session_state.get('officer_name', 'Cán bộ kỹ thuật')))
        unit = escape(str(st.session_state.get('officer_unit', 'Ban Quản lý Hạ tầng Giao thông')))
        login_time = escape(str(st.session_state.get('officer_login_time', 'Phiên hiện tại')))

        st.success(f"🟢 **Đã mở phiên quản trị**: Chào mừng **{name}** ({unit})")

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"""
            <div style="background: #fff; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; margin-bottom: 16px;">
              <h3 style="margin-top: 0; font-size: 1.1rem; color: #0F172A; display: flex; align-items: center; gap: 8px;">
                <span>🛡️</span> Thông tin phiên làm việc Cán bộ
              </h3>
              <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                <tr style="border-bottom: 1px solid #F1F5F9;">
                  <td style="padding: 8px 0; color: #64748B; width: 35%;">Họ tên / Mã cán bộ:</td>
                  <td style="padding: 8px 0; font-weight: 600; color: #0F172A;">{name}</td>
                </tr>
                <tr style="border-bottom: 1px solid #F1F5F9;">
                  <td style="padding: 8px 0; color: #64748B;">Đơn vị phụ trách:</td>
                  <td style="padding: 8px 0; font-weight: 600; color: #0F172A;">{unit}</td>
                </tr>
                <tr style="border-bottom: 1px solid #F1F5F9;">
                  <td style="padding: 8px 0; color: #64748B;">Thời gian đăng nhập:</td>
                  <td style="padding: 8px 0; color: #0F172A;">{login_time}</td>
                </tr>
                <tr>
                  <td style="padding: 8px 0; color: #64748B;">Phạm vi quyền hạn:</td>
                  <td style="padding: 8px 0; color: #166534; font-weight: 600;">
                    Toàn quyền duyệt hồ sơ, gom cụm ưu tiên, điều phối lộ trình và quản trị hệ thống
                  </td>
                </tr>
              </table>
            </div>
            """, unsafe_allow_html=True)

            st.subheader('Thao tác nhanh chuyên môn')
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

        with col2:
            st.markdown("""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px;">
              <h4 style="margin: 0 0 10px 0; font-size: 1rem; color: #0F172A;">Đóng phiên làm việc</h4>
              <p style="font-size: 0.85rem; color: #64748B; margin-bottom: 16px; line-height: 1.5;">
                Đăng xuất khi hoàn thành ca trực để bảo đảm an toàn dữ liệu quản lý kết cấu hạ tầng giao thông.
              </p>
            </div>
            """, unsafe_allow_html=True)
            if st.button('🚪 Đăng xuất ngay', key='logout_main_page', **stretch(st.button)):
                st.session_state['role'] = 'citizen'
                st.session_state.pop('officer_name', None)
                st.session_state.pop('officer_unit', None)
                st.session_state.pop('officer_login_time', None)
                st.rerun()

        disclaimer()
        return

    # Khi chưa đăng nhập: Giao diện đăng nhập tiêu chuẩn
    col_info, col_form = st.columns([1.1, 1], gap='large')

    with col_info:
        st.markdown("""
        <div style="background: #fff; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; margin-bottom: 16px;">
          <h3 style="margin-top: 0; font-size: 1.15rem; color: #0F172A; display: flex; align-items: center; gap: 8px;">
            <span>📋</span> Quyền hạn & Chức năng Cán bộ
          </h3>
          <ul style="font-size: 0.9rem; color: #334155; line-height: 1.8; padding-left: 20px; margin-bottom: 0;">
            <li><strong>Thẩm định báo cáo hư hỏng:</strong> Kiểm tra hình ảnh nứt (D00/D10/D20), ổ gà (D40) do người dân gửi lên; duyệt hoặc từ chối kèm lý do.</li>
            <li><strong>Gộp điểm trùng lặp:</strong> Phát hiện các phản ánh cùng vị trí hư hỏng để tránh chồng chéo xử lý.</li>
            <li><strong>Xếp hạng ưu tiên (50-30-20):</strong> Phân bổ nguồn lực dựa trên mức độ nghiêm trọng, mật độ phản ánh và cấp đường.</li>
            <li><strong>Lập lộ trình tuần tra:</strong> Tự động gom cụm các điểm hư hỏng gần nhau và xuất lộ trình kiểm tra thực địa.</li>
            <li><strong>Đối chiếu trước/sau sửa chữa:</strong> Lưu trữ hồ sơ hoàn thành phục vụ nghiệm thu kỹ thuật.</li>
          </ul>
        </div>

        <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 10px; padding: 14px 16px;">
          <div style="display: flex; gap: 10px; align-items: flex-start;">
            <span style="font-size: 1.2rem;">🔒</span>
            <div style="font-size: 0.85rem; color: #1E40AF; line-height: 1.5;">
              <strong>Bảo mật thông tin:</strong> Đây là bản demo dùng mật khẩu chung; người dùng nhập tên cán bộ thủ công. Không sử dụng như hệ thống xác thực danh tính chính thức.
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_form:
        st.markdown("""
        <div style="background: #fff; border: 1px solid #CBD5E1; border-top: 4px solid #2563EB; border-radius: 12px; padding: 24px; box-shadow: 0 4px 12px rgba(15,23,42,0.04);">
          <h3 style="margin-top: 0; font-size: 1.2rem; color: #0F172A;">🔐 Đăng nhập Cán bộ Quản lý</h3>
          <p style="font-size: 0.85rem; color: #64748B; margin-bottom: 16px;">Vui lòng điền thông tin cán bộ trực ca để truy cập các tính năng nghiệp vụ.</p>
        </div>
        """, unsafe_allow_html=True)

        pw = cfg('ROADWATCH_OFFICER_PASSWORD')
        if not pw:
            st.warning('⚠️ Hệ thống chưa cấu hình `ROADWATCH_OFFICER_PASSWORD` trong Streamlit Secrets. Cán bộ tạm thời chưa thể đăng nhập.')
            return

        with st.form('officer_login_form', clear_on_submit=False):
            officer_name = st.text_input('👤 Họ và tên / Mã cán bộ', placeholder='Ví dụ: Nguyễn Văn A hoặc CB-01', value='Cán bộ trực ca')
            officer_unit = st.selectbox('🏢 Đơn vị / Phòng ban công tác', [
                'Đội Quản lý & Duy tu Đường bộ 1',
                'Đội Quản lý & Duy tu Đường bộ 2',
                'Ban Quản lý Dự án Giao thông Đô thị',
                'Thanh tra Sở Giao thông Vận tải',
                'Trung tâm Quản lý Điều hành Giao thông',
                'Đội Tuần tra & Phản ứng nhanh',
                'Khác (Cán bộ độc lập)',
            ])
            entered_pw = st.text_input('🔑 Mật khẩu xác thực', type='password', placeholder='Nhập mật khẩu được cấp')
            
            submitted = st.form_submit_button('Xác thực & Truy cập Cổng Cán Bộ', type='primary', **stretch(st.form_submit_button))

            if submitted:
                if not entered_pw:
                    st.error('Vui lòng nhập mật khẩu xác thực.')
                elif hmac.compare_digest(entered_pw.encode(), pw.encode()):
                    st.session_state['role'] = 'officer'
                    st.session_state['officer_name'] = officer_name.strip() or 'Cán bộ trực ca'
                    st.session_state['officer_unit'] = officer_unit
                    st.session_state['officer_login_time'] = datetime.now().strftime('%H:%M:%S %d/%m/%Y')
                    st.success('✅ Đăng nhập thành công. Đang mở khu vực quản trị...')
                    try:
                        st.switch_page('views/queue.py')
                    except Exception:
                        st.rerun()
                else:
                    st.error('❌ Mật khẩu không chính xác. Vui lòng kiểm tra lại.')

        st.caption('Chưa có tài khoản hoặc cần đặt lại mật khẩu? Liên hệ: **Ban Quản trị Kỹ thuật RoadWatch AI**.')

    disclaimer()


show()
