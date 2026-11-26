import pandas as pd
import streamlit as st

from core import db
from core.ahp import (
    build_auto_ahp_matrix,
    compute_ahp_priority,
    normalize_weather_component,
)
from core.constants import ACTIVE_STATUSES
from core.corridor_hotspot import analyze_corridor_clusters
from core.cost_estimation import estimate_maintenance_cost
from core.priority import build_hotspots
from core.ui import (
    df_show,
    disclaimer,
    kpi_grid,
    page_intro,
    require_officer,
    safe_csv_export,
    weights_sidebar,
)
from core.weather import fetch_rain_forecast, rain_bonus

require_officer(('admin', 'officer'))
page_intro(
    'HỖ TRỢ RA QUYẾT ĐỊNH',
    'Ưu tiên kiểm tra & Dự toán sửa chữa',
    'Sắp xếp thứ tự ưu tiên xử lý, phát hiện đoạn đường xuống cấp liên hoàn và lập dự toán kinh phí sửa chữa.',
)
weights, radius = weights_sidebar()
use_trend = st.sidebar.checkbox('Ưu tiên điểm đang xuống cấp thêm', value=True)
use_weather = st.sidebar.checkbox('Ưu tiên ổ gà khi dự báo có mưa', value=False)

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
        st.info(f"Dự báo mưa 3 ngày tới: {rain_mm_val} mm — tự động tăng mức ưu tiên cho vị trí có ổ gà.")
        wb = {int(r.hotspot_id): rain_bonus(rain_mm_val, r.has_pothole) for r in base.itertuples()}
    else:
        st.warning('Không lấy được dự báo mưa; bỏ qua.')
hs = build_hotspots(df, weights, radius, use_trend, wb) if wb else base
custom_prices = db.get_setting('unit_prices')

tab1, tab2, tab3 = st.tabs([
    'Xếp hạng ưu tiên',
    'Đoạn đường xuống cấp',
    'Dự toán sửa chữa',
])

with tab1:
    severe_ratio = float((hs['severity_label'] == 'Cần kiểm tra sớm').mean()) if not hs.empty else 0.0
    ahp_matrix, _ahp_meta = build_auto_ahp_matrix(
        weights=weights,
        rain_mm=rain_mm_val,
        severe_ratio=severe_ratio,
    )

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
        'priority_rank', 'location_name', 'severity_label', 'report_count', 'road_type', 'priority_score',
    ]].copy()
    priority_display['road_type'] = priority_display['road_type'].astype(str).str.replace(' (minh họa)', '', regex=False)
    priority_display = priority_display.rename(columns={
        'priority_rank': 'Hạng',
        'location_name': 'Điểm hư hỏng',
        'severity_label': 'Mức độ',
        'report_count': 'Số phản ánh',
        'road_type': 'Cấp đường',
        'priority_score': 'Điểm ưu tiên',
    })
    df_show(
        priority_display,
        hide_index=True,
        column_config={
            'Hạng': st.column_config.NumberColumn('Hạng', width='small'),
            'Số phản ánh': st.column_config.NumberColumn('Số phản ánh', width='small'),
            'Cấp đường': st.column_config.TextColumn('Cấp đường', width='medium'),
            'Điểm ưu tiên': st.column_config.NumberColumn('Điểm ưu tiên', width='small'),
        },
    )
    chart_df = hs[['location_name', 'priority_score']].copy()
    chart_df['location_name'] = chart_df['location_name'].astype(str).map(
        lambda s: s if len(s) <= 24 else s[:23] + '…'
    )
    chart_df = chart_df.set_index('location_name').rename(columns={'priority_score': 'Điểm ưu tiên'})
    with st.container(border=True, key='rw_glass_pri_chart'):
        st.caption('So sánh nhanh điểm ưu tiên giữa các vị trí (thang 0–100)')
        st.bar_chart(chart_df, use_container_width=True)

with tab2:
    st.subheader('Các đoạn đường xuống cấp liên hoàn')
    st.caption('Tự động gom các điểm hư hỏng đã xác minh cách nhau ≤ 250 m. Cụm từ 3 điểm trở lên được đề xuất thảm nhựa đồng bộ.')
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
                    st.caption(f"Mã phản ánh liên quan: {', '.join(c_item['report_ids'][:8])}")
                with col_right:
                    st.metric('Dự toán sửa chữa cụm', c_item['formatted_cost'])
                    st.caption(f"Vật tư: {c_item['material_detail']}")

with tab3:
    st.subheader('Dự toán vật tư & kinh phí sửa chữa')
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

    kpi_grid([
        ('Điểm cần duy tu', f'{len(cost_rows)} điểm', 'blue', 'Đã xác minh & đang giao'),
        ('Tổng diện tích hư hỏng', f'{tot_area_sum:.2f} m²', 'amber', 'Ước tính từ ảnh AI'),
        ('Tổng kinh phí dự trù', f'{tot_all_vnd:,} VNĐ'.replace(',', '.'), 'green', 'Vật tư & nhân công'),
    ], cols=3)

    cost_table = pd.DataFrame(cost_rows)
    if not cost_table.empty:
        cost_disp = cost_table.rename(columns={
            'Vị trí điểm nóng': 'Vị trí',
            'Số hồ sơ': 'Số phản ánh',
            'Tổng cộng (VNĐ)': 'Tổng dự toán (VNĐ)',
        })[['Hạng', 'Vị trí', 'Số phản ánh', 'Diện tích (m²)', 'Phương án vật tư', 'Tổng dự toán (VNĐ)']]
        df_show(
            cost_disp,
            hide_index=True,
            column_config={
                'Hạng': st.column_config.NumberColumn('Hạng', width='small'),
                'Số phản ánh': st.column_config.NumberColumn('Số phản ánh', width='small'),
                'Diện tích (m²)': st.column_config.NumberColumn('Diện tích (m²)', width='small'),
                'Phương án vật tư': st.column_config.TextColumn('Phương án vật tư', width='medium'),
                'Tổng dự toán (VNĐ)': st.column_config.NumberColumn('Tổng dự toán (VNĐ)', width='small'),
            },
        )
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
