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
st.header('🎥 Khảo sát bằng video + GPX')
st.caption('Video quay từ xe + file GPX ghi cùng lúc (ví dụ từ ứng dụng ghi hành trình). Giới hạn tải lên mặc định của Streamlit là 200 MB.')
det = detector_or_stop()
vid = st.file_uploader('Video', type=['mp4', 'mov', 'avi'])
gpx = st.file_uploader('GPX', type=['gpx'])
c = st.columns(3)
every = c[0].number_input('Lấy 1 khung mỗi (giây)', 0.5, 30.0, 2.0, 0.5)
offset = c[1].number_input('Video bắt đầu sau điểm GPX đầu (giây)', -600.0, 600.0, 0.0, 1.0,
                           help='0 nếu quay và ghi GPX bắt đầu cùng lúc.')
thr = c[2].slider('Ngưỡng tin cậy', 0.10, 0.90, 0.25, 0.05)
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
        name = st.text_input('Tên tuyến khảo sát')
        road = st.selectbox('Cấp tuyến (giả định)', list(ROAD_TYPES), index=2)
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
disclaimer()
