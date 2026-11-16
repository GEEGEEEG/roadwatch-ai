from pathlib import Path

import streamlit as st

from core.config import data_dir
from core.evaluation import metrics_table, run_batch
from core.ui import detector_or_stop, df_show, disclaimer, page_intro, require_officer, safe_csv_export

require_officer(('admin', 'officer'))
page_intro('KIỂM CHỨNG MÔ HÌNH AI', 'Đánh giá thực nghiệm mô hình', 'Phân tích TP/FP/FN/TN, Precision, Recall và F1 ở nhiều ngưỡng tin cậy trên tập kiểm thử độc lập.')
st.caption(
    'Đánh giá cấp độ ảnh (Có / Không có hư hỏng) đối chiếu với nhãn chuẩn do người kiểm định gán. '
    'Phục vụ báo cáo thực nghiệm khoa học minh bạch.'
)
folder = data_dir() / 'test_images'
ups = st.file_uploader('Thêm ảnh kiểm thử độc lập', type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
for f in ups or []:
    (folder / Path(f.name).name).write_bytes(f.getvalue())
photos = sorted(p for p in folder.iterdir() if p.suffix.lower() in ('.jpg', '.jpeg', '.png'))
st.write(f'Hiện có **{len(photos)}** ảnh kiểm thử trong `{folder}`.')

imgsz = st.selectbox('Kích thước suy luận (imgsz)', [640, 800, 960, 1024], index=1)
if st.button('🧪 Chạy đánh giá hàng loạt', type='primary', disabled=not photos):
    det = detector_or_stop()
    with st.spinner('Đang chạy mô hình qua tập ảnh kiểm thử...'):
        res = run_batch(det, photos, 0.10, imgsz)
    res['Nhãn người (Có/Không)'] = ''
    st.session_state['eval_df'] = res

res = st.session_state.get('eval_df')
if res is not None:
    st.write('Gán nhãn thực tế cho từng ảnh (`Có` / `Không`) để tính bảng chỉ số bên dưới:')
    shown = res[['image_name', 'max_conf', 'elapsed_ms', 'Nhãn người (Có/Không)']].copy()
    edited = st.data_editor(
        shown,
        hide_index=True,
        disabled=['image_name', 'max_conf', 'elapsed_ms'],
        column_config={'Nhãn người (Có/Không)': st.column_config.SelectboxColumn(options=['', 'Có', 'Không'])},
    )
    merged = res.drop(columns=['Nhãn người (Có/Không)']).merge(edited[['image_name', 'Nhãn người (Có/Không)']], on='image_name')
    table = metrics_table(merged, 'Nhãn người (Có/Không)')
    df_show(table, hide_index=True)
    st.caption(f"Thời gian suy luận trung bình: **{res.elapsed_ms.mean():.1f} ms/ảnh**.")
    st.download_button(
        '⬇️ Tải bảng kết quả thực nghiệm (.csv)',
        safe_csv_export(merged.drop(columns=['detections'])),
        file_name='RoadWatch_danh_gia_mo_hinh.csv',
        mime='text/csv',
    )
disclaimer()
