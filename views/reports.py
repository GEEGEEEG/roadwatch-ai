from datetime import timedelta

import streamlit as st

from core import db
from core.config import cfg, now_vn, today_vn
from core.priority import build_hotspots
from core.report import (
    acceptance_record,
    build_acceptance_docx,
    build_acceptance_pdf,
    build_pdf,
    build_periodic_docx,
    build_periodic_pdf,
    build_periodic_summary,
    build_work_order_docx,
    cost_for_hotspot,
    gemini_models,
    generate_acceptance_note,
    generate_periodic_note,
    generate_report,
    hotspot_record,
)
from core.ui import (
    df_show,
    disclaimer,
    image_file,
    image_url_or_file,
    img_show,
    page_intro,
    require_officer,
    safe_csv_export,
    weights_sidebar,
)

require_officer(('admin', 'officer'))
page_intro(
    'HỒ SƠ BÁO CÁO HÀNH CHÍNH',
    'Phiếu giao việc, Báo cáo định kỳ & Biên bản nghiệm thu',
    'Xuất văn bản chuẩn hành chính (PDF in ký ngay, Word .docx chỉnh sửa tiếp, CSV bảng số liệu) kèm nhận xét hỗ trợ từ Gemini AI.',
)
weights, radius = weights_sidebar()
df = db.fetch_df()
hs = build_hotspots(df, weights, radius)
custom_prices = db.get_setting('unit_prices')
key = cfg('GEMINI_API_KEY')

default_unit = st.session_state.get('officer_unit') or 'Đội Quản lý & Duy tu Đường bộ'
default_actor = st.session_state.get('officer_name') or st.session_state.get('officer_username') or ''
now_stamp = now_vn()

with st.expander('Thông tin cơ quan & chữ ký hành chính (dùng chung cho file PDF / Word)', expanded=False):
    m1, m2, m3 = st.columns(3)
    parent_org = m1.text_input('Cơ quan chủ quản', value='SỞ XÂY DỰNG / BAN QUẢN LÝ HẠ TẦNG ĐÔ THỊ', key='rep_parent_org')
    unit_name = m2.text_input('Đơn vị lập báo cáo', value=default_unit, key='rep_unit_name')
    city_name = m3.text_input('Địa danh', value='Đà Nẵng', key='rep_city')
    m4, m5 = st.columns(2)
    prepared_by = m4.text_input('Người lập phiếu / báo cáo', value=default_actor, key='rep_prepared_by')
    approver = m5.text_input('Lãnh đạo phê duyệt', value='', placeholder='Nhập họ tên lãnh đạo (để trống nếu ký tay)', key='rep_approver')

if key:
    st.caption('Hỗ trợ soạn thảo tự động: đã bật (chỉ gợi ý phần nhận xét, số liệu luôn lấy cố định từ cơ sở dữ liệu).')
else:
    st.caption('Hỗ trợ soạn thảo tự động: chưa cấu hình — hệ thống dùng biểu mẫu chuẩn cố định.')

tab_wo, tab_per, tab_acc = st.tabs([
    '1. Phiếu giao việc (1 điểm)',
    '2. Báo cáo tổng hợp định kỳ',
    '3. Biên bản nghiệm thu (Trước/Sau)',
])

# ── TAB 1: PHIẾU GIAO VIỆC & KIỂM TRA HIỆN TRƯỜNG ─────────────────────────
with tab_wo:
    if hs.empty:
        st.info('Chưa có điểm nóng đã xác minh để lập phiếu giao việc.')
    else:
        hid = st.selectbox(
            'Chọn điểm nóng cần lập phiếu',
            hs.hotspot_id.tolist(),
            format_func=lambda h: f"#{hs[hs.hotspot_id == h].priority_rank.iloc[0]} {hs[hs.hotspot_id == h].location_name.iloc[0]}",
            key='wo_hid',
        )
        row = hs[hs.hotspot_id == hid].iloc[0]
        rec = hotspot_record(row, df)
        rec['cost_estimate'] = cost_for_hotspot(rec, df, custom_prices)

        k = st.columns(4)
        k[0].metric('Hạng ưu tiên', f"#{int(row.priority_rank)}")
        k[1].metric('Điểm ưu tiên', f"{float(row.priority_score):.1f}/100")
        k[2].metric('Số phản ánh', int(row.report_count))
        k[3].metric('Dự toán sơ bộ', rec['cost_estimate']['formatted_total'])

        c_meta1, c_meta2, c_meta3 = st.columns(3)
        wo_doc_no = c_meta1.text_input('Số phiếu', value=f"Số: {now_stamp:%Y%m%d}-{int(row.priority_rank):02d}/RW-GV", key=f'wo_no_{hid}')
        wo_assignee = c_meta2.text_input('Đội / Người phụ trách', value=str(rec.get('assigned_to') or ''), placeholder='Ví dụ: Đội Duy tu Đường bộ 1', key=f'wo_as_{hid}')
        wo_due = c_meta3.text_input('Hạn hoàn thành', value=str(rec.get('due_date') or (today_vn() + timedelta(days=3))), key=f'wo_due_{hid}')

        col_img, col_info = st.columns([1, 1.3], gap='large')
        with col_img:
            img_src = image_url_or_file(rec.get('annotated_file'), public_only=False)
            if img_src:
                img_show(img_src, caption=f"Ảnh AI đánh dấu · {rec['id']}")
            else:
                st.info('Chưa tải được ảnh hiện trường của hồ sơ này.')
        with col_info:
            st.markdown(
                f"**Vị trí:** {rec['location_name']}  \n"
                f"**Mức độ cán bộ xác nhận:** {rec.get('final_level') or '-'}  \n"
                f"**Cấp đường:** {str(rec.get('road_type') or '-').replace(' (minh họa)', '')}  \n"
                f"**Phương án vật tư:** {rec['cost_estimate']['material_detail']}"
            )
            if st.button('Tạo bản thảo phiếu giao việc', type='primary', key='btn_wo_gen'):
                with st.spinner('Đang soạn bản thảo...'):
                    text, method = generate_report(rec, key)
                st.session_state.update(rep_method=method, rep_for=hid)
                st.session_state[f'rep_edit_{hid}'] = text

        edit_key = f'rep_edit_{hid}'
        if st.session_state.get('rep_for') == hid and edit_key in st.session_state:
            method = st.session_state.get('rep_method', '')
            if method.startswith('Gemini'):
                st.success('Phương pháp tạo: Biểu mẫu cố định kết hợp hỗ trợ soạn thảo tự động.')
            elif key:
                st.warning('Phương pháp tạo: ' + method)
            else:
                st.caption('Phương pháp tạo: ' + method)
            t_prev, t_edit = st.tabs(['Xem trước', 'Chỉnh sửa nội dung'])
            with t_edit:
                edited = st.text_area('Rà soát và chỉnh sửa trước khi xuất bản', key=edit_key, height=380)
            with t_prev:
                with st.container(border=True):
                    st.markdown(edited)
            if not (edited or '').strip():
                st.warning('Nội dung phiếu đang trống — vui lòng nhập nội dung hoặc bấm **Tạo bản thảo phiếu giao việc** lại trước khi phê duyệt và xuất file.')
            elif st.checkbox('Tôi đã đối chiếu số liệu và phê duyệt nội dung phiếu giao việc', key=f'wo_ok_{hid}'):
                wo_meta = {
                    'parent_org': parent_org,
                    'unit': unit_name,
                    'city': city_name,
                    'doc_no': wo_doc_no,
                    'assignee': wo_assignee,
                    'due_date': wo_due,
                    'prepared_by': prepared_by,
                    'approver': approver,
                }
                local_img = image_file(rec.get('annotated_file'))
                d1, d2, d3 = st.columns(3)
                d1.download_button(
                    'Tải Phiếu PDF (.pdf)',
                    build_pdf(rec, local_img, '', meta=wo_meta, edited_markdown=edited),
                    file_name=f"PhieuGiaoViec_{rec['id']}.pdf",
                    mime='application/pdf',
                    use_container_width=True,
                )
                d2.download_button(
                    'Tải Word chỉnh sửa (.docx)',
                    build_work_order_docx(rec, local_img, '', meta=wo_meta, edited_markdown=edited),
                    file_name=f"PhieuGiaoViec_{rec['id']}.docx",
                    mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    use_container_width=True,
                )
                d3.download_button(
                    'Tải Markdown (.md)',
                    edited.encode('utf-8'),
                    file_name=f"PhieuGiaoViec_{rec['id']}.md",
                    mime='text/markdown',
                    use_container_width=True,
                )

# ── TAB 2: BÁO CÁO TỔNG HỢP ĐỊNH KỲ ───────────────────────────────────────
with tab_per:
    today = today_vn()
    p_cols = st.columns([1.2, 1, 1, 1.3])
    preset = p_cols[0].selectbox('Kỳ báo cáo', ['30 ngày gần nhất', '7 ngày gần nhất', 'Toàn bộ dữ liệu', 'Tùy chọn ngày'], key='per_preset')
    if preset == '7 ngày gần nhất':
        d_start, d_end = today - timedelta(days=6), today
    elif preset == '30 ngày gần nhất':
        d_start, d_end = today - timedelta(days=29), today
    elif preset == 'Toàn bộ dữ liệu':
        d_start, d_end = today - timedelta(days=3650), today
    else:
        d_start = p_cols[1].date_input('Từ ngày', value=today - timedelta(days=29), key='per_start')
        d_end = p_cols[2].date_input('Đến ngày', value=today, key='per_end')
    if preset != 'Tùy chọn ngày':
        p_cols[1].text_input('Từ ngày', value=str(d_start), disabled=True, key='per_start_ro')
        p_cols[2].text_input('Đến ngày', value=str(d_end), disabled=True, key='per_end_ro')
    per_doc_no = p_cols[3].text_input('Số báo cáo', value=f"Số: {now_stamp:%Y%m}/RW-BCTH", key='per_doc_no')

    if d_start > d_end:
        st.error('Ngày bắt đầu phải nhỏ hơn hoặc bằng ngày kết thúc.')
    else:
        summary = build_periodic_summary(df, hs, d_start, d_end, custom_prices=custom_prices)
        pk = st.columns(5)
        pk[0].metric('Tiếp nhận trong kỳ', summary['total_reports'])
        pk[1].metric('Đã sửa chữa', f"{summary['fixed']} ({summary['completion_pct']}%)")
        pk[2].metric('Điểm nóng đang mở', summary['active_hotspots'])
        pk[3].metric('Quá hạn SLA', summary['overdue_count'])
        pk[4].metric('Tổng dự toán sơ bộ', summary['formatted_total_cost'])

        st.subheader('Bảng điểm nóng ưu tiên & dự toán kinh phí')
        if summary['table_df'].empty:
            st.info('Chưa có điểm hư hỏng đang mở để tổng hợp.')
        else:
            df_show(
                summary['table_df'].rename(columns={
                    'Vị trí / Tuyến đường': 'Vị trí',
                    'Số phản ánh': 'SL',
                    'Điểm ưu tiên': 'Điểm',
                    'Diện tích (m²)': 'Diện tích',
                    'Dự toán (VNĐ)': 'Dự toán',
                }),
                hide_index=True,
            )

        per_key = f'per_note_{d_start}_{d_end}'
        if st.button('Tạo tóm tắt điều hành tự động', type='primary', key='btn_per_gen'):
            with st.spinner('Đang tổng hợp nhận định điều hành...'):
                note, method = generate_periodic_note(summary, key)
            st.session_state[per_key] = note
            st.session_state['per_method'] = method

        if per_key not in st.session_state:
            note_def, _ = generate_periodic_note(summary, '')
            st.session_state[per_key] = note_def
            st.session_state['per_method'] = 'Mẫu tóm tắt từ số liệu'

        per_method = st.session_state.get('per_method', '')
        if per_method.startswith('Gemini'):
            st.success('Phương pháp tạo: Hỗ trợ soạn thảo tự động từ số liệu kỳ báo cáo.')
        elif key and 'lỗi' in per_method:
            st.warning('Phương pháp tạo: ' + per_method)
        else:
            st.caption('Phương pháp tạo: ' + per_method)

        per_note = st.text_area('Chỉnh sửa phần Nhận định & Tóm tắt điều hành trước khi xuất file', key=per_key, height=220)
        per_meta = {
            'parent_org': parent_org,
            'unit': unit_name,
            'city': city_name,
            'doc_no': per_doc_no,
            'prepared_by': prepared_by,
            'approver': approver,
        }
        b1, b2, b3 = st.columns(3)
        b1.download_button(
            'Tải Báo cáo định kỳ (.pdf)',
            build_periodic_pdf(summary, per_note, meta=per_meta),
            file_name=f"BaoCaoDinhKy_{d_start}_{d_end}.pdf",
            mime='application/pdf',
            use_container_width=True,
        )
        b2.download_button(
            'Tải Word báo cáo (.docx)',
            build_periodic_docx(summary, per_note, meta=per_meta),
            file_name=f"BaoCaoDinhKy_{d_start}_{d_end}.docx",
            mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            use_container_width=True,
        )
        b3.download_button(
            'Tải Bảng số liệu Excel (.csv)',
            safe_csv_export(summary['table_df']),
            file_name=f"BangDuToan_{d_start}_{d_end}.csv",
            mime='text/csv',
            use_container_width=True,
        )

# ── TAB 3: BIÊN BẢN NGHIỆM THU SAU SỬA CHỮA ───────────────────────────────
with tab_acc:
    fixed_df = df[df['status'] == 'fixed'].copy() if not df.empty else df
    if fixed_df.empty:
        st.info('Chưa có hồ sơ nào ở trạng thái "Đã xử lý". Hãy nghiệm thu ảnh sau sửa ở trang **Trước/sau sửa chữa** trước khi xuất biên bản.')
    else:
        fixed_df = fixed_df.sort_values('fixed_at', ascending=False, na_position='last')
        acc_id = st.selectbox(
            'Chọn hồ sơ đã sửa chữa để xuất Biên bản nghiệm thu',
            fixed_df['id'].tolist(),
            format_func=lambda rid: (
                f"{rid} — {fixed_df.loc[fixed_df['id'] == rid, 'location_name'].iloc[0]} "
                f"(sửa lúc {fixed_df.loc[fixed_df['id'] == rid, 'fixed_at'].iloc[0] or 'chưa ghi'})"
            ),
            key='acc_pick_id',
        )
        acc = acceptance_record(fixed_df[fixed_df['id'] == acc_id].iloc[0])

        ak = st.columns(4)
        ak[0].metric('Vùng AI trước sửa', acc['before_boxes'])
        ak[1].metric('Vùng AI sau sửa', acc['after_boxes'])
        ak[2].metric('Mức giảm khuyết tật', f"{acc['reduction_pct']}%")
        ak[3].metric('Diện tích ban đầu', f"{acc['damage_area_m2']:.2f} m²")

        ic1, ic2 = st.columns(2)
        with ic1:
            b_src = image_url_or_file(acc.get('annotated_file'), public_only=False)
            if b_src:
                img_show(b_src, caption=f"TRƯỚC SỬA ({acc['before_boxes']} vùng AI)")
            else:
                st.info('Chưa có ảnh trước sửa.')
        with ic2:
            a_src = image_url_or_file(acc.get('after_image_file'), public_only=False)
            if a_src:
                img_show(a_src, caption=f"SAU SỬA ({acc['after_boxes']} vùng AI)")
            else:
                st.info('Chưa có ảnh sau sửa.')

        am1, am2, am3 = st.columns(3)
        acc_doc_no = am1.text_input('Số biên bản', value=f"Số: {now_stamp:%Y%m%d}/RW-BBNT", key=f'acc_no_{acc_id}')
        acc_contractor = am2.text_input('Đơn vị thi công / Đội duy tu', value=acc['assigned_to'] or 'Đội Duy tu Đường bộ', key=f'acc_ct_{acc_id}')
        acc_conclusion = am3.selectbox(
            'Kết luận nghiệm thu',
            [
                'Đạt yêu cầu kỹ thuật, đồng ý đóng hồ sơ',
                'Đạt cơ bản, cần theo dõi bổ sung sau mưa',
                'Chưa đạt, yêu cầu đội thi công khắc phục lại',
            ],
            key=f'acc_cl_{acc_id}',
        )

        acc_key = f'acc_note_{acc_id}'
        if st.button('Gợi ý nhận xét nghiệm thu (Gemini AI)', type='primary', key='btn_acc_gen'):
            with st.spinner('Đang soạn nhận xét nghiệm thu cùng Gemini AI...' if key else 'Đang soạn nhận xét...'):
                note, method = generate_acceptance_note(acc, key)
            st.session_state[acc_key] = note
            st.session_state['acc_method'] = method

        if acc_key not in st.session_state:
            note_def, _ = generate_acceptance_note(acc, '')
            st.session_state[acc_key] = note_def
            st.session_state['acc_method'] = 'Mẫu nhận xét tự động từ đối chiếu AI'

        acc_method = st.session_state.get('acc_method', '')
        if acc_method.startswith('Gemini'):
            st.success('Phương pháp tạo nhận xét: ' + acc_method)
        elif key and 'lỗi' in acc_method:
            st.warning('Phương pháp tạo nhận xét: ' + acc_method)
        else:
            st.caption('Phương pháp tạo nhận xét: ' + acc_method)

        acc_note = st.text_area('Chỉnh sửa nhận xét nghiệm thu trước khi xuất biên bản', key=acc_key, height=180)
        acc_meta = {
            'parent_org': parent_org,
            'unit': unit_name,
            'city': city_name,
            'doc_no': acc_doc_no,
            'contractor': acc_contractor,
            'contractor_rep': acc_contractor,
            'inspector': prepared_by,
            'prepared_by': prepared_by,
            'conclusion': acc_conclusion,
        }
        before_local = image_file(acc.get('annotated_file'))
        after_local = image_file(acc.get('after_image_file'))
        e1, e2 = st.columns(2)
        e1.download_button(
            'Tải Biên bản nghiệm thu (.pdf)',
            build_acceptance_pdf(acc, before_local, after_local, acc_note, meta=acc_meta),
            file_name=f"BienBanNghiemThu_{acc['id']}.pdf",
            mime='application/pdf',
            use_container_width=True,
        )
        e2.download_button(
            'Tải Word biên bản (.docx)',
            build_acceptance_docx(acc, before_local, after_local, acc_note, meta=acc_meta),
            file_name=f"BienBanNghiemThu_{acc['id']}.docx",
            mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            use_container_width=True,
        )

disclaimer()
