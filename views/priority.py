import pandas as pd
import streamlit as st

from core import db
from core.ahp import (
    build_pairwise_matrix,
    compute_ahp_priority,
    compute_ahp_weights,
    normalize_weather_component,
)
from core.constants import ACTIVE_STATUSES
from core.corridor_hotspot import analyze_corridor_clusters
from core.cost_estimation import estimate_maintenance_cost
from core.priority import build_hotspots, compare_rankings
from core.ui import (
    current_actor,
    df_show,
    disclaimer,
    page_intro,
    require_officer,
    safe_csv_export,
    weights_sidebar,
)
from core.weather import fetch_rain_forecast, rain_bonus

require_officer(('admin', 'officer'))
page_intro(
    'HỖ TRỢ RA QUYẾT ĐỊNH',
    'Ưu tiên kiểm tra & Dự toán duy tu',
    'So sánh điểm nóng theo trọng số thực nghiệm, ma trận toán học AHP chuẩn Saaty và lập dự toán ngân sách.',
)
weights, radius = weights_sidebar()
use_trend = st.sidebar.checkbox('Cộng điểm nếu điểm đang nặng thêm', value=True)
use_weather = st.sidebar.checkbox('Cộng điểm ổ gà khi dự báo mưa nhiều (Open-Meteo)', value=False)

df = db.fetch_df()
base = build_hotspots(df, weights, radius, use_trend)
if base.empty:
    st.info('Chưa có bản ghi đã xác minh.')
    st.stop()

wb = None
rain_mm_val = None
if use_weather:
    rain = fetch_rain_forecast(base.latitude.mean(), base.longitude.mean())
    if rain:
        rain_mm_val = rain['total_mm']
        st.info(f"Dự báo mưa 3 ngày (tại tâm khu vực): {rain_mm_val} mm — cộng tối đa +5 điểm cho vị trí có ổ gà.")
        wb = {int(r.hotspot_id): rain_bonus(rain_mm_val, r.has_pothole) for r in base.itertuples()}
    else:
        st.warning('Không lấy được dự báo mưa; bỏ qua.')
hs = build_hotspots(df, weights, radius, use_trend, wb) if wb else base

saved_pairs = db.get_setting('ahp_pairs') or {
    'c12': 2.0, 'c13': 3.0, 'c14': 4.0, 'c23': 2.0, 'c24': 3.0, 'c34': 2.0
}
custom_prices = db.get_setting('unit_prices')

tab1, tab2, tab3 = st.tabs([
    'Xếp hạng & AHP',
    'Hành lang xuống cấp',
    'Dự toán duy tu',
])

with tab1:
    with st.expander('Hiệu chỉnh Ma trận AHP (Thang Saaty 1/9–9 · CR < 0.10)', expanded=False):
        st.caption('Điều chỉnh tỷ lệ ưu tiên tương đối giữa 4 tiêu chí ($C_1$: Mức độ hư hại, $C_2$: Cấp đường, $C_3$: Tần suất phản ánh, $C_4$: Thời tiết/ngập):')
        p_cols1 = st.columns(3)
        c12 = p_cols1[0].slider('C1 so với C2 (Nghiêm trọng / Cấp đường)', 0.2, 9.0, float(saved_pairs.get('c12', 2.0)), 0.5)
        c13 = p_cols1[1].slider('C1 so với C3 (Nghiêm trọng / Tần suất)', 0.2, 9.0, float(saved_pairs.get('c13', 3.0)), 0.5)
        c14 = p_cols1[2].slider('C1 so với C4 (Nghiêm trọng / Thời tiết)', 0.2, 9.0, float(saved_pairs.get('c14', 4.0)), 0.5)
        p_cols2 = st.columns(3)
        c23 = p_cols2[0].slider('C2 so với C3 (Cấp đường / Tần suất)', 0.2, 9.0, float(saved_pairs.get('c23', 2.0)), 0.5)
        c24 = p_cols2[1].slider('C2 so với C4 (Cấp đường / Thời tiết)', 0.2, 9.0, float(saved_pairs.get('c24', 3.0)), 0.5)
        c34 = p_cols2[2].slider('C3 so với C4 (Tần suất / Thời tiết)', 0.2, 9.0, float(saved_pairs.get('c34', 2.0)), 0.5)

        ahp_matrix = build_pairwise_matrix(c12, c13, c14, c23, c24, c34)
        ahp_meta = compute_ahp_weights(ahp_matrix)
        w = ahp_meta['weights']

        if ahp_meta['is_consistent']:
            st.success(
                f"**Ma trận nhất quán logic ($CR = {ahp_meta['CR']} < 0.10$, $\\lambda_{{max}} = {ahp_meta['lambda_max']}$, $CI = {ahp_meta['CI']}$)** — "
                f"Trọng số: **C1={w[0]*100:.1f}% · C2={w[1]*100:.1f}% · C3={w[2]*100:.1f}% · C4={w[3]*100:.1f}%**"
            )
        else:
            st.error(
                f"**Ma trận mâu thuẫn bắc cầu ($CR = {ahp_meta['CR']} \\ge 0.10$)!** "
                "Theo chuẩn Saaty, vui lòng điều chỉnh lại các tỷ lệ so sánh cặp cho nhất quán trước khi lưu."
            )

        btn_save_ahp, btn_reset_ahp = st.columns([1, 1])
        if btn_save_ahp.button('Lưu bộ ma trận AHP này làm mặc định', disabled=not ahp_meta['is_consistent']):
            db.set_setting(
                'ahp_pairs',
                {'c12': c12, 'c13': c13, 'c14': c14, 'c23': c23, 'c24': c24, 'c34': c34},
                actor=current_actor(),
            )
            st.success('Đã lưu cấu hình ma trận AHP lên cơ sở dữ liệu!')
        if btn_reset_ahp.button('Khôi phục ma trận Saaty tiêu chuẩn'):
            db.set_setting(
                'ahp_pairs',
                {'c12': 2.0, 'c13': 3.0, 'c14': 4.0, 'c23': 2.0, 'c24': 3.0, 'c34': 2.0},
                actor=current_actor(),
            )
            st.rerun()

    ahp_scores = []
    for r in hs.itertuples():
        w_comp = normalize_weather_component(r.weather_bonus, rain_mm=rain_mm_val, has_pothole=bool(r.has_pothole))
        s_ahp, _ = compute_ahp_priority(
            r.severity_component,
            r.road_component,
            r.frequency_component,
            w_comp,
            custom_matrix=ahp_matrix,
        )
        ahp_scores.append(s_ahp)
    hs['diem_AHP'] = ahp_scores

    st.subheader('Bảng xếp hạng ưu tiên xử lý')
    priority_display = hs[[
        'priority_rank', 'location_name', 'severity_label', 'report_count', 'road_type',
        'priority_score', 'diem_AHP', 'trend_bonus', 'weather_bonus', 'ranking_reason',
    ]].copy()
    priority_display['road_type'] = priority_display['road_type'].astype(str).str.replace(' (minh họa)', '', regex=False)
    priority_display = priority_display.rename(columns={
        'priority_rank': 'Hạng',
        'location_name': 'Điểm hư hỏng',
        'severity_label': 'Mức độ',
        'report_count': 'SL',
        'road_type': 'Cấp đường',
        'priority_score': 'Ưu tiên',
        'diem_AHP': 'AHP',
        'trend_bonus': 'Xu hướng',
        'weather_bonus': 'Mưa',
        'ranking_reason': 'Lý do xếp hạng',
    })
    df_show(
        priority_display,
        hide_index=True,
        column_config={
            'Hạng': st.column_config.NumberColumn('Hạng', width='small'),
            'SL': st.column_config.NumberColumn('SL', width='small'),
            'Cấp đường': st.column_config.TextColumn('Cấp đường', width='medium'),
            'Ưu tiên': st.column_config.NumberColumn('Ưu tiên', width='small'),
            'AHP': st.column_config.NumberColumn('AHP', width='small'),
        },
    )
    chart_df = hs.set_index('location_name')[['priority_score', 'diem_AHP']].rename(
        columns={'priority_score': 'Điểm ưu tiên', 'diem_AHP': 'Điểm AHP'}
    )
    st.bar_chart(chart_df)

    with st.expander('Kiểm tra độ ổn định xếp hạng (Spearman)'):
        c = st.columns(3)
        wa = (c[0].number_input('A: mức độ', 0, 100, 50), c[1].number_input('A: tần suất', 0, 100, 30), c[2].number_input('A: tuyến', 0, 100, 20))
        c = st.columns(3)
        wb2 = (c[0].number_input('B: mức độ', 0, 100, 20), c[1].number_input('B: tần suất', 0, 100, 20), c[2].number_input('B: tuyến', 0, 100, 60))
        cmp, rho = compare_rankings(df, wa, wb2, radius)
        if not cmp.empty:
            df_show(cmp.rename(columns={'priority_rank_A': 'hạng A', 'priority_rank_B': 'hạng B', 'rank_change': 'đổi hạng (A−B)'}), hide_index=True)
            if rho is not None:
                st.metric('Hệ số tương quan hạng (Spearman ρ)', f'{rho:.2f}')

with tab2:
    st.subheader('Phân tích Cụm Tuyến Đường (Corridor Clustering)')
    st.caption('Tự động liên kết các điểm hư hỏng đã xác minh cách nhau ≤ 250m. Cụm ≥ 3 điểm được gắn cảnh báo **Xuống cấp diện rộng** để chuyển sang phương án thảm nhựa đồng bộ.')
    corridors = analyze_corridor_clusters(df, max_distance_m=250.0, min_cluster_size=3)
    if not corridors:
        st.info('Chưa phát hiện cụm hư hỏng tập trung nào.')
    else:
        for c_idx, c_item in enumerate(corridors):
            with st.container(border=True, key=f'rw_glass_corridor_{c_idx}'):
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    st.markdown(f"### {c_item['proposal']}")
                    st.write(f"**Tuyến đại diện:** {c_item['location_summary']}")
                    st.write(f"**Quy mô:** {c_item['cluster_size']} điểm | **Chiều dài ảnh hưởng:** ~{c_item['span_length_m']} m | **Diện tích:** {c_item['total_area_m2']:.2f} m²")
                    st.caption(f"Danh sách mã hồ sơ: {', '.join(c_item['report_ids'][:8])}")
                with col_right:
                    st.metric('Dự toán sửa chữa cụm', c_item['formatted_cost'])
                    st.caption(f"Vật tư: {c_item['material_detail']}")

with tab3:
    st.subheader('Dự toán Khối lượng Vật tư & Kinh phí Duy tu (Chỉ tính điểm Đã xác minh / Đang giao)')
    st.caption('Tính toán chi tiết theo từng điểm nóng đang hoạt động, không tính nhầm hồ sơ đã đóng hoặc từ chối.')

    active_df = df[df.status.isin(ACTIVE_STATUSES)].copy()
    cost_rows = []
    tot_mat_vnd = 0
    tot_lab_vnd = 0
    tot_all_vnd = 0
    tot_area_sum = 0.0

    for h in hs.itertuples():
        members = active_df[active_df.id.isin(h.member_ids)]
        h_area = float(members['damage_area_m2'].fillna(0.15).clip(lower=0.05).sum()) if not members.empty else 0.15
        h_vol = float(members['damage_volume_l'].fillna(5.0).clip(lower=0.0).sum()) if not members.empty else 5.0
        est = estimate_maintenance_cost(h_area, h_vol, point_count=len(members) or 1, custom_prices=custom_prices)
        tot_area_sum += est['area_m2']
        tot_mat_vnd += est['material_cost_vnd']
        tot_lab_vnd += est['labor_cost_vnd']
        tot_all_vnd += est['total_estimate_vnd']
        cost_rows.append({
            'Hạng': h.priority_rank,
            'Vị trí điểm nóng': h.location_name,
            'Số hồ sơ': len(members),
            'Diện tích (m²)': est['area_m2'],
            'Phương án vật tư': est['material_detail'],
            'Chi phí vật tư (VNĐ)': est['material_cost_vnd'],
            'Nhân công & máy (VNĐ)': est['labor_cost_vnd'],
            'Tổng cộng (VNĐ)': est['total_estimate_vnd'],
        })

    m1, m2, m3 = st.columns(3)
    m1.metric('Tổng số điểm nóng cần duy tu', f'{len(cost_rows)} điểm')
    m2.metric('Tổng diện tích hư hại hoạt động', f'{tot_area_sum:.2f} m²')
    m3.metric('Tổng kinh phí dự trù', f'{tot_all_vnd:,} VNĐ'.replace(',', '.'))

    cost_table = pd.DataFrame(cost_rows)
    if not cost_table.empty:
        df_show(cost_table, hide_index=True)
        st.download_button(
            'Xuất bảng dự toán chi tiết (.csv)',
            safe_csv_export(cost_table),
            file_name='RoadWatch_du_toan_duy_tu.csv',
            mime='text/csv',
        )

    st.markdown(
        """
    #### Tổng hợp cơ cấu ngân sách dự kiến:
    | Hạng mục chi phí | Thuyết minh tính toán | Thành tiền (VNĐ) |
    | :--- | :--- | ---: |
    | **Vật liệu mặt đường** | Nhựa nguội Carboncor (< 0.5 m²) hoặc thảm BTN nóng (≥ 0.5 m²) | {:,} đ |
    | **Nhân công & Ca máy thi công** | Tính theo số vị trí thực tế (có chiết khấu theo cụm) | {:,} đ |
    | **Tổng dự toán đề xuất** | Chỉ tính các điểm đã xác minh và đang giao duy tu | **{:,} đ** |
    """.format(tot_mat_vnd, tot_lab_vnd, tot_all_vnd).replace(',', '.')
    )

st.caption('Số liệu phục vụ lập kế hoạch kiểm tra và dự trù vật tư sơ bộ; dự toán chính thức căn cứ biên bản đo đạc hiện trường.')
disclaimer()
