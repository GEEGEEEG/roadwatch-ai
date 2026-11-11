from core.ui import page_intro
import pandas as pd
import streamlit as st

from core.config import data_dir
from core.evaluation import metrics_table, run_batch
from core.ui import detector_or_stop, disclaimer, df_show, require_officer

require_officer()
page_intro('KIỂM CHỨNG AI','Đánh giá mô hình','Phân tích các trường hợp nhận diện đúng, sai và bỏ sót từ nhãn được người kiểm thử xác nhận.')
st.caption('Đánh giá mức ảnh (có/không có hư hỏng) dựa trên nhãn do NGƯỜI gán. Không thay thế mAP trên tập có nhãn khung. '
           'Ảnh lấy từ kho mô hình có thể trùng tập huấn luyện — không gọi là kiểm thử độc lập nếu chưa xác nhận.')
folder = data_dir() / 'test_images'
ups = st.file_uploader('Thêm ảnh kiểm thử', type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
for f in ups or []:
    (folder / f.name).write_bytes(f.getvalue())
photos = sorted(p for p in folder.iterdir() if p.suffix.lower() in ('.jpg', '.jpeg', '.png'))
st.write(f'{len(photos)} ảnh trong {folder}')
det = detector_or_stop()
imgsz = st.selectbox('imgsz', [640, 960, 1024])
if st.button('Chạy mô hình', disabled=not photos):
    with st.spinner('Đang xử lý...'):
        res = run_batch(det, photos, 0.10, imgsz)
    res['Nhãn người (Có/Không)'] = ''
    st.session_state['eval_df'] = res
res = st.session_state.get('eval_df')
if res is not None:
    st.write('Gán nhãn thật cho từng ảnh (Có / Không) rồi xem chỉ số bên dưới:')
    shown = res[['image_name', 'max_conf', 'elapsed_ms', 'Nhãn người (Có/Không)']].copy()
    edited = st.data_editor(shown, hide_index=True, disabled=['image_name', 'max_conf', 'elapsed_ms'],
                            column_config={'Nhãn người (Có/Không)': st.column_config.SelectboxColumn(options=['', 'Có', 'Không'])})
    merged = res.drop(columns=['Nhãn người (Có/Không)']).merge(edited[['image_name', 'Nhãn người (Có/Không)']], on='image_name')
    table = metrics_table(merged, 'Nhãn người (Có/Không)')
    df_show(table)
    st.caption(f"Thời gian suy luận trung bình: {res.elapsed_ms.mean():.0f} ms/ảnh. Chỉ số None = chưa đủ nhãn.")
    st.download_button('Tải kết quả (.csv)', merged.drop(columns=['detections']).to_csv(index=False).encode('utf-8-sig'),
                       file_name='RoadWatch_danh_gia.csv', mime='text/csv')
disclaimer()
