"""Luồng gửi báo cáo: kiểm tra -> nhận diện -> lưu ảnh -> gắn cờ -> ghi DB."""
import hashlib
import io
import json
from datetime import datetime

from PIL import Image

from . import db
from .config import data_dir
from .constants import ACTIVE_STATUSES, DUP_FLAG_M, ROAD_TYPES
from .damage_analysis import analyze_image_damage
from .geo import nearby_points
from .priority import final_score
from .quality import assess_quality, screening_flags
from .visual_dedup import check_visual_duplicate

MAX_BYTES = 12 * 1024 * 1024


class SubmitError(Exception):
    pass


def submit_report(detector, raw: bytes, filename: str, *, location_name, lat, lon, gps_source,
                  source='citizen', consent=False, contact='', road_type=None, note='',
                  threshold=0.25, status='pending', actor='', captured_at=None, final_level=None,
                  imgsz=640, tta=False, capture_method='upload', gps_accuracy_m=None):
    if len(raw) > MAX_BYTES:
        raise SubmitError('Ảnh vượt quá 12 MB.')
    if source == 'citizen' and not consent:
        raise SubmitError('Cần đồng ý cho phép lưu ảnh và vị trí trước khi gửi.')
    if not str(location_name).strip():
        raise SubmitError('Thiếu tên tuyến / điểm chụp.')
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        raise SubmitError('Vĩ độ/kinh độ không hợp lệ. Không lưu vị trí bịa đặt.')
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise SubmitError('Vĩ độ/kinh độ ngoài phạm vi hợp lệ.')
    road_type = road_type if road_type in ROAD_TYPES else 'Đường khu dân cư (minh họa)'
    digest = hashlib.sha256(raw).hexdigest()
    existing = db.find_by_hash(digest)
    if existing:
        raise db.DuplicateImage(existing)
    try:
        pil = Image.open(io.BytesIO(raw))
        pil.load()
    except Exception:
        raise SubmitError('Không đọc được ảnh (cần JPG/PNG hợp lệ).')

    out = detector.predict_image(pil, threshold=threshold, imgsz=imgsz, tta=tta)
    sev, dets = out['severity'], out['detections']
    quality = assess_quality(pil)
    damage_info = analyze_image_damage(pil, dets)
    out['damage_analysis'] = damage_info
    now = datetime.now()
    df_all = db.fetch_df()
    flags = list(screening_flags(df_all, lat, lon, now, len(dets), quality['flags']))

    # Kiểm tra trùng lặp vị trí GPS
    for near_id, near_m, _ in nearby_points(df_all, lat, lon, DUP_FLAG_M, ACTIVE_STATUSES)[:1]:
        flags.append(f'Có thể trùng điểm với hồ sơ {near_id} (cách {near_m:.0f} m)')

    # Kiểm tra trùng lặp đa góc chụp bằng AI thị giác (Visual Deduplication)
    visual_matches = check_visual_duplicate(df_all, pil, lat, lon, radius_m=35.0, threshold=0.72)
    for vm in visual_matches[:1]:
        flags.append(f'AI Thị giác: ảnh tương đồng {vm["similarity"]*100:.0f}% với hồ sơ {vm["id"]} (cách {vm["distance_m"]:.0f} m)')

    ext = (filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg')
    ext = ext if ext in ('jpg', 'jpeg', 'png') else 'jpg'
    image_file, annotated_file = f'images/{digest[:16]}.{ext}', f'annotated/{digest[:16]}.jpg'
    (data_dir() / image_file).write_bytes(raw)
    annotated_preview = out['annotated_image'].copy()
    annotated_preview.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
    annotated_preview.convert('RGB').save(data_dir() / annotated_file, 'JPEG', quality=83, optimize=True)

    # Đồng bộ ảnh lên Cloud Storage (GCS/Drive) nếu được cấu hình
    try:
        from . import storage
        if storage.is_enabled():
            import io as _io
            storage.upload(image_file, raw)
            buf = _io.BytesIO()
            annotated_preview.convert('RGB').save(buf, 'JPEG', quality=83, optimize=True)
            storage.upload(annotated_file, buf.getvalue(), 'image/jpeg')
    except Exception as _exc:
        import logging as _log
        _log.getLogger(__name__).warning('Upload ảnh lên Cloud thất bại: %s', _exc)

    level = final_level or sev['level']
    row = {
        'image_hash': digest, 'image_file': image_file, 'annotated_file': annotated_file,
        'location_name': str(location_name).strip(), 'latitude': round(lat, 6), 'longitude': round(lon, 6),
        'gps_source': gps_source, 'gps_accuracy_m': gps_accuracy_m, 'captured_at': captured_at,
        'status': status, 'source': source, 'capture_method': capture_method,
        'contact': contact, 'consent': int(bool(consent)), 'total_boxes': len(dets),
        **{f'count_{k}': v for k, v in sev['counts'].items()},
        'avg_confidence': round(sum(d['confidence'] for d in dets) / len(dets), 3) if dets else 0.0,
        'bbox_union_pct': sev['bbox_proxy_pct'],
        'damage_area_m2': damage_info['total_damage_m2'],
        'damage_volume_l': damage_info['estimated_volume_liters'],
        'damage_depth_desc': damage_info['damage_severity_desc'],
        'ai_level': sev['level'], 'ai_score': sev['score'],
        'final_level': level, 'final_score': final_score(sev['level'], sev['score'], level),
        'road_type': road_type, 'road_score': ROAD_TYPES[road_type], 'note': note,
        'quality_flags': '; '.join(quality['flags']), 'screen_flags': '; '.join(flags),
        'detections_json': json.dumps(dets, ensure_ascii=False), 'elapsed_ms': out['elapsed_ms'],
    }
    if status == 'verified':
        row.update(reviewed_by=actor, reviewed_at=now.strftime('%Y-%m-%d %H:%M:%S'))
    return db.insert_report(row), out, quality, flags
