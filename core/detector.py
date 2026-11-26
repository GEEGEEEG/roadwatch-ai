"""Nhận diện D00/D10/D20/D40 (v5.0): Hỗ trợ kép ONNX Runtime nhẹ RAM & PyTorch Ultralytics + EXIF GPS."""
import ast
import io
import json
import os
import re
import time
from pathlib import Path

import numpy as np
from PIL import ExifTags, Image, ImageDraw, ImageOps

from .constants import BASE, COLORS, LABELS

DEFAULT_CLASS_THRESHOLDS = {'D40': 0.15}


def fast_prepare_rgb(src: bytes | Image.Image, max_side: int = 1280) -> Image.Image:
    """Giải mã & thu nhỏ ảnh tốc độ cao (dùng JPEG DCT draft subsampling, nhanh gấp ~10-15 lần LANCZOS trên ảnh 12MP)."""
    if isinstance(src, (bytes, bytearray, memoryview)):
        im = Image.open(io.BytesIO(src))
        try:
            exif = im.getexif()
            orient = exif.get(274, 1) if exif else 1
        except Exception:
            orient = 1
        if im.format == 'JPEG' and orient == 1 and max(im.size) > max_side * 1.4:
            im.draft('RGB', (max_side, max_side))
        im.load()
    else:
        im = src

    im = ImageOps.exif_transpose(im)
    if im.mode != 'RGB':
        im = im.convert('RGB')
    w, h = im.size
    if max(w, h) > max_side:
        scale = max_side / max(w, h)
        im = im.resize((max(1, int(round(w * scale))), max(1, int(round(h * scale)))), Image.Resampling.BILINEAR)
    return im


def encode_jpeg_bytes(image: Image.Image, max_side: int = 1120, quality: int = 82) -> bytes:
    """Nén sẵn ảnh sang JPEG nhẹ (~90-140 KB) để st.image không tốn 2-4 giây CPU nén PNG lossless."""
    im = image if image.mode == 'RGB' else image.convert('RGB')
    w, h = im.size
    if max(w, h) > max_side:
        scale = max_side / max(w, h)
        im = im.resize((max(1, int(round(w * scale))), max(1, int(round(h * scale)))), Image.Resampling.BILINEAR)
    buf = io.BytesIO()
    im.save(buf, format='JPEG', quality=quality)
    return buf.getvalue()


def decode_model_label(name):
    label = str(name).strip().lower()
    for code in LABELS:
        if re.search(r'(?<![a-z0-9])' + code.lower() + r'(?![a-z0-9])', label):
            return code
    aliases = {
        'D00': ('longitudinal',),
        'D10': ('transverse',),
        'D20': ('alligator', 'crocodile'),
        'D40': ('pothole', 'pot hole'),
    }
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
        return {
            'level': 'Không phát hiện',
            'score': 0.0,
            'counts': counts,
            'bbox_proxy_pct': 0.0,
            'explanation': 'Không có vùng nào vượt ngưỡng. Không chứng minh đường hoàn toàn an toàn.',
        }
    if width and height:
        proxy = union_area_pct([d['bbox_xyxy'] for d in detections], width, height)
    else:
        proxy = min(100.0, sum(d['bbox_area_percent'] for d in detections))
    base = max(BASE[d['class_code']] for d in detections)
    score = min(100.0, round(base * 0.8 + min(proxy * 0.6, 15) + min((len(detections) - 1) * 3.5, 10), 1))
    level = 'Cần kiểm tra sớm' if score >= 70 else ('Trung bình' if score >= 45 else 'Nhẹ')
    return {
        'level': level,
        'score': score,
        'counts': counts,
        'bbox_proxy_pct': proxy,
        'explanation': (
            'Điểm sơ bộ từ loại hư hỏng, số vùng phát hiện và diện tích HỢP của các khung. '
            'Không đo độ sâu thực tế bằng cảm biến laser; luôn cần cán bộ xác minh.'
        ),
    }


def draw_detections(image, detections):
    from PIL import ImageFont
    drawn = image.copy()
    drawer = ImageDraw.Draw(drawn)
    w, h = drawn.size
    font_size = max(14, min(26, int(round(min(w, h) * 0.032))))
    try:
        font = ImageFont.load_default(size=font_size)
    except TypeError:
        font = ImageFont.load_default()
    line_w = max(3, min(6, int(round(min(w, h) * 0.005))))
    for d in detections:
        x1, y1, x2, y2 = d['bbox_xyxy']
        color = COLORS[d['class_code']]
        drawer.rectangle((x1, y1, x2, y2), outline=color, width=line_w)
        tag = f"{d['class_code']} {int(round(float(d['confidence']) * 100))}%"
        tb = drawer.textbbox((0, 0), tag, font=font)
        tw, th = tb[2] - tb[0], tb[3] - tb[1]
        pad_x, pad_y = 6, 3
        ty1 = max(0, y1 - th - pad_y * 2)
        tx1 = max(0, min(x1, max(0, w - tw - pad_x * 2)))
        drawer.rectangle((tx1, ty1, tx1 + tw + pad_x * 2, ty1 + th + pad_y * 2), fill=color)
        drawer.text((tx1 + pad_x, ty1 + pad_y), tag, fill='#FFFFFF', font=font)
    return drawn


def _nms_numpy(boxes_xyxy: np.ndarray, scores: np.ndarray, iou_thr: float = 0.45) -> list[int]:
    """Non-Maximum Suppression thuần NumPy cho suy luận ONNX Runtime siêu nhẹ."""
    if len(boxes_xyxy) == 0:
        return []
    x1 = boxes_xyxy[:, 0]
    y1 = boxes_xyxy[:, 1]
    x2 = boxes_xyxy[:, 2]
    y2 = boxes_xyxy[:, 3]
    areas = np.maximum(0.0, x2 - x1) * np.maximum(0.0, y2 - y1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = int(order[0])
        keep.append(i)
        if order.size == 1:
            break
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        inter = np.maximum(0.0, xx2 - xx1) * np.maximum(0.0, yy2 - yy1)
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        inds = np.where(iou <= iou_thr)[0]
        order = order[inds + 1]
    return keep


class RoadDamageDetector:
    MAX_INPUT_SIDE = 1280

    def __init__(self, model_path):
        self.model_path = Path(model_path)
        self.backend = 'ultralytics'
        self._ort_session = None
        self.model = None
        cpu_threads = max(1, min(4, os.cpu_count() or 2))

        if self.model_path.suffix.lower() == '.onnx':
            try:
                import onnxruntime as ort
                sess_opts = ort.SessionOptions()
                sess_opts.intra_op_num_threads = cpu_threads
                sess_opts.inter_op_num_threads = 1
                sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                self._ort_session = ort.InferenceSession(
                    str(self.model_path),
                    sess_options=sess_opts,
                    providers=['CPUExecutionProvider'],
                )
                meta = self._ort_session.get_modelmeta().custom_metadata_map or {}
                raw_names = meta.get('names')
                names = ast.literal_eval(raw_names) if raw_names else self._load_sidecar_names()
                if names:
                    items = names.items() if isinstance(names, dict) else enumerate(names)
                    self.class_to_code = {int(k): decode_model_label(v) for k, v in items}
                    if len(self.class_to_code) == 4 and set(self.class_to_code.values()) == set(LABELS):
                        self.backend = 'onnxruntime'
                        return
            except ImportError:
                pass

        try:
            import torch
            torch.set_num_threads(cpu_threads)
        except Exception:
            pass

        from ultralytics import YOLO
        self.model = YOLO(str(self.model_path))
        try:
            self.model.fuse()
        except Exception:
            pass
        names = self.model.names
        items = names.items() if isinstance(names, dict) else enumerate(names)
        self.class_to_code = {int(k): decode_model_label(v) for k, v in items}
        if len(self.class_to_code) != 4 or set(self.class_to_code.values()) != set(LABELS):
            raise ValueError(
                f'Không xác minh được bốn lớp D00/D10/D20/D40: {names}. '
                'Không tự gán nhãn theo index khi chưa chắc thứ tự.'
            )

    def _load_sidecar_names(self):
        sidecar = self.model_path.with_suffix('.json')
        if sidecar.is_file():
            try:
                return json.loads(sidecar.read_text(encoding='utf-8')).get('names')
            except Exception:
                return None
        return None

    def _predict_ort(self, image: Image.Image, run_conf: float, imgsz: int) -> list[tuple[list[int], float, int]]:
        inp = self._ort_session.get_inputs()[0]
        ishape = inp.shape
        target = int(ishape[2]) if len(ishape) >= 4 and isinstance(ishape[2], int) else int(imgsz)
        w0, h0 = image.size
        r = min(target / w0, target / h0)
        nw, nh = int(round(w0 * r)), int(round(h0 * r))
        dw, dh = (target - nw) / 2.0, (target - nh) / 2.0

        resized = image.resize((nw, nh), Image.Resampling.BILINEAR)
        canvas = Image.new('RGB', (target, target), (114, 114, 114))
        canvas.paste(resized, (int(round(dw - 0.1)), int(round(dh - 0.1))))

        arr = np.asarray(canvas, dtype=np.float32).transpose(2, 0, 1)[None] / 255.0
        out = self._ort_session.run(None, {inp.name: arr})[0]
        pred = np.squeeze(out, axis=0)
        if pred.shape[0] < pred.shape[1] and pred.shape[0] <= 64:
            pred = pred.T  # (N, 4 + num_classes)

        boxes_cxcywh = pred[:, :4]
        cls_scores = pred[:, 4:8]
        cids = np.argmax(cls_scores, axis=1)
        confs = cls_scores[np.arange(len(pred)), cids]
        mask = confs >= run_conf
        if not np.any(mask):
            return []

        boxes_cxcywh = boxes_cxcywh[mask]
        confs = confs[mask]
        cids = cids[mask]

        x1 = (boxes_cxcywh[:, 0] - boxes_cxcywh[:, 2] / 2.0 - dw) / r
        y1 = (boxes_cxcywh[:, 1] - boxes_cxcywh[:, 3] / 2.0 - dh) / r
        x2 = (boxes_cxcywh[:, 0] + boxes_cxcywh[:, 2] / 2.0 - dw) / r
        y2 = (boxes_cxcywh[:, 1] + boxes_cxcywh[:, 3] / 2.0 - dh) / r
        xyxy = np.stack([
            np.clip(x1, 0, w0),
            np.clip(y1, 0, h0),
            np.clip(x2, 0, w0),
            np.clip(y2, 0, h0),
        ], axis=1)

        results = []
        for cls_id in np.unique(cids):
            idx = np.where(cids == cls_id)[0]
            keep = _nms_numpy(xyxy[idx], confs[idx], iou_thr=0.45)
            for k in keep:
                gi = idx[k]
                results.append(([int(v) for v in xyxy[gi]], float(confs[gi]), int(cids[gi])))
        return results

    def _run_single_pass(self, image: Image.Image, run_conf: float, imgsz: int, augment: bool = False) -> list[tuple[list[int], float, int]]:
        if self.backend == 'onnxruntime':
            return self._predict_ort(image, run_conf, imgsz)
        try:
            import torch
            ctx = torch.inference_mode()
        except Exception:
            from contextlib import nullcontext
            ctx = nullcontext()
        raw_preds = []
        with ctx:
            pred = self.model.predict(image, conf=run_conf, imgsz=imgsz, augment=augment, device='cpu', half=False, verbose=False)[0]
        if pred.boxes is not None:
            for xyxy, conf, cid in zip(
                pred.boxes.xyxy.cpu().tolist(),
                pred.boxes.conf.cpu().tolist(),
                pred.boxes.cls.cpu().tolist(),
            ):
                raw_preds.append(([int(v) for v in xyxy], float(conf), int(cid)))
        return raw_preds

    @staticmethod
    def _merge_preds_nms(raw_preds: list[tuple[list[int], float, int]], iou_thr: float = 0.45) -> list[tuple[list[int], float, int]]:
        if len(raw_preds) <= 1:
            return raw_preds
        boxes = np.asarray([p[0] for p in raw_preds], dtype=np.float32)
        confs = np.asarray([p[1] for p in raw_preds], dtype=np.float32)
        cids = np.asarray([p[2] for p in raw_preds], dtype=np.int32)
        merged = []
        for cls_id in np.unique(cids):
            idx = np.where(cids == cls_id)[0]
            keep = _nms_numpy(boxes[idx], confs[idx], iou_thr=iou_thr)
            for k in keep:
                gi = int(idx[k])
                merged.append((raw_preds[gi][0], raw_preds[gi][1], raw_preds[gi][2]))
        return merged

    @staticmethod
    def _glare_enhanced_copy(image: Image.Image) -> Image.Image:
        """Tăng tương phản cục bộ và giảm lóa nhẹ để lộ viền ổ gà đọng nước (D40)."""
        stretched = ImageOps.autocontrast(image, cutoff=2)
        arr = np.asarray(stretched, dtype=np.float32) / 255.0
        arr = np.power(np.clip(arr, 0.0, 1.0), 1.18) * 255.0
        return Image.fromarray(arr.astype(np.uint8), mode='RGB')

    def predict_image(
        self,
        original_image,
        threshold=0.25,
        imgsz=640,
        tta=False,
        class_thresholds=None,
        enhance_glare=False,
    ):
        class_thresholds = class_thresholds or DEFAULT_CLASS_THRESHOLDS
        image = fast_prepare_rgb(original_image, max_side=self.MAX_INPUT_SIDE)
        width, height = image.size

        run_conf = min([threshold, *class_thresholds.values()])
        start = time.perf_counter()

        raw_preds = self._run_single_pass(image, run_conf, imgsz, augment=(tta and self.backend != 'onnxruntime'))

        if tta and self.backend == 'onnxruntime':
            flipped = self._run_single_pass(ImageOps.mirror(image), run_conf, imgsz, augment=False)
            for (x1, y1, x2, y2), conf, cid in flipped:
                raw_preds.append(([max(0, width - x2), y1, min(width, width - x1), y2], conf, cid))

        if enhance_glare or tta:
            glare_preds = self._run_single_pass(self._glare_enhanced_copy(image), run_conf, imgsz, augment=False)
            d40_min = max(0.18, float(class_thresholds.get('D40', threshold)))
            for box, conf, cid in glare_preds:
                if self.class_to_code.get(int(cid)) == 'D40' and conf >= d40_min:
                    raw_preds.append((box, conf, cid))

        raw_preds = self._merge_preds_nms(raw_preds, iou_thr=0.45)

        elapsed = round((time.perf_counter() - start) * 1000, 1)
        detections = []
        for (x1, y1, x2, y2), conf, cid in raw_preds:
            code = self.class_to_code[int(cid)]
            if conf < class_thresholds.get(code, threshold):
                continue
            detections.append({
                'class_code': code,
                'class_name': LABELS[code],
                'confidence': round(float(conf), 4),
                'bbox_xyxy': [x1, y1, x2, y2],
                'bbox_area_percent': round(100.0 * max(0, x2 - x1) * max(0, y2 - y1) / (width * height), 2),
            })

        return {
            'annotated_image': draw_detections(image, detections),
            'detections': detections,
            'elapsed_ms': elapsed,
            'severity': severity_rule(detections, width, height),
            'image_size': (width, height),
        }


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
