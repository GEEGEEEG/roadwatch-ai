from core.ui import page_intro
import streamlit as st

from core import db
from core.backup import make_backup, restore_backup
from core.config import cfg, data_dir, model_path
from core.notify import send_telegram, telegram_configured
from core.priority import build_hotspots
from core.ui import df_show, disclaimer, require_officer, safe_csv_export
from datetime import datetime

require_officer()
page_intro('QUẢN TRỊ HỆ THỐNG','Cấu hình & sao lưu','Theo dõi dữ liệu và tạo bản sao lưu trước khi khôi phục hoặc chỉnh sửa cấu hình.')
df = db.fetch_df()
st.write(f'Thư mục dữ liệu: `{data_dir()}` — {len(df)} bản ghi.')
st.write(f'Mô hình: `{model_path()}` — {"có" if model_path().is_file() else "THIẾU"}')
st.write('Gemini: ' + ('đã cấu hình' if cfg('GEMINI_API_KEY') else 'chưa') + ' | Telegram: ' + ('đã cấu hình' if telegram_configured() else 'chưa'))
if telegram_configured() and st.button('Gửi thử Telegram'):
    st.success('OK') if send_telegram('RoadWatch: tin nhắn thử') else st.error('Gửi thất bại')

if not df.empty:
    df_show(df.drop(columns=['detections_json']))
    st.download_button('Tải toàn bộ bản ghi (.csv)', safe_csv_export(df.drop(columns=['detections_json'])),
                       file_name='RoadWatch_all_reports.csv', mime='text/csv')
st.subheader('Sao lưu / khôi phục')
st.download_button('Tải bản sao lưu (.zip: CSDL + ảnh)', make_backup(),
                   file_name=f"roadwatch_backup_{datetime.now():%Y%m%d_%H%M}.zip", mime='application/zip')
up = st.file_uploader('Khôi phục từ file .zip', type=['zip'])
if up and st.button('Khôi phục (ghi đè dữ liệu cùng tên)'):
    try:
        restore_backup(up.getvalue())
        st.success('Đã khôi phục.')
    except Exception as exc:
        st.error(f'Không khôi phục được: {exc}')
disclaimer()
