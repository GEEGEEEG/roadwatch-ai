from core.ui import page_intro
import streamlit as st

from core import db
from core.ahp import compute_ahp_priority, compute_ahp_weights
from core.corridor_hotspot import analyze_corridor_clusters
from core.cost_estimation import estimate_maintenance_cost
from core.priority import build_hotspots, compare_rankings
from core.ui import df_show, disclaimer, page_intro, require_officer, weights_sidebar
from core.weather import fetch_rain_forecast, rain_bonus

require_officer()
page_intro('HỖ TRỢ RA QUYẾT ĐỊNH','Ưu tiên kiểm tra','So sánh các điểm nóng dựa trên mức độ hư hỏng, tần suất phản ánh và cấp tuyến.')
weights, radius = weights_sidebar()
use_trend = st.sidebar.checkbox('Cộng điểm nếu điểm đang nặng thêm', value=True)
use_weather = st.sidebar.checkbox('Cộng điểm ổ gà khi dự báo mưa nhiều (Open-Meteo)', value=False)

df = db.fetch_df()
base = build_hotspots(df, weights, radius, use_trend)
if base.empty:
    st.info('Chưa có bản ghi đã xác minh.')
    st.stop()

wb = None
if use_weather:
    rain = fetch_rain_forecast(base.latitude.mean(), base.longitude.mean())
    if rain:
        st.info(f"Dự báo mưa 3 ngày (tại tâm khu vực): {rain['total_mm']} mm — quy tắc cộng điểm là giả định của nhóm.")
        wb = {int(r.hotspot_id): rain_bonus(rain['total_mm'], r.has_pothole) for r in base.itertuples()}
    else:
        st.warning('Không lấy được dự báo mưa; bỏ qua.')
hs = build_hotspots(df, weights, radius, use_trend, wb) if wb else base

tab1, tab2, tab3 = st.tabs([
    '📊 Xếp hạng ưu tiên & Ma trận AHP',
    '🚨 Quy hoạch Hành lang Xuống cấp (Corridors)',
    '💰 Dự toán Vật tư & Chi phí Duy tu',
])

with tab1:
    # Tính toán thêm cột điểm AHP chuẩn hóa
    ahp_scores = []
    for r in hs.itertuples():
        s_ahp, _ = compute_ahp_priority(r.severity_component, r.road_component, r.frequency_component, r.weather_bonus)
        ahp_scores.append(s_ahp)
    hs['diem_AHP'] = ahp_scores

    st.subheader('Thứ tự ưu tiên xử lý')
    df_show(hs[['priority_rank', 'location_name', 'severity_label', 'report_count', 'road_type', 'priority_score',
                'diem_AHP', 'trend_bonus', 'weather_bonus', 'ranking_reason']])
    st.bar_chart(hs.set_index('location_name')[['priority_score', 'diem_AHP']])

    with st.expander('📐 Thông tin Ma trận Đa tiêu chí AHP (Analytic Hierarchy Process)'):
        ahp_meta = compute_ahp_weights()
        w = ahp_meta['weights']
        st.markdown(f"""
        - **Mô hình toán học:** Phương pháp Saaty phân tích thứ bậc 4 tiêu chí.
        - **Trọng số chuẩn hóa:** Mức độ hư hại: **{w[0]*100:.1f}%** | Cấp đường: **{w[1]*100:.1f}%** | Tần suất phản ánh: **{w[2]*100:.1f}%** | Thời tiết/ngập: **{w[3]*100:.1f}%**
        - **Chỉ số nhất quán:** $CI = {ahp_meta['CI']}$ | **Tỷ số nhất quán:** $CR = {ahp_meta['CR']}$ ({'✅ Đạt độ nhất quán logic cao (CR < 0.1)' if ahp_meta['is_consistent'] else 'Cần hiệu chỉnh'})
        """)

    with st.expander('So sánh độ nhạy: hai bộ trọng số'):
        c = st.columns(3)
        wa = (c[0].number_input('A: mức độ', 0, 100, 50), c[1].number_input('A: tần suất', 0, 100, 30), c[2].number_input('A: tuyến', 0, 100, 20))
        c = st.columns(3)
        wb2 = (c[0].number_input('B: mức độ', 0, 100, 20), c[1].number_input('B: tần suất', 0, 100, 20), c[2].number_input('B: tuyến', 0, 100, 60))
        cmp, rho = compare_rankings(df, wa, wb2, radius)
        if not cmp.empty:
            df_show(cmp.rename(columns={'priority_rank_A': 'hạng A', 'priority_rank_B': 'hạng B', 'rank_change': 'đổi hạng (A−B)'}))
            if rho is not None:
                st.metric('Hệ số tương quan hạng (Spearman)', f'{rho:.2f}')

with tab2:
    st.subheader('Phân tích Cụm Tuyến Đường (Corridor Clustering)')
    st.caption('Thuật toán tự động nhóm các điểm hư hỏng trong cự ly 250m dọc tuyến. Cụm từ 3 điểm trở lên sẽ được phân loại là **Xuống cấp diện rộng** để chuyển sang phương án thảm lại mặt đường thay vì vá điểm lẻ.')
    corridors = analyze_corridor_clusters(df, max_distance_m=250.0, min_cluster_size=3)
    if not corridors:
        st.info('Chưa phát hiện cụm hư hỏng tập trung nào.')
    else:
        for c in corridors:
            with st.container(border=True):
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    st.markdown(f"### {c['proposal']}")
                    st.write(f"**Tuyến đại diện:** {c['location_summary']}")
                    st.write(f"**Số điểm hư hỏng tập trung:** {c['cluster_size']} điểm | **Chiều dài ảnh hưởng:** ~{c['span_length_m']} m")
                    st.caption(f"Danh sách mã hồ sơ: {', '.join(c['report_ids'][:6])}")
                with col_right:
                    st.metric('Dự toán sửa chữa cụm', c['formatted_cost'])
                    st.caption(f"Vật tư: {c['material_detail']}")

with tab3:
    st.subheader('Dự toán Khối lượng Vật tư & Chi phí Duy tu Tổng thể')
    st.caption('Định mức tham chiếu theo tiêu chuẩn duy tu giao thông đô thị Việt Nam (nhựa nguội Carboncor Asphalt, BTN hạt mịn, bê tông xi măng).')
    tot_area = float(df.get('damage_area_m2', pd.Series([0.2] * len(df))).fillna(0.2).sum())
    tot_vol = float(df.get('damage_volume_l', pd.Series([6.0] * len(df))).fillna(6.0).sum())
    overall_cost = estimate_maintenance_cost(tot_area, tot_vol)

    m1, m2, m3 = st.columns(3)
    m1.metric('Tổng diện tích hư hại ước tính', f"{overall_cost['area_m2']:.2f} m²")
    m2.metric('Vật tư đề xuất', overall_cost['material_detail'])
    m3.metric('Tổng ngân sách dự trù', overall_cost['formatted_total'])

    st.markdown("""
    #### 📋 Bảng cơ cấu chi phí tham khảo:
    | Hạng mục chi phí | Định mức áp dụng | Thành tiền (VNĐ) |
    | :--- | :--- | :--- |
    | **Vật liệu sửa chữa** | Nhựa nguội 145.000đ/bao hoặc BTN 380.000đ/m² | {:,} đ |
    | **Nhân công & Máy đầm** | Đầm cóc, nhân công vá hoàn thiện hiện trường | {:,} đ |
    | **Tổng dự toán phê duyệt** | Đã bao gồm dự phòng phí | **{:,} đ** |
    """.format(overall_cost['material_cost_vnd'], overall_cost['labor_cost_vnd'], overall_cost['total_estimate_vnd']).replace(',', '.'))

st.caption('Kết quả để thảo luận thứ tự kiểm tra và lập kế hoạch ngân sách, không phải lệnh sửa chữa tự động.')
disclaimer()
