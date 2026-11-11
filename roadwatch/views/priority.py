from core.ui import page_intro
import streamlit as st

from core import db
from core.priority import build_hotspots, compare_rankings
from core.ui import disclaimer, df_show, require_officer, weights_sidebar
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

df_show(hs[['priority_rank', 'location_name', 'severity_label', 'report_count', 'road_type', 'priority_score',
            'trend_bonus', 'weather_bonus', 'ranking_reason']])
st.bar_chart(hs.set_index('location_name')['priority_score'])

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
        st.caption('Đây là quy tắc do nhóm thiết kế; kết quả đổi hạng phụ thuộc dữ liệu thật đang có.')
st.caption('Kết quả để thảo luận thứ tự kiểm tra, không phải lệnh sửa chữa tự động.')
disclaimer()
