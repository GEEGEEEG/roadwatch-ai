"""Luồng gửi báo cáo tốc độ cao (v5.0 Turbo):
- Tái sử dụng trọn vẹn kết quả AI, ảnh JPEG đã nén và vector thị giác từ bước Preview (0 ms tính lại).
- Nén thông minh ảnh chụp điện thoại > 1.2 MB về JPEG 1600px (~220 KB) nhưng vẫn giữ SHA-256 gốc chống trùng.
- Tải song song 2 luồng (Parallel Upload) lên Supabase Storage + truy vấn cột siêu nhẹ `fetch_screening_df`.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
import logging
from datetime import datetime

from PIL import Image

from . import db
from .config import data_dir, now_vn
from .constants import ACTIVE_STATUSES, DUP_FLAG_M, ROAD_TYPES
from .damage_analysis import analyze_image_damage
from .detector import encode_jpeg_bytes, fast_prepare_rgb
from .geo import nearby_points
from .priority import final_score
from .quality import assess_quality, screening_flags
from .visual_dedup import check_visual_duplicate, image_fingerprint

log = logging.getLogger(__name__)
MAX_BYTES = 12 * 1024 * 1024
SMART_COMPRESS_THRESHOLD = 1_200_000  # > 1.2 MB thì nén tối ưu lưu trữ Cloud


class SubmitError(Exception):
    pass


def submit_report(
    detector,
    raw: bytes,
    filename: str,
    *,
    location_name,
    lat,
    lon,
    gps_source,
    source='citizen',
    consent=False,
    contact='',
    road_type=None,
    note='',
    threshold=0.25,
    status='pending',
    actor='',
    captured_at=None,
    final_level=None,
    imgsz=640,
    tta=False,
    capture_method='upload',
    gps_accuracy_m=None,
    precomputed_out: dict | None = None,
):
    if len(raw) > MAX_BYTES:
        raise SubmitError('Ảnh vượt quá 12 MB.')
    if source == 'citizen' and not consent:
        raise SubmitError('Cần đồng ý cho phép lưu ảnh và vị trí trước khi gửi.')
    if not str(location_name).strip():
        raise SubmitError('Thiếu tên tuyến / điểm chụp.')
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError) as exc:
        raise SubmitError('Vĩ độ/kinh độ không hợp lệ. Không lưu vị trí bịa đặt.') from exc
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise SubmitError('Vĩ độ/kinh độ ngoài phạm vi hợp lệ.')

    road_type = road_type if road_type in ROAD_TYPES else 'Đường khu dân cư (minh họa)'
    digest = hashlib.sha256(raw).hexdigest()
    existing = db.find_by_hash(digest)
    if existing:
        raise db.DuplicateImage(existing)

    pil: Image.Image | None = None
    if precomputed_out is not None:
        out = dict(precomputed_out)
    else:
        try:
            pil = fast_prepare_rgb(raw, max_side=1280)
        except Exception as exc:
            raise SubmitError('Không đọc được ảnh (cần JPG/PNG hợp lệ).') from exc
        out = detector.predict_image(pil, threshold=threshold, imgsz=imgsz, tta=tta)

    sev, dets = out['severity'], out['detections']
    if pil is None and ('quality' not in out or 'damage_analysis' not in out or 'fingerprint' not in out):
        try:
            pil = fast_prepare_rgb(raw, max_side=1280)
        except Exception as exc:
            raise SubmitError('Không đọc được ảnh (cần JPG/PNG hợp lệ).') from exc

    quality = out.get('quality') or assess_quality(pil)
    damage_info = out.get('damage_analysis') or analyze_image_damage(pil, dets)
    fp = out.get('fingerprint') or image_fingerprint(pil)
    out['damage_analysis'] = damage_info
    out['quality'] = quality
    out['fingerprint'] = fp

    now = now_vn()
    df_screen = db.fetch_screening_df()
    flags = list(screening_flags(df_screen, lat, lon, now, len(dets), quality['flags']))

    for near_id, near_m, _ in nearby_points(df_screen, lat, lon, DUP_FLAG_M, ACTIVE_STATUSES)[:1]:
        flags.append(f'Có thể trùng điểm với hồ sơ {near_id} (cách {near_m:.0f} m)')

    visual_matches = check_visual_duplicate(df_screen, pil, lat, lon, radius_m=35.0, threshold=0.72, cur_fp=fp)
    for vm in visual_matches[:1]:
        flags.append(f'AI Thị giác: ảnh tương đồng {vm["similarity"]*100:.0f}% với hồ sơ {vm["id"]} (cách {vm["distance_m"]:.0f} m)')

    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
    ext = ext if ext in ('jpg', 'jpeg', 'png') else 'jpg'

    # Nén thông minh nếu ảnh gốc từ điện thoại quá nặng (> 1.2 MB) để upload Cloud trong < 0.3s
    store_raw = raw
    if len(raw) > SMART_COMPRESS_THRESHOLD:
        try:
            src_im = pil or fast_prepare_rgb(raw, max_side=1600)
            store_raw = encode_jpeg_bytes(src_im, max_side=1600, quality=84)
            ext = 'jpg'
        except Exception:
            store_raw = raw

    image_file, annotated_file = f'images/{digest[:16]}.{ext}', f'annotated/{digest[:16]}.jpg'
    (data_dir() / image_file).write_bytes(store_raw)

    ann_bytes = out.get('annotated_jpeg_bytes')
    if not ann_bytes:
        ann_bytes = encode_jpeg_bytes(out['annotated_image'], max_side=1280, quality=83)
        out['annotated_jpeg_bytes'] = ann_bytes
    (data_dir() / annotated_file).write_bytes(ann_bytes)

    try:
        from . import storage
        if storage.is_enabled():
            raw_mime = 'image/png' if ext == 'png' else 'image/jpeg'
            with ThreadPoolExecutor(max_workers=2) as pool:
                f1 = pool.submit(storage.upload, image_file, store_raw, raw_mime)
                f2 = pool.submit(storage.upload, annotated_file, ann_bytes, 'image/jpeg')
                f1.result(timeout=20)
                f2.result(timeout=20)
    except Exception as exc:
        log.warning('Upload ảnh lên Cloud thất bại: %s', exc)

    level = final_level or sev['level']
    row = {
        'image_hash': digest,
        'dhash_64': fp['dhash_hex'],
        'color_vec': fp['color_json'],
        'image_file': image_file,
        'annotated_file': annotated_file,
        'location_name': str(location_name).strip(),
        'latitude': round(lat, 6),
        'longitude': round(lon, 6),
        'gps_source': gps_source,
        'gps_accuracy_m': gps_accuracy_m,
        'captured_at': captured_at,
        'status': status,
        'source': source,
        'capture_method': capture_method,
        'contact': contact,
        'consent': int(bool(consent)),
        'total_boxes': len(dets),
        **{f'count_{k}': v for k, v in sev['counts'].items()},
        'avg_confidence': round(sum(d['confidence'] for d in dets) / len(dets), 3) if dets else 0.0,
        'bbox_union_pct': sev['bbox_proxy_pct'],
        'damage_area_m2': damage_info['total_damage_m2'],
        'damage_volume_l': damage_info['estimated_volume_liters'],
        'damage_depth_desc': damage_info['damage_severity_desc'],
        'ai_level': sev['level'],
        'ai_score': sev['score'],
        'final_level': level,
        'final_score': final_score(sev['level'], sev['score'], level),
        'road_type': road_type,
        'road_score': ROAD_TYPES[road_type],
        'note': note,
        'quality_flags': '; '.join(quality['flags']),
        'screen_flags': '; '.join(flags),
        'detections_json': json.dumps(dets, ensure_ascii=False),
        'elapsed_ms': out['elapsed_ms'],
    }
    if status == 'verified':
        row.update(reviewed_by=actor or 'officer', reviewed_at=now.strftime('%Y-%m-%d %H:%M:%S'))
    return db.insert_report(row), out, quality, flags
