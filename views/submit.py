import hashlib
import io
import time

import folium
import streamlit as st
from PIL import Image, ImageOps
from streamlit_folium import st_folium

from core import db
from core.config import cfg
from core.constants import LEVELS, ROAD_TYPES, STATUS_LABELS
from core.damage_analysis import analyze_image_damage
from core.detector import encode_jpeg_bytes, extract_exif_gps, fast_prepare_rgb
from core.geo import reverse_geocode
from core.pin_map import add_draggable_marker
from core.quality import assess_quality
from core.service import SubmitError, submit_report
from core.ui import (
    add_legal_map_layers,
    confetti_celebrate,
    current_actor,
    detector_or_stop,
    disclaimer,
    img_show,
    is_officer,
    page_intro,
    qr_png,
    safe_page_link,
    steps,
)
from core.visual_dedup import image_fingerprint

MAX_CITIZEN_FILES_PER_BATCH = 3
MAX_CITIZEN_SUBMITS_PER_10M = 8


@st.cache_data(max_entries=32, ttl=600, show_spinner=False)
def _cached_exif_gps(image_digest: str, raw_bytes: bytes) -> dict:
    try:
        return extract_exif_gps(Image.open(io.BytesIO(raw_bytes)))
    except Exception:
        return {'has_gps': False}


@st.cache_data(max_entries=24, ttl=600, show_spinner=False)
def _cached_preview_analysis(image_digest: str, raw_bytes: bytes, threshold: float, imgsz: int, tta: bool):
    """Giải mã DCT 1 lần + YOLO + Phân đoạn diện tích + Nén sẵn JPEG nhẹ vào RAM đệm.
    Triệt tiêu hoàn toàn độ trễ nén PNG của Streamlit và giữ 0 ms cho mọi lần bấm GPS / Bản đồ / Gửi."""
    t0 = time.perf_counter()
    det = detector_or_stop(silent=True)
    if det is None:
        return None
    prep_img = fast_prepare_rgb(raw_bytes, max_side=1280)
    out = det.predict_image(prep_img, threshold=threshold, imgsz=imgsz, tta=tta, enhance_glare=True)
    out['damage_analysis'] = analyze_image_damage(prep_img, out['detections'])
    out['quality'] = assess_quality(prep_img)
    out['fingerprint'] = image_fingerprint(prep_img)
    out['orig_jpeg_bytes'] = encode_jpeg_bytes(prep_img, max_side=960, quality=80)
    out['annotated_jpeg_bytes'] = encode_jpeg_bytes(out['annotated_image'], max_side=1200, quality=83)
    out['total_pipeline_ms'] = round((time.perf_counter() - t0) * 1000, 1)
    return out


def _check_citizen_rate_limit(n_new: int) -> str | None:
    now = time.time()
    history = [t for t in st.session_state.get('_submit_ts', []) if now - t < 600]
    st.session_state['_submit_ts'] = history
    if len(history) + n_new > MAX_CITIZEN_SUBMITS_PER_10M:
        return (
            f'Bạn đã gửi tối đa {MAX_CITIZEN_SUBMITS_PER_10M} phản ánh trong 10 phút qua. '
            'Vui lòng đợi ít phút trước khi gửi tiếp để bảo vệ tài nguyên hệ thống.'
        )
    return None


officer = is_officer()
page_intro(
    'GỬI PHẢN ÁNH',
    'Ghi nhận tình trạng mặt đường',
    'Chụp ảnh rõ mặt đường hoặc tải ảnh từ máy, xác nhận vị trí GPS và gửi đến hàng chờ kiểm tra.',
)
steps('1. Chọn ảnh hiện trường', '2. Xác nhận tọa độ GPS', '3. AI Thẩm định & Gửi', active=0)
st.markdown(
    '<div class="rw-hint"><b>An toàn trước tiên:</b> hãy đứng ở vị trí an toàn và không sử dụng camera khi đang điều khiển phương tiện. '
    'Báo cáo sẽ được cấp mã <code>RW-...</code> để bạn tra cứu tiến độ xử lý.</div>',
    unsafe_allow_html=True,
)

if officer:
    threshold = st.sidebar.slider('Ngưỡng tin cậy', 0.10, 0.90, 0.25, 0.05)
    with st.sidebar.expander('Nâng cao'):
        imgsz = st.selectbox(
            'Kích thước suy luận (imgsz)',
            [640, 800, 960, 1024],
            index=0,
            help='640px chuẩn gốc YOLOv8 cho tốc độ nhanh nhất trên Cloud CPU; chọn 800-960px khi khảo sát vết nứt mảnh từ xa.',
        )
        tta = st.checkbox('Chế độ chính xác cao (TTA)', value=False)
else:
    threshold, imgsz, tta = 0.25, 640, False

st.subheader('01 · Thu thập hình ảnh hư hỏng')
st.caption('Chụp trực tiếp tại hiện trường hoặc tải ảnh có sẵn từ bộ nhớ thiết bị.')

mode = st.radio(
    'Phương thức gửi ảnh',
    ['Chụp trực tiếp bằng camera', 'Tải ảnh từ thiết bị / thư viện'],
    index=1,
    horizontal=True,
    help='Khuyến khích chụp trực tiếp tại hiện trường để có tọa độ GPS chính xác nhất.',
)

ups, cam = [], None
if mode.startswith('Chụp'):
    cam = st.camera_input('Chạm để mở camera và chụp ảnh mặt đường')
else:
    limit_note = '' if officer else f' (tối đa {MAX_CITIZEN_FILES_PER_BATCH} ảnh/lần)'
    ups = st.file_uploader(
        f'Tải ảnh JPG/PNG, tối đa 12 MB mỗi ảnh{limit_note}',
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        help='Có thể tải ảnh chụp hiện trường từ thư viện điện thoại.',
    ) or []
    if not officer and len(ups) > MAX_CITIZEN_FILES_PER_BATCH:
        st.warning(f'Cổng cộng đồng xử lý tối đa {MAX_CITIZEN_FILES_PER_BATCH} ảnh mỗi lượt gửi; hệ thống sẽ lấy {MAX_CITIZEN_FILES_PER_BATCH} ảnh đầu tiên.')
        ups = ups[:MAX_CITIZEN_FILES_PER_BATCH]

items = [(f.name, f.getvalue()) for f in ups]
if cam is not None:
    items.append(('camera.jpg', cam.getvalue()))

if not items:
    st.markdown(
        '<div class="rw-empty"><b>Chưa có ảnh.</b><br>'
        'Hãy chụp ảnh qua camera hoặc tải ảnh từ máy để tiếp tục. Nếu camera bị chặn, hãy kiểm tra quyền Camera trên trình duyệt HTTPS.</div>',
        unsafe_allow_html=True,
    )
    disclaimer()
    st.stop()

# ─── PREVIEW AI REAL-TIME CHO TẤT CẢ ẢNH (CÓ CACHE THEO SHA-256) ──────────
all_previews = {}
with st.spinner(f'AI đang quét & phân tích hình thái hư hỏng {len(items)} ảnh hiện trường...'):
    for idx, (p_name, p_raw) in enumerate(items):
        p_digest = hashlib.sha256(p_raw).hexdigest()
        try:
            p_out = _cached_preview_analysis(p_digest, p_raw, threshold, imgsz, tta)
            if p_out:
                all_previews[idx] = p_out
        except Exception:
            all_previews[idx] = None

_preview_out = all_previews.get(0)

if len(items) == 1:
    if _preview_out is not None:
        _dets = _preview_out['detections']
        _sev = _preview_out['severity']
        _dmg_prev = _preview_out.get('damage_analysis') or {}
        _qual_prev = _preview_out.get('quality') or {'flags': []}
        _tot_ms = _preview_out.get('total_pipeline_ms', _preview_out['elapsed_ms'])

        st.markdown(
            f'<div class="rw-preview-banner">Phân tích AI hoàn tất trong {_tot_ms} ms '
            f'(Suy luận mô hình: {_preview_out["elapsed_ms"]} ms · Đã lưu đệm 0 ms)</div>',
            unsafe_allow_html=True,
        )
        col_orig, col_ann = st.columns(2)
        with col_orig:
            st.caption('**Ảnh gốc**')
            img_show(_preview_out.get('orig_jpeg_bytes') or items[0][1], caption=items[0][0])
        with col_ann:
            st.caption(f'**AI: {_sev["level"]} · {len(_dets)} vùng phát hiện**')
            img_show(_preview_out.get('annotated_jpeg_bytes') or _preview_out['annotated_image'], caption=f'Điểm quy tắc: {_sev["score"]}/100')

        if _dmg_prev.get('total_damage_m2', 0) > 0:
            _ma, _mb, _mc, _md = st.columns(4)
            _ma.metric('Số vùng phát hiện', len(_dets))
            _mb.metric('Mức độ sơ bộ', _sev['level'])
            _mc.metric('Diện tích ước tính', f"{_dmg_prev['total_damage_m2']:.2f} m²")
            _vol_l = float(_dmg_prev.get('estimated_volume_liters', 0.0) or 0.0)
            if _vol_l > 0:
                _md.metric('Thể tích ổ gà', f'{_vol_l:.1f} L')
            else:
                _avg_c = sum(d['confidence'] for d in _dets) / len(_dets) if _dets else 0.0
                _md.metric('Độ tin cậy TB', f'{_avg_c * 100:.0f}%')
        else:
            _ma, _mb = st.columns(2)
            _ma.metric('Số vùng phát hiện', len(_dets))
            _mb.metric('Mức độ sơ bộ', _sev['level'])

        if _dets:
            _det_tags = ' · '.join(
                f"`{d['class_code']}` {d['class_name']} ({int(round(d['confidence'] * 100))}%)"
                for d in _dets[:8]
            )
            st.caption(f'**Chi tiết phát hiện AI:** {_det_tags}')

        for qf in _qual_prev.get('flags', []):
            st.warning(f'Chất lượng ảnh đầu vào: **{qf}** — bạn có thể chụp lại ảnh rõ/sáng hơn để tăng độ chính xác.')
        if not _dets:
            st.info('AI chưa phát hiện vùng hư hỏng vượt ngưỡng trong ảnh này. Bạn vẫn có thể gửi để cán bộ kiểm tra thủ công.')
    else:
        try:
            thumb_bytes = encode_jpeg_bytes(fast_prepare_rgb(items[0][1], max_side=960), max_side=960, quality=80)
            img_show(thumb_bytes, caption='Ảnh đã chọn · ' + items[0][0])
        except Exception:
            st.warning('Không hiển thị được ảnh xem trước; vui lòng kiểm tra lại định dạng.')
else:
    tot_boxes = sum(len(p['detections']) for p in all_previews.values() if p)
    tot_m2 = sum((p.get('damage_analysis') or {}).get('total_damage_m2', 0.0) for p in all_previews.values() if p)
    st.markdown(
        f'<div class="rw-preview-banner">AI đã quét &amp; dán nhãn xong <b>{len(items)} ảnh</b> hiện trường '
        f'· Phát hiện tổng cộng: <b>{tot_boxes} khuyết tật</b> (Tổng diện tích: ~<b>{tot_m2:.2f} m²</b>)</div>',
        unsafe_allow_html=True,
    )
    st.write('**Xem trước kết quả AI đã dán nhãn từng ảnh (chọn tab để xem):**')
    tabs = st.tabs([f"Ảnh {i+1} ({items[i][0][:18]})" for i in range(len(items))])
    for i, tab in enumerate(tabs):
        with tab:
            p_out = all_previews.get(i)
            p_name, p_raw = items[i]
            if p_out is not None:
                p_dets = p_out['detections']
                p_sev = p_out['severity']
                p_dmg = p_out.get('damage_analysis') or {}
                p_qual = p_out.get('quality') or {'flags': []}

                c_orig, c_ann = st.columns(2)
                with c_orig:
                    st.caption(f'**Ảnh gốc: {p_name}**')
                    img_show(p_out.get('orig_jpeg_bytes') or p_raw, caption=p_name)
                with c_ann:
                    st.caption(f'**AI đã dán nhãn ({len(p_dets)} vùng khuyết tật)**')
                    img_show(p_out.get('annotated_jpeg_bytes') or p_out['annotated_image'], caption=f'Mức độ: {p_sev["level"]} ({p_sev["score"]}/100)')

                if p_dmg.get('total_damage_m2', 0) > 0:
                    ma, mb, mc, md = st.columns(4)
                    ma.metric('Số khuyết tật', len(p_dets))
                    mb.metric('Mức độ sơ bộ', p_sev['level'])
                    mc.metric('Diện tích ước tính', f"{p_dmg['total_damage_m2']:.2f} m²")
                    p_vol = float(p_dmg.get('estimated_volume_liters', 0.0) or 0.0)
                    if p_vol > 0:
                        md.metric('Thể tích ổ gà', f'{p_vol:.1f} L')
                    else:
                        p_avg = sum(d['confidence'] for d in p_dets) / len(p_dets) if p_dets else 0.0
                        md.metric('Độ tin cậy TB', f'{p_avg * 100:.0f}%')
                else:
                    ma, mb = st.columns(2)
                    ma.metric('Số khuyết tật', len(p_dets))
                    mb.metric('Mức độ sơ bộ', p_sev['level'])

                if p_dets:
                    p_tags = ' · '.join(
                        f"`{d['class_code']}` {d['class_name']} ({int(round(d['confidence'] * 100))}%)"
                        for d in p_dets[:8]
                    )
                    st.caption(f'**Chi tiết phát hiện AI:** {p_tags}')

                for qf in p_qual.get('flags', []):
                    st.warning(f'Chất lượng ảnh **{p_name}**: {qf}')
                if not p_dets:
                    st.info(f'Ảnh {p_name} không phát hiện hư hỏng rõ rệt vượt ngưỡng.')
            else:
                st.warning(f'Không phân tích được ảnh {p_name}')

st.caption(f'Đã sẵn sàng {len(items)} ảnh. Bước tiếp theo: xác nhận vị trí chính xác nơi chụp.')
steps('1. Chọn ảnh hiện trường', '2. Xác nhận tọa độ GPS', '3. AI Thẩm định & Gửi', active=1)

st.session_state.setdefault('sub_lat', '')
st.session_state.setdefault('sub_lon', '')
st.session_state.setdefault('sub_loc_name', '')
st.session_state.setdefault('sub_gps_src', 'Nhập tay')

_pending = st.session_state.pop('_pending_coords', None)
if _pending:
    st.session_state['sub_lat'], st.session_state['sub_lon'], st.session_state['sub_gps_src'] = _pending[:3]
    if _pending[3]:
        st.session_state['sub_loc_name'] = _pending[3]

exif_info = [_cached_exif_gps(hashlib.sha256(raw).hexdigest(), raw) for _, raw in items]
n_exif = sum(1 for e in exif_info if e.get('has_gps'))
st.caption(f'Thông tin ảnh: {n_exif}/{len(items)} ảnh chứa EXIF GPS. EXIF chỉ là gợi ý và cần đối chiếu trước khi gửi.')

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
if st.checkbox('Lấy vị trí GPS trực tiếp từ thiết bị / trình duyệt'):
    try:
        from streamlit_js_eval import get_geolocation
        g = get_geolocation()
        if g and 'coords' in g:
            b_lat = round(g['coords']['latitude'], 6)
            b_lon = round(g['coords']['longitude'], 6)
            browser_loc = (b_lat, b_lon)
            browser_accuracy = g.get('coords', {}).get('accuracy')
            if browser_accuracy is not None:
                st.caption(f'Sai số GPS do thiết bị ước tính: ~{browser_accuracy:.0f} m.')
                if browser_accuracy > 100:
                    st.warning('Sai số GPS vượt 100 m (thường do mạng Wi-Fi/trong nhà). Hãy bật bản đồ bên dưới để kéo ghim đúng vị trí.')
            st.success(f'Vị trí GPS thiết bị: {b_lat}, {b_lon}')
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
            st.info('Đang chờ trình duyệt cấp quyền định vị GPS...')
    except ImportError:
        st.warning('Chưa cài streamlit-js-eval; bạn có thể chọn vị trí trực tiếp trên bản đồ dưới đây.')


def _norm(v):
    return str(v).strip().replace(',', '.')


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

if cur_lat is not None and cur_lon is not None and not str(st.session_state.get('sub_loc_name', '')).strip():
    if st.button('Tự điền tên đường từ tọa độ GPS', key='btn_retry_geocode'):
        addr_retry = reverse_geocode(cur_lat, cur_lon)
        if addr_retry:
            st.session_state['_pending_coords'] = (str(cur_lat), str(cur_lon), st.session_state.get('sub_gps_src', 'GPS trình duyệt'), addr_retry)
            st.rerun()
        else:
            st.info('Dịch vụ bản đồ chưa trả về tên đường cho tọa độ này; bạn có thể nhập tay tên tuyến bên dưới.')

if st.toggle('Mở bản đồ GIS để chọn / kéo thả ghim tọa độ', value=False, key='show_location_picker'):
    st.caption('**Kéo ghim đỏ** hoặc **chạm vào mặt đường trên bản đồ** → tọa độ và tên đường tự động cập nhật tức thì.')
    center_pos = [cur_lat, cur_lon] if cur_lat is not None else [16.0544, 108.2022]
    zoom_lvl = 18 if cur_lat is not None else 13
    m_preview = folium.Map(location=center_pos, zoom_start=zoom_lvl, control_scale=True, tiles=None)
    add_legal_map_layers(m_preview)

    if cur_lat is not None:
        add_draggable_marker(
            m_preview,
            cur_lat,
            cur_lon,
            tooltip='Kéo ghim để tinh chỉnh vị trí',
            popup=st.session_state.get('sub_loc_name') or f'{cur_lat}, {cur_lon}',
        )

    map_out = st_folium(
        m_preview,
        height=380,
        width=None,
        key='submit_picker_map',
        returned_objects=['last_clicked'],
        center=center_pos,
        zoom=zoom_lvl,
    )
    clicked = (map_out or {}).get('last_clicked')
    if clicked:
        pt = (round(clicked['lat'], 6), round(clicked['lng'], 6))
        if pt != st.session_state.get('_last_click'):
            st.session_state['_last_click'] = pt
            if pt != (cur_lat, cur_lon):
                st.session_state['_pending_coords'] = (str(pt[0]), str(pt[1]), 'Chọn trên bản đồ', reverse_geocode(*pt))
                st.rerun()
    if cur_lat is not None:
        st.link_button('Kiểm tra vị trí này trên Google Maps', f'https://www.google.com/maps?q={cur_lat},{cur_lon}')

st.subheader('03 · Xác nhận và gửi báo cáo')
if cur_lat is None:
    st.caption('Chưa có tọa độ GPS — hãy tích **Lấy vị trí GPS** hoặc **Mở bản đồ GIS** ở Bước 02 trước khi bấm gửi.')
elif not str(st.session_state.get('sub_loc_name', '')).strip():
    st.caption('Đã có tọa độ GPS, nhưng chưa tự tra được tên đường — vui lòng nhập **Tên tuyến / điểm chụp** ở ô đầu tiên bên dưới.')

with st.form('submit_form'):
    loc = st.text_input(
        'Tên tuyến / điểm chụp (bắt buộc)',
        value=st.session_state.get('sub_loc_name', ''),
        max_chars=160,
        placeholder='Ví dụ: Đường Nguyễn Văn Linh, Quận Hải Châu',
    )
    if officer:
        road = st.selectbox('Tầm quan trọng tuyến', list(ROAD_TYPES), index=2)
    else:
        road = list(ROAD_TYPES)[2]
    note = st.text_area('Ghi chú / điều kiện hiện trường', max_chars=600, placeholder='Ví dụ: ổ gà sâu sát vạch phân làn, đọng nước sau mưa...')
    consent = st.checkbox('Tôi đồng ý cho lưu ảnh và vị trí để cơ quan chuyên môn xác minh') if not officer else True
    auto_verify = False
    final_level = None
    if officer:
        auto_verify = st.checkbox('Duyệt ngay (cán bộ đã kiểm tra tại chỗ), bỏ qua hàng chờ')
        pick = st.selectbox('Mức độ cán bộ xác nhận', ['Theo quy tắc sơ bộ'] + LEVELS)
        final_level = None if pick.startswith('Theo') else pick
    go = st.form_submit_button('Gửi phản ánh đến hệ thống', type='primary', disabled=not items, use_container_width=True)

if go:
    st.session_state['sub_loc_name'] = loc
    if not officer:
        rl_err = _check_citizen_rate_limit(len(items))
        if rl_err:
            st.error(rl_err)
            st.stop()

    det = detector_or_stop()
    created_ids = []
    attempt_map = st.session_state.setdefault('_session_attempt_ts', {})
    submitted_map = st.session_state.setdefault('_session_submitted', {})

    for idx, ((name, raw), exif) in enumerate(zip(items, exif_info)):
        st.divider()
        st.subheader(name)
        manual_override = st.session_state.get('sub_gps_src') in ('Nhập tay', 'Chọn trên bản đồ', 'GPS trình duyệt')
        if exif.get('has_gps') and not manual_override:
            lat, lon, src = exif['latitude'], exif['longitude'], 'EXIF GPS (chưa xác minh)'
            captured = exif.get('datetime')
        else:
            lat, lon, captured = lat_txt, lon_txt, None
            try:
                same = browser_loc and float(_norm(lat_txt)) == browser_loc[0] and float(_norm(lon_txt)) == browser_loc[1]
            except (ValueError, TypeError):
                same = False
            src = 'GPS trình duyệt' if same else st.session_state.get('sub_gps_src', 'Nhập tay')

        reuse_out = all_previews.get(idx) if (all_previews.get(idx) is not None) else None
        raw_digest = hashlib.sha256(raw).hexdigest()
        prev_attempt_ts = attempt_map.get(raw_digest)
        already_submitted_id = submitted_map.get(raw_digest)
        has_required_inputs = bool((officer or consent) and str(loc).strip() and str(lat).strip() and str(lon).strip())
        if has_required_inputs:
            attempt_map[raw_digest] = time.time()

        try:
            with st.spinner('Đang tải ảnh lên Cloud & lưu hồ sơ phản ánh...'):
                rid, out, quality, flags = submit_report(
                    det,
                    raw,
                    name,
                    location_name=loc,
                    lat=_norm(lat),
                    lon=_norm(lon),
                    gps_source=src,
                    source='officer' if officer else 'citizen',
                    consent=consent,
                    contact='',
                    road_type=road,
                    note=note,
                    threshold=threshold,
                    status='verified' if auto_verify else 'pending',
                    actor=current_actor() if officer else '',
                    captured_at=captured,
                    final_level=final_level,
                    imgsz=imgsz,
                    tta=tta,
                    capture_method='camera_web' if name == 'camera.jpg' else 'upload',
                    gps_accuracy_m=browser_accuracy if src == 'GPS trình duyệt' else None,
                    precomputed_out=reuse_out,
                )
            created_ids.append(rid)
            submitted_map[raw_digest] = rid
            if not officer:
                st.session_state.setdefault('_submit_ts', []).append(time.time())
        except db.DuplicateImage as dup:
            was_own_recent = (
                dup.existing_id == already_submitted_id
                or dup.existing_id == st.session_state.get('_last_submitted_id')
                or (prev_attempt_ts is not None and (time.time() - prev_attempt_ts) < 300)
            )
            if was_own_recent:
                submitted_map[raw_digest] = dup.existing_id
                st.session_state['_last_submitted_id'] = dup.existing_id
                st.success(
                    f'**Phản ánh của bạn đã được ghi nhận!** Mã hồ sơ: **`{dup.existing_id}`** '
                    '(hệ thống bỏ qua thao tác bấm trùng để không tạo bản ghi lặp).'
                )
            else:
                st.warning(f'Ảnh này đã tồn tại trên hệ thống (Mã hồ sơ: **{dup.existing_id}**); không lưu trùng.')
            safe_page_link('views/track.py', label=f'Tra cứu tiến độ hồ sơ {dup.existing_id}')
            continue
        except SubmitError as err:
            attempt_map.pop(raw_digest, None)
            st.error(str(err))
            continue
        except Exception as err:
            attempt_map.pop(raw_digest, None)
            st.error(f'Lỗi xử lý ảnh: {err}')
            continue

        sev = out['severity']
        img_show(out.get('annotated_jpeg_bytes') or out['annotated_image'])
        dmg = out.get('damage_analysis') or {}
        if dmg.get('total_damage_m2', 0) > 0:
            a, b, c, d = st.columns(4)
            a.metric('Số vùng phát hiện', len(out['detections']))
            b.metric('Mức độ sơ bộ', sev['level'])
            c.metric('Điểm quy tắc', f"{sev['score']}/100")
            d.metric('Diện tích tổn thương', f"{dmg['total_damage_m2']:.2f} m²", help=dmg.get('damage_severity_desc', ''))
        else:
            a, b, c = st.columns(3)
            a.metric('Số vùng phát hiện', len(out['detections']))
            b.metric('Mức độ sơ bộ', sev['level'])
            c.metric('Điểm quy tắc', f"{sev['score']}/100")

        for q in quality['flags']:
            st.warning('Chất lượng ảnh: ' + q)
        for f in flags:
            st.warning('Cờ sàng lọc: ' + f)

        st.session_state['_last_submitted_id'] = rid
        confetti_celebrate()
        st.success(
            f'**Gửi phản ánh thành công!** Mã hồ sơ của bạn: **`{rid}`** — '
            f'Trạng thái: **{STATUS_LABELS["verified" if auto_verify else "pending"]}**.'
        )

        base_url = cfg('ROADWATCH_BASE_URL').rstrip('/')
        qr_col, link_col = st.columns([1, 3])
        with qr_col:
            track_target = f'{base_url}/track?id={rid}' if base_url else rid
            st.image(qr_png(track_target), caption='QR Mã hồ sơ', width=130)
        with link_col:
            st.info(f'Hãy lưu lại mã **`{rid}`** để tra cứu tiến độ xác minh và ảnh nghiệm thu sau sửa chữa.')
            safe_page_link('views/track.py', label=f'Mở trang Tra cứu tiến độ cho {rid}')

    if created_ids:
        steps('1. Chọn ảnh hiện trường', '2. Xác nhận tọa độ GPS', '3. AI Thẩm định & Gửi', active=2)

disclaimer()
