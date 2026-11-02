import io
from datetime import datetime

import streamlit as st
from PIL import Image

from core import db
from core.constants import LEVELS, ROAD_TYPES
from core.detector import extract_exif_gps
from core.service import SubmitError, submit_report
from core.ui import detector_or_stop, disclaimer, img_show, is_officer
from core.constants import STATUS_LABELS

officer = is_officer()
st.header('📷 Gửi báo cáo hư hỏng mặt đường')
st.caption('Báo cáo của người dân vào **hàng chờ xác minh**; chỉ báo cáo đã duyệt mới tính vào bản đồ và xếp hạng.')
det = detector_or_stop()

threshold = st.sidebar.slider('Ngưỡng tin cậy', 0.10, 0.90, 0.25, 0.05)
with st.sidebar.expander('Nâng cao'):
    imgsz = st.selectbox('Kích thước suy luận (imgsz)', [640, 960, 1024], index=0,
                         help='Lớn hơn bắt nứt nhỏ tốt hơn nhưng chậm hơn.')
    tta = st.checkbox('Chế độ chính xác cao (TTA)', value=False)

tab_up, tab_cam = st.tabs(['Tải ảnh (nhiều ảnh)', 'Chụp bằng điện thoại'])
with tab_up:
    ups = st.file_uploader('Ảnh JPG/PNG (≤ 12 MB mỗi ảnh)', type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
with tab_cam:
    cam = st.camera_input('Chụp mặt đường')

items = [(f.name, f.getvalue()) for f in ups or []]
if cam is not None:
    items.append(('camera.jpg', cam.getvalue()))

browser_loc = None
if st.checkbox('Lấy vị trí hiện tại từ trình duyệt (cần cho phép định vị)'):
    try:
        from streamlit_js_eval import get_geolocation
        g = get_geolocation()
        if g and 'coords' in g:
            browser_loc = (round(g['coords']['latitude'], 6), round(g['coords']['longitude'], 6))
            st.success(f'Vị trí trình duyệt: {browser_loc[0]}, {browser_loc[1]}')
        else:
            st.info('Đang chờ trình duyệt cấp quyền vị trí...')
    except ImportError:
        st.warning('Chưa cài streamlit-js-eval; hãy nhập tọa độ tay.')

exif_info = []
for name, raw in items:
    try:
        exif_info.append(extract_exif_gps(Image.open(io.BytesIO(raw))))
    except Exception:
        exif_info.append({'has_gps': False})
n_exif = sum(1 for e in exif_info if e.get('has_gps'))
if items:
    st.write(f'{len(items)} ảnh; {n_exif} ảnh có EXIF GPS (ảnh có GPS dùng tọa độ riêng của ảnh).')

with st.form('submit_form'):
    loc = st.text_input('Tên tuyến / điểm chụp (bắt buộc)', placeholder='Ví dụ: Đường A, gần cổng trường B')
    road = st.selectbox('Tầm quan trọng tuyến (thang giả định)', list(ROAD_TYPES), index=2)
    st.caption('Tọa độ dùng cho ảnh KHÔNG có EXIF GPS (không dùng tọa độ mẫu):')
    c1, c2 = st.columns(2)
    lat_txt = c1.text_input('Vĩ độ', value=str(browser_loc[0]) if browser_loc else '')
    lon_txt = c2.text_input('Kinh độ', value=str(browser_loc[1]) if browser_loc else '')
    note = st.text_area('Ghi chú / điều kiện chụp')
    contact = st.text_input('Liên hệ (tùy chọn, chỉ cán bộ xem)') if not officer else ''
    consent = st.checkbox('Tôi đồng ý cho lưu ảnh và vị trí để cán bộ xác minh') if not officer else True
    auto_verify = False
    final_level = None
    if officer:
        auto_verify = st.checkbox('Duyệt ngay (cán bộ đã xem ảnh), bỏ qua hàng chờ')
        pick = st.selectbox('Mức độ cán bộ xác nhận', ['Theo quy tắc sơ bộ'] + LEVELS)
        final_level = None if pick.startswith('Theo') else pick
    go = st.form_submit_button('Gửi báo cáo', disabled=not items)

if go:
    for (name, raw), exif in zip(items, exif_info):
        st.divider()
        st.subheader(name)
        if exif.get('has_gps'):
            lat, lon, src = exif['latitude'], exif['longitude'], 'EXIF GPS'
            captured = exif.get('datetime')
        else:
            lat, lon, captured = lat_txt, lon_txt, None
            try:
                same = browser_loc and float(lat_txt) == browser_loc[0] and float(lon_txt) == browser_loc[1]
            except ValueError:
                same = False
            src = 'GPS trình duyệt' if same else 'Nhập tay'
        try:
            rid, out, quality, flags = submit_report(
                det, raw, name, location_name=loc, lat=lat, lon=lon, gps_source=src,
                source='officer' if officer else 'citizen', consent=consent, contact=contact, road_type=road,
                note=note, threshold=threshold, status='verified' if auto_verify else 'pending',
                actor='cán bộ' if officer else '', captured_at=captured, final_level=final_level,
                imgsz=imgsz, tta=tta)
        except db.DuplicateImage as dup:
            st.warning(f'Ảnh này đã được gửi trước đó (mã {dup.existing_id}); không lưu trùng.')
            continue
        except SubmitError as err:
            st.error(str(err))
            continue
        except Exception as err:
            st.error(f'Lỗi xử lý ảnh: {err}')
            continue
        sev = out['severity']
        img_show(out['annotated_image'])
        a, b, c = st.columns(3)
        a.metric('Số vùng phát hiện', len(out['detections']))
        b.metric('Mức độ sơ bộ', sev['level'])
        c.metric('Điểm quy tắc', f"{sev['score']}/100")
        for q in quality['flags']:
            st.warning('Chất lượng ảnh: ' + q + ' — kết quả nhận diện có thể kém tin cậy.')
        for f in flags:
            st.warning('Cờ kiểm tra: ' + f)
        st.success(f'Đã lưu {rid} — trạng thái: {STATUS_LABELS["verified" if auto_verify else "pending"]}.')
disclaimer()
