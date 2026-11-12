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
from core.pin_map import add_draggable_marker
from core.service import SubmitError, submit_report
from core.ui import detector_or_stop, disclaimer, img_show, is_officer, page_intro, steps

officer = is_officer()
page_intro('GỬI PHẢN ÁNH', 'Ghi nhận tình trạng mặt đường', 'Chụp ảnh rõ mặt đường hoặc tải ảnh từ máy, xác nhận vị trí và gửi đến hàng chờ kiểm tra.')
steps('Chụp/Tải ảnh', 'Xác nhận vị trí', 'Gửi phản ánh', active=0)
st.markdown('<div class="rw-hint">🛡️ <b>An toàn trước tiên:</b> hãy đứng ở vị trí an toàn và không sử dụng camera khi đang điều khiển phương tiện. Báo cáo chưa được công khai trước khi cán bộ xác minh.</div>', unsafe_allow_html=True)

if officer:  # chỉ cán bộ thấy tùy chỉnh kỹ thuật; người dân dùng giá trị mặc định
    threshold = st.sidebar.slider('Ngưỡng tin cậy', 0.10, 0.90, 0.25, 0.05)
    with st.sidebar.expander('Nâng cao'):
        imgsz = st.selectbox('Kích thước suy luận (imgsz)', [640, 960, 1024], index=0,
                             help='Lớn hơn bắt nứt nhỏ tốt hơn nhưng chậm hơn.')
        tta = st.checkbox('Chế độ chính xác cao (TTA)', value=False)
else:
    threshold, imgsz, tta = 0.25, 640, False

# Cho phép cả người dân và cán bộ linh hoạt: Chụp bằng camera hoặc Tải ảnh từ thiết bị
st.subheader('01 · Thu thập hình ảnh hư hỏng')
st.caption('Chụp trực tiếp tại hiện trường hoặc tải ảnh có sẵn từ bộ nhớ thiết bị/thư viện ảnh.')

mode = st.radio(
    'Phương thức gửi ảnh',
    ['📷 Chụp trực tiếp bằng camera', '📁 Tải ảnh từ thiết bị / thư viện'],
    horizontal=True,
    help='Khuyến khích chụp trực tiếp tại hiện trường để có tọa độ GPS chính xác nhất.'
)

ups, cam = [], None
if mode.startswith('📷'):
    cam = st.camera_input('Chạm để mở camera và chụp ảnh mặt đường')
else:
    ups = st.file_uploader(
        'Tải ảnh JPG/PNG, tối đa 12 MB mỗi ảnh',
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        help='Có thể tải 1 hoặc nhiều ảnh chụp hiện trường.'
    ) or []

items = [(f.name, f.getvalue()) for f in ups]
if cam is not None:
    items.append(('camera.jpg', cam.getvalue()))

if not items:
    st.markdown('<div class="rw-empty"><b>Chưa có ảnh.</b><br>Hãy chụp ảnh qua camera hoặc tải ảnh từ máy để tiếp tục. Nếu camera bị chặn, kiểm tra quyền Camera của trình duyệt.</div>', unsafe_allow_html=True)
    disclaimer()
    st.stop()

from PIL import ImageOps
preview_name, preview_raw = items[0]
try:
    with Image.open(io.BytesIO(preview_raw)) as im:
        thumb = ImageOps.exif_transpose(im).convert('RGB')
        thumb.thumbnail((960, 720))
    st.image(thumb, caption='Ảnh đã chọn · ' + preview_name, use_container_width=True)
except Exception:
    st.warning('Không hiển thị được ảnh xem trước; vui lòng kiểm tra lại định dạng.')
st.caption(f'Đã có {len(items)} ảnh. Bước tiếp theo: xác nhận vị trí chính xác nơi chụp.')
st.markdown('<div class="rw-progress"><span>✓ 1. Chọn ảnh</span><span class="active">2. Xác nhận vị trí</span><span>3. Gửi phản ánh</span></div>', unsafe_allow_html=True)

st.session_state.setdefault('sub_lat', '')
st.session_state.setdefault('sub_lon', '')
st.session_state.setdefault('sub_loc_name', '')
st.session_state.setdefault('sub_gps_src', 'Nhập tay')

# Tọa độ do bản đồ (bấm hoặc kéo ghim) gửi về: áp dụng TRƯỚC khi tạo ô nhập để không vướng giới hạn của Streamlit.
_pending = st.session_state.pop('_pending_coords', None)
if _pending:
    st.session_state['sub_lat'], st.session_state['sub_lon'], st.session_state['sub_gps_src'] = _pending[:3]
    if _pending[3]:
        st.session_state['sub_loc_name'] = _pending[3]

exif_info = []
for name, raw in items:
    try:
        exif_info.append(extract_exif_gps(Image.open(io.BytesIO(raw))))
    except Exception:
        exif_info.append({'has_gps': False})
n_exif = sum(1 for e in exif_info if e.get('has_gps'))
if items:
    st.caption(f'Thông tin ảnh: {n_exif}/{len(items)} ảnh chứa EXIF GPS. EXIF chỉ là gợi ý và cần được kiểm tra trước khi lưu.')

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
browser_accuracy = None
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
                browser_accuracy = g.get('coords', {}).get('accuracy')
                if browser_accuracy is not None:
                    st.caption(f'Độ chính xác GPS do thiết bị ước tính: khoảng {browser_accuracy:.0f} m. Đây không phải sai số đã kiểm chứng.')
                    if browser_accuracy > 100:
                        st.warning('Độ chính xác ước tính vượt 100 m. Vui lòng đối chiếu lại vị trí trên bản đồ.')
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


def _norm(v):
    return str(v).strip().replace(',', '.')   # chấp nhận dấu phẩy kiểu Việt Nam


def _coords_typed():
    for k in ('sub_lat', 'sub_lon'):
        st.session_state[k] = _norm(st.session_state.get(k, ''))
    st.session_state['sub_gps_src'] = 'Nhập tay'
    try:
        la, lo = float(st.session_state['sub_lat']), float(st.session_state['sub_lon'])
    except ValueError:
        return
    if -90 <= la <= 90 and -180 <= lo <= 180:
        addr = reverse_geocode(la, lo)
        if addr:
            st.session_state['sub_loc_name'] = addr


st.subheader('02 · Xác nhận vị trí hư hỏng')
st.caption('Bật định vị trình duyệt hoặc nhập tọa độ thực tế. Tọa độ EXIF nếu có được điền làm gợi ý, không tự coi là đã xác minh.')
c1, c2 = st.columns(2)
lat_txt = c1.text_input('Vĩ độ (Latitude)', key='sub_lat', on_change=_coords_typed, placeholder='Ví dụ: 16.054407')
lon_txt = c2.text_input('Kinh độ (Longitude)', key='sub_lon', on_change=_coords_typed, placeholder='Ví dụ: 108.202167')

cur_lat = cur_lon = None
if lat_txt.strip() or lon_txt.strip():
    try:
        _la, _lo = float(_norm(lat_txt)), float(_norm(lon_txt))
        if not (-90 <= _la <= 90 and -180 <= _lo <= 180):
            raise ValueError
        cur_lat, cur_lon = _la, _lo
    except ValueError:
        st.warning('Tọa độ chưa hợp lệ: vĩ độ từ -90 đến 90, kinh độ từ -180 đến 180.')

if st.toggle('🗺️ Mở bản đồ để chọn / điều chỉnh tọa độ', value=False, key='show_location_picker'):
    st.caption('**Kéo ghim đỏ** để chỉnh hoặc **bấm vị trí mới** trên bản đồ → tọa độ & tên đường cập nhật tự động. Popup trên ghim hiển thị tọa độ realtime khi đang kéo.')
    center_pos = [cur_lat, cur_lon] if cur_lat is not None else [16.0544, 108.2022]
    zoom_lvl = 18 if cur_lat is not None else 13
    m_preview = folium.Map(location=center_pos, zoom_start=zoom_lvl, control_scale=True, tiles=None)
    
    # Lớp Google Maps Vệ tinh kết hợp đường sá (Hybrid)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google Maps Vệ tinh',
        name='Google Vệ tinh (Hybrid)',
        overlay=False,
        control=True
    ).add_to(m_preview)
    
    # Lớp Google Maps Đường sá
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr='Google Maps',
        name='Google Bản đồ đường',
        overlay=False,
        control=True
    ).add_to(m_preview)
    
    # Lớp OpenStreetMap
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='OpenStreetMap',
        overlay=False,
        control=True
    ).add_to(m_preview)
    
    folium.LayerControl().add_to(m_preview)

    if cur_lat is not None:
        add_draggable_marker(m_preview, cur_lat, cur_lon, tooltip='Kéo để chỉnh vị trí',
                             popup=st.session_state.get('sub_loc_name') or f'{cur_lat}, {cur_lon}')

    map_out = st_folium(m_preview, height=380, width=None, key='submit_picker_map',
                        returned_objects=['last_clicked'], center=center_pos, zoom=zoom_lvl)
    clicked = (map_out or {}).get('last_clicked')
    if clicked:
        pt = (round(clicked['lat'], 6), round(clicked['lng'], 6))
        if pt != st.session_state.get('_last_click'):   # chỉ xử lý điểm bấm/thả MỚI, không ghi đè tọa độ vừa nhập tay
            st.session_state['_last_click'] = pt
            if pt != (cur_lat, cur_lon):
                st.session_state['_pending_coords'] = (str(pt[0]), str(pt[1]), 'Chọn trên bản đồ', reverse_geocode(*pt))
                st.rerun()
    if cur_lat is not None:
        st.link_button('🧭 Mở vị trí này trong Google Maps', f'https://www.google.com/maps?q={cur_lat},{cur_lon}')

st.subheader('03 · Xác nhận và gửi báo cáo')
with st.form('submit_form'):
    loc = st.text_input(
        'Tên tuyến / điểm chụp (bắt buộc)',
        value=st.session_state.get('sub_loc_name', ''), max_chars=160,
        placeholder='Ví dụ: Đường Nguyễn Huệ, Phường Bến Nghé, Quận 1',
        help='Tự động cập nhật tên đường từ GPS/bản đồ. Bạn có thể chỉnh sửa lại theo thực tế.'
    )
    if officer:
        road = st.selectbox('Tầm quan trọng tuyến (thang giả định)', list(ROAD_TYPES), index=2,
                            help='Chỉ cán bộ mới xếp được; người dân không cần điền.')
    else:
        road = list(ROAD_TYPES)[2]  # mặc định "Đường khu dân cư (minh họa)"
    note = st.text_area('Ghi chú / điều kiện chụp', max_chars=600, placeholder='Ví dụ: ổ gà gần giao lộ, ảnh chụp lúc trời nắng...')
    contact = ''   # đã xóa trường liên hệ — người dân không cần
    consent = st.checkbox('Tôi đồng ý cho lưu ảnh và vị trí để cán bộ xác minh') if not officer else True
    auto_verify = False
    final_level = None
    if officer:
        auto_verify = st.checkbox('Duyệt ngay (cán bộ đã xem ảnh), bỏ qua hàng chờ')
        pick = st.selectbox('Mức độ cán bộ xác nhận', ['Theo quy tắc sơ bộ'] + LEVELS)
        final_level = None if pick.startswith('Theo') else pick
    go = st.form_submit_button('✓ Gửi phản ánh đến hàng chờ', type='primary', disabled=not items, use_container_width=True)

if go:
    det = detector_or_stop()  # Tải YOLO khi cần suy luận, không tăng thời gian mở trang ban đầu.
    for (name, raw), exif in zip(items, exif_info):
        st.divider()
        st.subheader(name)
        manual_override = st.session_state.get('sub_gps_src') in ('Nhập tay', 'Chọn trên bản đồ', 'GPS trình duyệt')
        if exif.get('has_gps') and not manual_override:
            lat, lon, src = exif['latitude'], exif['longitude'], 'EXIF GPS (chưa xác minh)'
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
                imgsz=imgsz, tta=tta,
                capture_method='camera_web' if name == 'camera.jpg' else 'upload',
                gps_accuracy_m=browser_accuracy if src == 'GPS trình duyệt' else None)
        except db.DuplicateImage as dup:
            st.warning(f'Ảnh này đã được gửi trước đó (mã {dup.existing_id}); không lưu trùng.')
            continue
        except SubmitError as err:
            st.error(str(err))
            continue
        except Exception as err:
            st.error(f'Lỗi xử lý ảnh: {err}')
            continue
        if not out['detections']:
            st.info('AI chưa phát hiện vùng nào vượt ngưỡng. Phản ánh vẫn được gửi để cán bộ kiểm tra thủ công.')
        sev = out['severity']
        img_show(out['annotated_image'])
        dmg = out.get('damage_analysis')
        if dmg and dmg['total_damage_m2'] > 0:
            a, b, c, d = st.columns(4)
            a.metric('Số vùng phát hiện', len(out['detections']))
            b.metric('Mức độ sơ bộ', sev['level'])
            c.metric('Điểm quy tắc', f"{sev['score']}/100")
            d.metric('Diện tích tổn thương', f"{dmg['total_damage_m2']:.2f} m²", help=dmg['damage_severity_desc'])
        else:
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
