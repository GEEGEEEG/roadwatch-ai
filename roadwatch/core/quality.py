"""Chấm chất lượng ảnh + gắn cờ báo cáo đáng ngờ."""
import numpy as np
import pandas as pd
from PIL import Image, ImageOps

from .geo import haversine_m


def assess_quality(image):
    img = ImageOps.exif_transpose(image).convert('L')
    w, h = img.size
    scale = min(1.0, 800 / max(w, h))
    small = np.asarray(img.resize((max(1, int(w * scale)), max(1, int(h * scale)))), dtype=float)
    brightness = float(small.mean())
    lap = (-4 * small[1:-1, 1:-1] + small[:-2, 1:-1] + small[2:, 1:-1] + small[1:-1, :-2] + small[1:-1, 2:]) \
        if min(small.shape) >= 3 else np.zeros((1, 1))
    sharp = float(lap.var())
    flags = []
    if min(w, h) < 320:
        flags.append('Ảnh độ phân giải thấp')
    if brightness < 50:
        flags.append('Ảnh quá tối')
    elif brightness > 215:
        flags.append('Ảnh quá sáng')
    if sharp < 40:
        flags.append('Ảnh có thể bị mờ/rung')
    return {'flags': flags, 'brightness': round(brightness, 1), 'sharpness': round(sharp, 1), 'size': (w, h)}


def screening_flags(existing_df, lat, lon, now, total_boxes, quality_flags):
    """Cờ để người duyệt chú ý; không tự từ chối báo cáo."""
    flags = []
    if existing_df is not None and not existing_df.empty:
        e = existing_df.dropna(subset=['latitude', 'longitude'])
        if not e.empty:
            dist = haversine_m(lat, lon, e.latitude.values, e.longitude.values)
            created = pd.to_datetime(e.created_at, errors='coerce')
            recent = (now - created).dt.total_seconds().abs() < 600
            if bool(((dist < 20) & recent.values).any()):
                flags.append('Gửi dồn: có báo cáo khác trong 20 m / 10 phút')
    if quality_flags and total_boxes == 0:
        flags.append('Ảnh kém chất lượng và không phát hiện gì')
    return flags
