import io
from datetime import datetime

import folium
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

from core import db
from core.constants import LEVELS, ROAD_TYPES, STATUS_LABELS
from core.detector import extract_exif_gps
from core.geo import reverse_geocode
from core.service import SubmitError, submit_report
from core.ui import detector_or_stop, disclaimer, img_show, is_officer

officer = is_officer()
st.header('📷 Gửi báo cáo hư hỏng mặt đường')
st.caption('Báo cáo của người dân vào **hàng chờ xác minh**; chỉ báo cáo đã duyệt mới tính vào bản đồ và xếp hạng.')
det = detector_or_stop()

if officer:  # chỉ cán bộ thấy tùy chỉnh kỹ thuật; người dân dùng giá trị mặc định
    threshold = st.sidebar.slider('Ngưỡng tin cậy', 0.10, 0.90, 0.25, 0.05)
    with st.sidebar.expander('Nâng cao'):
        imgsz = st.selectbox('Kích thước suy luận (imgsz)', [640, 960, 1024], index=0,
                             help='Lớn hơn bắt nứt nhỏ tốt hơn nhưng chậm hơn.')
        tta = st.checkbox('Chế độ chính xác cao (TTA)', value=False)
else:
    threshold, imgsz, tta = 0.25, 640, False

tab_up, tab_cam = st.tabs(['Tải ảnh (nhiều ảnh)', 'Chụp bằng điện thoại'])
with tab_up:
    ups = st.file_uploader('Ảnh JPG/PNG (≤ 12 MB mỗi ảnh)', type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
with tab_cam:
    cam = st.camera_input('Chụp mặt đường')

items = [(f.name, f.getvalue()) for f in ups or []]
if cam is not None:
    items.append(('camera.jpg', cam.getvalue()))

st.session_state.setdefault('sub_lat', '')
st.session_state.setdefault('sub_lon', '')
st.session_state.setdefault('sub_loc_name', '')
st.session_state.setdefault('sub_gps_src', 'Nhập tay')

exif_info = []
for name, raw in items:
    try:
        exif_info.append(extract_exif_gps(Image.open(io.BytesIO(raw))))
    except Exception:
        exif_info.append({'has_gps': False})
n_exif = sum(1 for e in exif_info if e.get('has_gps'))
if items:
    st.write(f'{len(items)} ảnh; {n_exif} ảnh có EXIF GPS (ảnh có GPS dùng tọa độ riêng của ảnh).')

# Tự động đọc tọa độ từ ảnh EXIF nếu có và session chưa có
if n_exif > 0 and not st.session_state.get('sub_lat'):
    first_exif = next(e for e in exif_info if e.get('has_gps'))
    e_lat, e_lon = first_exif['latitude'], first_exif['longitude']
    st.session_state['sub_lat'] = str(e_lat)
    st.session_state['sub_lon'] = str(e_lon)
    st.session_state['sub_gps_src'] = 'EXIF GPS'
    addr = reverse_geocode(e_lat, e_lon)
    if addr:
        st.session_state['sub_loc_name'] = addr

browser_loc = None
col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    if st.checkbox('📍 Lấy vị trí GPS từ thiết bị / trình duyệt'):
        try:
            from streamlit_js_eval import get_geolocation
            g = get_geolocation()
            if g and 'coords' in g:
                b_lat = round(g['coords']['latitude'], 6)
                b_lon = round(g['coords']['longitude'], 6)
                browser_loc = (b_lat, b_lon)
                st.success(f'Vị trí GPS: {b_lat}, {b_lon}')
                if st.session_state.get('_last_b_loc') != browser_loc:
                    st.session_state['_last_b_loc'] = browser_loc
                    st.session_state['sub_lat'] = str(b_lat)
                    st.session_state['sub_lon'] = str(b_lon)
                    st.session_state['sub_gps_src'] = 'GPS trình duyệt'
                    addr = reverse_geocode(b_lat, b_lon)
                    if addr:
                        st.session_state['sub_loc_name'] = addr
                    st.rerun()
            else:
                st.info('Đang chờ trình duyệt cấp quyền định vị...')
        except ImportError:
            st.warning('Chưa cài streamlit-js-eval; bạn có thể chọn vị trí trực tiếp trên bản đồ dưới đây.')

# Lấy tọa độ hiện tại để hiển thị ghim
cur_lat, cur_lon = None, None
try:
    if st.session_state.get('sub_lat') and st.session_state.get('sub_lon'):
        cur_lat = float(st.session_state['sub_lat'])
        cur_lon = float(st.session_state['sub_lon'])
except (TypeError, ValueError):
    pass

# Bản đồ tương tác trực tuyến Google Maps
with st.expander('🗺️ Bản đồ Google Maps vệ tinh: Xem ghim & Bấm chọn vị trí', expanded=False):
    st.caption('Bản đồ vệ tinh tự động ghim vị trí khi có GPS. Bạn cũng có thể **bấm trực tiếp lên bản đồ** để chọn điểm và tự động điền tên đường.')
    center_pos = [cur_lat, cur_lon] if (cur_lat and cur_lon) else [10.7769, 106.7009]
    zoom_lvl = 17 if (cur_lat and cur_lon) else 13
    m_preview = folium.Map(location=center_pos, zoom_start=zoom_lvl, control_scale=True, tiles=None)

    # Lớp Google Maps Vệ tinh kết hợp đường sá (Hybrid - chuẩn như Google Maps trong ảnh của bạn)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google Maps Vệ tinh',
        name='Google Vệ tinh (Hybrid)',
        overlay=False,
        control=True
    ).add_to(m_preview)

    # Lớp Google Maps Đường sá thông thường
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr='Google Maps',
        name='Google Bản đồ đường',
        overlay=False,
        control=True
    ).add_to(m_preview)

    # Lớp OpenStreetMap dự phòng
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='OpenStreetMap',
        overlay=False,
        control=True
    ).add_to(m_preview)

    folium.LayerControl(position='topright').add_to(m_preview)

    if cur_lat and cur_lon:
        folium.Marker(
            [cur_lat, cur_lon],
            tooltip="Vị trí đã chọn",
            popup=st.session_state.get('sub_loc_name') or f"{cur_lat}, {cur_lon}",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m_preview)

    map_out = st_folium(m_preview, height=350, width=None, key='submit_picker_map')
    if map_out and map_out.get('last_clicked'):
        clicked = map_out['last_clicked']
        c_lat = round(clicked['lat'], 6)
        c_lon = round(clicked['lng'], 6)
        if (c_lat, c_lon) != (cur_lat, cur_lon):
            st.session_state['sub_lat'] = str(c_lat)
            st.session_state['sub_lon'] = str(c_lon)
            st.session_state['sub_gps_src'] = 'Chọn trên bản đồ'
            addr = reverse_geocode(c_lat, c_lon)
            if addr:
                st.session_state['sub_loc_name'] = addr
            st.rerun()

with st.form('submit_form'):
    loc = st.text_input(
        'Tên tuyến / điểm chụp (bắt buộc)',
        value=st.session_state.get('sub_loc_name', ''),
        placeholder='Ví dụ: Đường Nguyễn Huệ, Phường Bến Nghé, Quận 1',
        help='Tự động cập nhật tên đường từ GPS/bản đồ. Bạn có thể chỉnh sửa lại theo thực tế.'
    )
    road = st.selectbox('Tầm quan trọng tuyến (thang giả định)', list(ROAD_TYPES), index=2)
    st.caption('Tọa độ vị trí (tự động cập nhật từ GPS/Bản đồ, hoặc chỉnh sửa tay):')
    c1, c2 = st.columns(2)
    lat_txt = c1.text_input('Vĩ độ (Latitude)', value=st.session_state.get('sub_lat', ''))
    lon_txt = c2.text_input('Kinh độ (Longitude)', value=st.session_state.get('sub_lon', ''))
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
            except (ValueError, TypeError):
                same = False
            src = 'GPS trình duyệt' if same else st.session_state.get('sub_gps_src', 'Nhập tay')
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
