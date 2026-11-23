import io
from pathlib import Path
import tempfile

import pandas as pd
import streamlit as st
from PIL import Image

from core import db
from core.constants import ROAD_TYPES
from core.geo import reverse_geocode
from core.service import SubmitError, submit_report
from core.ui import current_actor, detector_or_stop, disclaimer, img_show, page_intro, require_officer
from core.video import interpolate, parse_gpx, sample_frames

require_officer()
page_intro(
    'KHẢO SÁT MỞ RỘNG',
    'Tuần đường Thông minh & Phân tích Video GPX',
    'Quét nhanh mặt đường kèm GPS tự động trên xe tuần tra (Dashcam Mode) hoặc đồng bộ tệp Video + GPX.',
)

v_tab1, v_tab2 = st.tabs([
    'Chế độ Tuần đường Trực tiếp (Smart Patrol)',
    'Phân tích Video & GPX có sẵn',
])

with v_tab1:
    st.subheader('Chế độ Tuần đường Thông minh (Smart Patrol / Dashcam Mode)')
    st.caption('Gắn điện thoại/máy tính bảng lên xe tuần tra, bật tự động lấy GPS trình duyệt và chụp quét nhanh các đoạn mặt đường.')

    col_p1, col_p2 = st.columns([1, 1])
    with col_p1:
        patrol_name = st.text_input(
            'Tuyến đường đang tuần tra',
            value=st.session_state.get('patrol_auto_addr', ''),
            placeholder='Tự động điền từ GPS hoặc nhập tên tuyến',
            key='patrol_loc_name',
        )
        patrol_road = st.selectbox('Cấp đường', list(ROAD_TYPES), index=1, key='patrol_road_type')
    with col_p2:
        patrol_thr = st.slider('Độ nhạy AI (Confidence)', 0.15, 0.85, 0.25, 0.05, key='patrol_thr')

    st.markdown('#### Định vị GPS Tuần tra')
    st.session_state.setdefault('patrol_lat', '16.0544')
    st.session_state.setdefault('patrol_lon', '108.2022')
    patrol_gps_source = 'GPS Tuần tra (nhập tay)'

    if st.checkbox('Tự động lấy tọa độ GPS thực tế từ thiết bị đang di chuyển', value=False, key='patrol_live_gps'):
        try:
            from streamlit_js_eval import get_geolocation
            g = get_geolocation(component_key='patrol_geo_eval')
            if g and 'coords' in g:
                glat = round(float(g['coords']['latitude']), 6)
                glon = round(float(g['coords']['longitude']), 6)
                patrol_gps_source = 'GPS Tuần tra (Trình duyệt)'
                if st.session_state.get('_last_patrol_gps') != (glat, glon):
                    st.session_state['_last_patrol_gps'] = (glat, glon)
                    st.session_state['patrol_lat'] = str(glat)
                    st.session_state['patrol_lon'] = str(glon)
                    addr = reverse_geocode(glat, glon)
                    if addr:
                        st.session_state['patrol_auto_addr'] = addr
                    st.rerun()
            else:
                st.info('Đang nhận tín hiệu vệ tinh GPS từ trình duyệt...')
        except ImportError:
            st.warning('Chưa cài streamlit-js-eval; vui lòng nhập tọa độ bên dưới.')

    col_gps1, col_gps2 = st.columns(2)
    p_lat = col_gps1.text_input('Vĩ độ (Latitude)', key='patrol_lat')
    p_lon = col_gps2.text_input('Kinh độ (Longitude)', key='patrol_lon')

    _gps_ok = False
    try:
        _lat_f, _lon_f = float(str(p_lat).replace(',', '.')), float(str(p_lon).replace(',', '.'))
        if 8.0 <= _lat_f <= 24.0 and 102.0 <= _lon_f <= 110.0:
            _gps_ok = True
            st.success(f'Tọa độ tuần tra hợp lệ: {_lat_f:.6f}, {_lon_f:.6f}')
        else:
            st.error('Tọa độ nằm ngoài phạm vi Việt Nam (Vĩ độ 8–24, Kinh độ 102–110).')
    except ValueError:
        st.error('Vui lòng nhập số thực hợp lệ cho Vĩ độ / Kinh độ.')

    patrol_cam = st.camera_input(
        'Chạm để quét khung hình hiện trường tiếp theo',
        key='patrol_camera',
        disabled=not _gps_ok,
    )
    if patrol_cam and _gps_ok:
        det = detector_or_stop()
        raw_b = patrol_cam.getvalue()
        im = Image.open(io.BytesIO(raw_b))
        out_p = det.predict_image(im, threshold=patrol_thr)
        dets_p = out_p['detections']

        img_show(out_p['annotated_image'], caption='Kết quả quét AI trên xe tuần tra')
        if dets_p:
            st.warning(f"Phát hiện **{len(dets_p)}** vùng hư hỏng ({out_p['severity']['level']})!")
            if st.button('Lưu ngay vào Hàng chờ Duyệt', type='primary', key='btn_save_patrol'):
                try:
                    rid, _, _, _ = submit_report(
                        det,
                        raw_b,
                        'patrol_capture.jpg',
                        location_name=patrol_name or st.session_state.get('patrol_auto_addr') or 'Tuyến tuần tra chuyên trách',
                        lat=str(_lat_f),
                        lon=str(_lon_f),
                        gps_source=patrol_gps_source,
                        source='officer',
                        consent=True,
                        road_type=patrol_road,
                        note='Ghi nhận từ Chế độ Tuần đường Thông minh (Smart Patrol)',
                        threshold=patrol_thr,
                        status='pending',
                        actor=current_actor(),
                        capture_method='camera_patrol',
                        precomputed_out=out_p,
                    )
                    st.success(f'Đã lưu hồ sơ **{rid}** vào hệ thống!')
                except Exception as err:
                    st.error(f'Lỗi lưu hồ sơ: {err}')
        else:
            st.success('Mặt đường thông thoáng, không phát hiện hư hỏng vượt ngưỡng.')

with v_tab2:
    st.caption('Tải video hành trình kèm tệp quỹ đạo GPX ghi cùng thời điểm. File video tạm sẽ tự động xóa ngay sau khi trích xuất để giải phóng bộ nhớ máy chủ.')
    vid = st.file_uploader('Video hành trình', type=['mp4', 'mov', 'avi'])
    gpx = st.file_uploader('Tệp quỹ đạo GPX', type=['gpx'])
    c = st.columns(3)
    every = c[0].number_input('Lấy 1 khung mỗi (giây)', 0.5, 30.0, 2.0, 0.5)
    offset = c[1].number_input('Độ lệch thời gian Video so với GPX (giây)', -600.0, 600.0, 0.0, 1.0)
    thr = c[2].slider('Ngưỡng tin cậy', 0.10, 0.90, 0.25, 0.05, key='video_thr')

    if st.button('Bắt đầu phân tích Video + GPX', type='primary', disabled=not (vid and gpx)):
        det = detector_or_stop()
        track = parse_gpx(gpx.getvalue())
        if len(track) < 2:
            st.error('Tệp GPX cần tối thiểu 2 điểm có mốc thời gian hợp lệ.')
            st.stop()
        tmp_path = None
        found = []
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                tmp.write(vid.getvalue())
                tmp_path = Path(tmp.name)
            bar = st.progress(0.0)
            for i, (sec, frame) in enumerate(sample_frames(tmp_path, every)):
                pos = interpolate(track, track[0][0] + offset + sec)
                out = det.predict_image(frame, threshold=thr)
                bar.progress(min(1.0, (i + 1) / 150))
                if pos is None or not out['detections']:
                    continue
                buf = io.BytesIO()
                frame.save(buf, 'JPEG', quality=90)
                found.append({
                    'sec': round(sec, 1),
                    'lat': round(pos[0], 6),
                    'lon': round(pos[1], 6),
                    'level': out['severity']['level'],
                    'boxes': len(out['detections']),
                    'jpeg': buf.getvalue(),
                    'annotated': out['annotated_image'],
                })
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)
        st.session_state['video_found'] = found

    found = st.session_state.get('video_found', [])
    if found:
        st.write(f'Phát hiện hư hỏng tại **{len(found)}** khung hình có tọa độ GPX hợp lệ:')
        st.dataframe(
            pd.DataFrame([{k: v for k, v in f.items() if k not in ('jpeg', 'annotated')} for f in found]),
            hide_index=True,
        )
        for f in found[:6]:
            img_show(f['annotated'], caption=f"{f['sec']} s — {f['level']} — {f['lat']}, {f['lon']}")
        with st.form('video_send'):
            name = st.text_input('Tên tuyến khảo sát', key='video_road_name')
            road = st.selectbox('Cấp tuyến', list(ROAD_TYPES), index=2, key='video_road_type')
            send = st.form_submit_button('Đưa toàn bộ các khung phát hiện vào Hàng chờ xác minh')
        if send:
            det = detector_or_stop()
            ok = dup = 0
            actor = current_actor()
            for f in found:
                try:
                    submit_report(
                        det,
                        f['jpeg'],
                        f"frame_{f['sec']}.jpg",
                        location_name=name,
                        lat=f['lat'],
                        lon=f['lon'],
                        gps_source='GPX + video (nội suy)',
                        source='officer',
                        consent=True,
                        road_type=road,
                        note='Khung hình trích xuất từ video khảo sát GPX',
                        threshold=thr,
                        status='pending',
                        actor=actor,
                        capture_method='video_gpx',
                    )
                    ok += 1
                except db.DuplicateImage:
                    dup += 1
                except SubmitError as e:
                    st.error(str(e))
                    break
            st.success(f'Đã gửi {ok} khung vào hàng chờ; bỏ qua {dup} khung trùng.')

disclaimer()
