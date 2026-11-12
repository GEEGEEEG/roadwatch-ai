from core.ui import page_intro
import io
import tempfile
from datetime import datetime

import pandas as pd
import streamlit as st

from core import db
from core.constants import ROAD_TYPES
from core.service import SubmitError, submit_report
from core.ui import detector_or_stop, disclaimer, img_show, require_officer
from core.video import interpolate, parse_gpx, sample_frames

require_officer()
page_intro('KHẢO SÁT MỞ RỘNG','Tuần đường & Video khảo sát','Kiểm tra khung hình từ video GPX hoặc kích hoạt chế độ tuần đường trực tiếp (Dashcam Mode).')

v_tab1, v_tab2 = st.tabs(['🚗 Chế độ Tuần đường Trực tiếp (Smart Patrol)', '🎥 Phân tích Video & GPX có sẵn'])

with v_tab2:
    st.caption('Video quay từ xe + file GPX ghi cùng lúc (ví dụ từ ứng dụng ghi hành trình). Giới hạn tải lên mặc định của Streamlit là 200 MB.')
    det = detector_or_stop()
    vid = st.file_uploader('Video', type=['mp4', 'mov', 'avi'])
    gpx = st.file_uploader('GPX', type=['gpx'])
    c = st.columns(3)
    every = c[0].number_input('Lấy 1 khung mỗi (giây)', 0.5, 30.0, 2.0, 0.5)
    offset = c[1].number_input('Video bắt đầu sau điểm GPX đầu (giây)', -600.0, 600.0, 0.0, 1.0,
                               help='0 nếu quay và ghi GPX bắt đầu cùng lúc.')
    thr = c[2].slider('Ngưỡng tin cậy', 0.10, 0.90, 0.25, 0.05, key='video_thr')
    if st.button('Phân tích video', disabled=not (vid and gpx)):
        track = parse_gpx(gpx.getvalue())
        if len(track) < 2:
            st.error('GPX cần ít nhất 2 điểm có thời gian.')
            st.stop()
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(vid.getvalue())
        found = []
        bar = st.progress(0.0)
        for i, (sec, frame) in enumerate(sample_frames(tmp.name, every)):
            pos = interpolate(track, track[0][0] + offset + sec)
            out = det.predict_image(frame, threshold=thr)
            bar.progress(min(1.0, (i + 1) / 150))
            if pos is None or not out['detections']:
                continue
            buf = io.BytesIO()
            frame.save(buf, 'JPEG', quality=92)
            found.append({'sec': round(sec, 1), 'lat': round(pos[0], 6), 'lon': round(pos[1], 6),
                          'level': out['severity']['level'], 'boxes': len(out['detections']),
                          'jpeg': buf.getvalue(), 'annotated': out['annotated_image']})
        st.session_state['video_found'] = found
    found = st.session_state.get('video_found', [])
    if found:
        st.write(f'{len(found)} khung có phát hiện (đã có tọa độ nội suy từ GPX).')
        st.dataframe(pd.DataFrame([{k: v for k, v in f.items() if k not in ('jpeg', 'annotated')} for f in found]), hide_index=True)
        for f in found[:6]:
            img_show(f['annotated'], caption=f"{f['sec']} s — {f['level']} — {f['lat']}, {f['lon']}")
        with st.form('video_send'):
            name = st.text_input('Tên tuyến khảo sát', key='video_road_name')
            road = st.selectbox('Cấp tuyến (giả định)', list(ROAD_TYPES), index=2, key='video_road_type')
            send = st.form_submit_button('Gửi các khung vào hàng chờ xác minh')
        if send:
            ok = dup = 0
            for f in found:
                try:
                    submit_report(det, f['jpeg'], f"frame_{f['sec']}.jpg", location_name=name, lat=f['lat'], lon=f['lon'],
                                  gps_source='GPX + video (nội suy)', source='officer', consent=True, road_type=road,
                                  note='Khung hình từ video khảo sát', threshold=thr, status='pending')
                    ok += 1
                except db.DuplicateImage:
                    dup += 1
                except SubmitError as e:
                    st.error(str(e)); break
            st.success(f'Đã gửi {ok} khung; bỏ qua {dup} khung trùng.')

with v_tab1:
    st.subheader('🚗 Chế độ Tuần đường Thông minh (Smart Patrol / Dashcam Mode)')
    st.caption('Gắn smartphone lên giá đỡ xe tuần tra. Chụp ảnh hiện trường liên tiếp dọc lộ trình, hệ thống AI tự quét nhận diện ổ gà/vết nứt và lưu kèm tọa độ GPS.')
    
    col_p1, col_p2 = st.columns([1, 1])
    with col_p1:
        patrol_name = st.text_input('Tuyến đường đang tuần tra', placeholder='Ví dụ: Tuyến Quốc Lộ 1A - Đoạn Km15', key='patrol_loc_name')
        patrol_road = st.selectbox('Cấp đường', list(ROAD_TYPES), index=1, key='patrol_road_type')
    with col_p2:
        patrol_thr = st.slider('Độ nhạy AI (Confidence)', 0.15, 0.85, 0.25, 0.05, key='patrol_thr')

    st.markdown('#### 📍 Tọa độ GPS điểm tuần tra')
    st.caption('Nhập tọa độ điểm đang đứng trước khi chụp. Dùng Google Maps → giữ ngón tay vào bản đồ → sao chép tọa độ.')
    col_gps1, col_gps2 = st.columns(2)
    with col_gps1:
        p_lat = st.text_input('🌐 Vĩ độ (Latitude)', value='16.0544',
                              placeholder='Ví dụ: 16.0544', key='patrol_lat',
                              help='Số dương = Bắc bán cầu. Dải hợp lệ: 8.0 – 24.0 (Việt Nam)')
    with col_gps2:
        p_lon = st.text_input('🌐 Kinh độ (Longitude)', value='108.2022',
                              placeholder='Ví dụ: 108.2022', key='patrol_lon',
                              help='Số dương = Đông bán cầu. Dải hợp lệ: 102.0 – 110.0 (Việt Nam)')

    # Validate tọa độ trước khi cho phép chụp
    _gps_ok = False
    try:
        _lat_f, _lon_f = float(p_lat), float(p_lon)
        if 8.0 <= _lat_f <= 24.0 and 102.0 <= _lon_f <= 110.0:
            _gps_ok = True
            st.success(f'✅ GPS hợp lệ: {_lat_f:.5f}, {_lon_f:.5f}')
        else:
            st.error('⚠️ Tọa độ nằm ngoài lãnh thổ Việt Nam — vui lòng kiểm tra lại.')
    except ValueError:
        st.error('⚠️ Tọa độ không hợp lệ — nhập số thực, ví dụ: 16.0544')

    patrol_cam = st.camera_input('📷 Chụp ảnh tuần tra (chạm để quét khung hình tiếp theo)',
                                 key='patrol_camera', disabled=not _gps_ok)
    if patrol_cam and _gps_ok:
        from PIL import Image as _PILImg
        raw_b = patrol_cam.getvalue()
        im = _PILImg.open(io.BytesIO(raw_b))
        out_p = det.predict_image(im, threshold=patrol_thr)
        dets_p = out_p['detections']

        img_show(out_p['annotated_image'], caption='Kết quả quét hiện trường')
        if dets_p:
            st.warning(f"🚨 Phát hiện **{len(dets_p)}** tổn thương ({out_p['severity']['level']})!")
            if st.button('📥 Lưu ngay vào Hàng chờ Duyệt', type='primary', key='btn_save_patrol'):
                try:
                    rid, _, _, _ = submit_report(
                        det, raw_b, 'patrol_capture.jpg',
                        location_name=patrol_name or 'Tuyến tuần tra chuyên trách',
                        lat=str(_lat_f), lon=str(_lon_f),
                        gps_source='GPS Tuần tra (Dashcam — nhập thủ công)',
                        source='officer', consent=True, road_type=patrol_road,
                        note='Ghi nhận tự động từ Chế độ Tuần đường Thông minh (Smart Patrol)',
                        threshold=patrol_thr, status='pending'
                    )
                    st.success(f'✅ Đã lưu hồ sơ **{rid}** vào hàng chờ xác minh!')
                except Exception as err:
                    st.error(f'Lỗi lưu: {err}')
        else:
            st.success('✅ Mặt đường thông thoáng, không phát hiện hư hỏng vượt ngưỡng.')

disclaimer()
