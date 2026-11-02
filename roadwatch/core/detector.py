"""Nhận diện D00/D10/D20/D40 bằng YOLO + mức độ sơ bộ theo quy tắc + EXIF GPS."""
import re
import time

import numpy as np
from PIL import ExifTags, Image, ImageDraw, ImageOps

from .constants import BASE, COLORS, LABELS

DEFAULT_CLASS_THRESHOLDS = {}   # ví dụ {'D40': 0.20}: ổ gà bỏ sót nghiêm trọng hơn


def decode_model_label(name):
    label = str(name).strip().lower()
    for code in LABELS:
        if re.search(r'(?<![a-z0-9])' + code.lower() + r'(?![a-z0-9])', label):
            return code
    aliases = {'D00': ('longitudinal',), 'D10': ('transverse',),
               'D20': ('alligator', 'crocodile'), 'D40': ('pothole', 'pot hole')}
    for code, parts in aliases.items():
        if any(x in label for x in parts):
            return code
    return None


def union_area_pct(boxes, width, height, max_side=512):
    """% diện tích ảnh bị phủ bởi hợp các khung (không cộng chồng)."""
    if not boxes or width <= 0 or height <= 0:
        return 0.0
    s = min(1.0, max_side / max(width, height))
    w, h = max(1, int(width * s)), max(1, int(height * s))
    mask = np.zeros((h, w), dtype=bool)
    for x1, y1, x2, y2 in boxes:
        mask[max(0, int(y1 * s)):min(h, int(np.ceil(y2 * s))), max(0, int(x1 * s)):min(w, int(np.ceil(x2 * s)))] = True
    return round(100.0 * mask.sum() / mask.size, 2)


def severity_rule(detections, width=None, height=None):
    counts = {code: 0 for code in LABELS}
    for det in detections:
        counts[det['class_code']] += 1
    if not detections:
        return {'level': 'Không phát hiện', 'score': 0.0, 'counts': counts, 'bbox_proxy_pct': 0.0,
                'explanation': 'Không có vùng nào vượt ngưỡng. Không chứng minh đường hoàn toàn an toàn.'}
    if width and height:
        proxy = union_area_pct([d['bbox_xyxy'] for d in detections], width, height)
    else:
        proxy = min(100.0, sum(d['bbox_area_percent'] for d in detections))
    base = max(BASE[d['class_code']] for d in detections)
    score = min(100.0, round(base * 0.8 + min(proxy * 0.6, 15) + min((len(detections) - 1) * 3.5, 10), 1))
    level = 'Cần kiểm tra sớm' if score >= 70 else ('Trung bình' if score >= 45 else 'Nhẹ')
    return {'level': level, 'score': score, 'counts': counts, 'bbox_proxy_pct': proxy,
            'explanation': 'Điểm sơ bộ từ loại hư hỏng, số vùng phát hiện và diện tích HỢP của các khung. '
                           'Không đo độ sâu, không suy ra diện tích thực tế; cần con người xác minh.'}


def draw_detections(image, detections):
    drawn = image.copy()
    drawer = ImageDraw.Draw(drawn)
    for d in detections:
        x1, y1, x2, y2 = d['bbox_xyxy']
        color = COLORS[d['class_code']]
        drawer.rectangle((x1, y1, x2, y2), outline=color, width=4)
        drawer.text((x1 + 3, max(0, y1 - 16)), f"{d['class_code']}: {d['confidence']:.2f}", fill=color)
    return drawn


class RoadDamageDetector:
    def __init__(self, model_path):
        from ultralytics import YOLO      # import muộn để phần còn lại chạy/kiểm thử không cần torch
        self.model = YOLO(str(model_path))
        names = self.model.names
        items = names.items() if isinstance(names, dict) else enumerate(names)
        self.class_to_code = {int(k): decode_model_label(v) for k, v in items}
        if len(self.class_to_code) != 4 or set(self.class_to_code.values()) != set(LABELS):
            raise ValueError(f'Không xác minh được bốn lớp D00/D10/D20/D40: {names}. '
                             'Không tự gán nhãn theo index khi chưa chắc thứ tự.')

    # Giới hạn kích thước đầu vào để tránh tràn RAM trên Streamlit Community Cloud (~1 GB).
    # Ảnh có cạnh dài > MAX_INPUT_SIDE sẽ được thu nhỏ trước khi đưa vào YOLO.
    MAX_INPUT_SIDE = 1920

    def predict_image(self, original_image, threshold=0.25, imgsz=640, tta=False, class_thresholds=None):
        class_thresholds = class_thresholds or DEFAULT_CLASS_THRESHOLDS
        image = ImageOps.exif_transpose(original_image).convert('RGB')
        # Thu nhỏ ảnh nếu cạnh dài vượt ngưỡng (giữ tỉ lệ, dùng LANCZOS)
        w, h = image.size
        max_side = self.MAX_INPUT_SIDE
        if max(w, h) > max_side:
            scale = max_side / max(w, h)
            image = image.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
        run_conf = min([threshold, *class_thresholds.values()])
        start = time.perf_counter()
        pred = self.model.predict(image, conf=run_conf, imgsz=imgsz, augment=tta, verbose=False)[0]
        elapsed = round((time.perf_counter() - start) * 1000, 1)
        width, height = image.size
        detections = []
        if pred.boxes is not None:
            for xyxy, conf, cid in zip(pred.boxes.xyxy.cpu().tolist(), pred.boxes.conf.cpu().tolist(),
                                       pred.boxes.cls.cpu().tolist()):
                code = self.class_to_code[int(cid)]
                if conf < class_thresholds.get(code, threshold):
                    continue
                x1, y1, x2, y2 = [int(v) for v in xyxy]
                detections.append({'class_code': code, 'class_name': LABELS[code],
                                   'confidence': round(float(conf), 4), 'bbox_xyxy': [x1, y1, x2, y2],
                                   'bbox_area_percent': round(100.0 * max(0, x2 - x1) * max(0, y2 - y1) / (width * height), 2)})
        return {'annotated_image': draw_detections(image, detections), 'detections': detections,
                'elapsed_ms': elapsed, 'severity': severity_rule(detections, width, height),
                'image_size': (width, height)}


def extract_exif_gps(image):
    result = {'latitude': None, 'longitude': None, 'datetime': None, 'has_gps': False}
    try:
        exif = image.getexif()
        if not exif:
            return result
        result['datetime'] = exif.get(36867) or exif.get(306)
        gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
        if not gps:
            return result

        def dms(values, ref):
            values = [float(x[0]) / float(x[1]) if isinstance(x, tuple) else float(x) for x in values]
            deg = values[0] + values[1] / 60 + values[2] / 3600
            return -deg if ref in ('S', 'W', b'S', b'W') else deg
        lat, lon = dms(gps[2], gps[1]), dms(gps[4], gps[3])
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            result.update(latitude=round(lat, 6), longitude=round(lon, 6), has_gps=True)
    except Exception:
        pass
    return result
