"""Phân tích tổn thương chuyên sâu (v5.0): Phân đoạn hình thái học & Ước lượng diện tích hợp nhất (m²).

Cải tiến:
- Hợp nhất mặt nạ nhị phân toàn khung hình (`global_defect_mask`) để KHÔNG cộng trùng diện tích khi các khung YOLO đè nhau.
- Hiệu chỉnh trọng số phối cảnh theo trục dọc `y` (pixel ở xa phía trên khung hình đại diện diện tích mặt đường lớn hơn).
"""
import numpy as np

DEFAULT_FOV_ROAD_AREA_M2 = 8.75


def _otsu_threshold(gray_arr: np.ndarray) -> int:
    hist, _ = np.histogram(gray_arr, bins=256, range=(0, 256))
    total = gray_arr.size
    if total == 0:
        return 128
    current_max, threshold = 0.0, 128
    sum_total = float(np.dot(np.arange(256), hist))
    weight_bg, sum_bg = 0, 0.0
    for i in range(256):
        weight_bg += int(hist[i])
        if weight_bg == 0:
            continue
        weight_fg = total - weight_bg
        if weight_fg == 0:
            break
        sum_bg += i * float(hist[i])
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_total - sum_bg) / weight_fg
        var_between = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
        if var_between > current_max:
            current_max = var_between
            threshold = i
    return threshold


def extract_defect_contour(img_rgb_np: np.ndarray, bbox_xyxy, class_code: str) -> dict:
    """Trích xuất mặt nạ tổn thương thực tế bên trong Bounding Box (ROI)."""
    x1, y1, x2, y2 = bbox_xyxy
    h_img, w_img = img_rgb_np.shape[:2]
    x1, y1 = max(0, int(x1)), max(0, int(y1))
    x2, y2 = min(w_img, int(x2)), min(h_img, int(y2))

    roi = img_rgb_np[y1:y2, x1:x2]
    if roi.size == 0 or (x2 - x1) < 4 or (y2 - y1) < 4:
        return {
            'pixel_count': 0,
            'fill_ratio': 0.0,
            'depth_estimate': 'Không xác định',
            'depth_cm': 0.0,
            'mask': None,
            'clamped_box': (x1, y1, x2, y2),
        }

    gray = (
        np.dot(roi[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)
        if roi.ndim == 3
        else roi.astype(np.uint8)
    )

    if class_code == 'D40':
        thresh_val = _otsu_threshold(gray)
        mask = gray <= thresh_val
        pothole_pixels = gray[mask]
        surround_pixels = gray[~mask]
        if len(pothole_pixels) > 0 and len(surround_pixels) > 0:
            contrast_delta = float(surround_pixels.mean() - pothole_pixels.mean())
            if contrast_delta > 40:
                depth_desc, depth_cm = 'Sâu (> 5 cm)', 6.0
            elif contrast_delta > 18:
                depth_desc, depth_cm = 'Trung bình (2 - 5 cm)', 3.5
            else:
                depth_desc, depth_cm = 'Nông (< 2 cm)', 1.5
        else:
            depth_desc, depth_cm = 'Trung bình (2 - 5 cm)', 3.0
    else:
        p30 = np.percentile(gray, 30)
        mask = gray <= p30
        depth_desc, depth_cm = 'Nứt bề mặt (< 1 cm)', 0.8

    defect_pixels = int(np.count_nonzero(mask))
    roi_total = int(mask.size)
    fill_ratio = defect_pixels / roi_total if roi_total > 0 else 0.0

    return {
        'pixel_count': defect_pixels,
        'fill_ratio': round(fill_ratio, 3),
        'depth_estimate': depth_desc,
        'depth_cm': depth_cm,
        'mask': mask,
        'clamped_box': (x1, y1, x2, y2),
    }


def analyze_image_damage(image_pil, detections, fov_m2: float = DEFAULT_FOV_ROAD_AREA_M2, perspective: bool = True) -> dict:
    """Tính diện tích hư hại hợp nhất (m²) và thể tích ước tính (lít) không bị nhân đôi vùng chồng lấn."""
    if not detections or image_pil is None:
        return {
            'total_damage_m2': 0.0,
            'total_damage_cm2': 0.0,
            'estimated_volume_liters': 0.0,
            'damage_severity_desc': 'Không phát hiện tổn thương',
            'detailed_boxes': [],
        }

    im = image_pil if image_pil.mode == 'RGB' else image_pil.convert('RGB')
    w0, h0 = im.size
    box_scale = 1.0
    if max(w0, h0) > 960:
        from PIL import Image
        box_scale = 960.0 / max(w0, h0)
        im = im.resize((max(1, int(round(w0 * box_scale))), max(1, int(round(h0 * box_scale)))), Image.Resampling.BILINEAR)
    img_rgb = np.asarray(im)
    h_img, w_img = img_rgb.shape[:2]
    total_img_pixels = max(1, h_img * w_img)

    # Trọng số phối cảnh tuyến tính theo dòng y (trung bình toàn ảnh = 1.0):
    # phía xa đầu ảnh (y=0) ~ 1.30x, sát chân người chụp (y=H-1) ~ 0.70x
    if perspective and h_img > 1:
        row_weights = np.linspace(1.30, 0.70, h_img, dtype=np.float32)[:, None]
    else:
        row_weights = np.ones((h_img, 1), dtype=np.float32)

    global_defect_mask = np.zeros((h_img, w_img), dtype=bool)
    global_depth_cm_map = np.zeros((h_img, w_img), dtype=np.float32)
    detailed_boxes = []

    for d in detections:
        code = d['class_code']
        raw_box = d['bbox_xyxy']
        box = [v * box_scale for v in raw_box] if box_scale != 1.0 else raw_box
        seg = extract_defect_contour(img_rgb, box, code)
        mask = seg['mask']
        x1, y1, x2, y2 = seg['clamped_box']

        if mask is not None and mask.size > 0:
            weighted_px = float(np.sum(mask * row_weights[y1:y2, :]))
            global_defect_mask[y1:y2, x1:x2] |= mask
            if code == 'D40':
                cur_slice = global_depth_cm_map[y1:y2, x1:x2]
                global_depth_cm_map[y1:y2, x1:x2] = np.where(mask, np.maximum(cur_slice, seg['depth_cm']), cur_slice)
        else:
            weighted_px = 0.0

        area_m2 = (weighted_px / total_img_pixels) * fov_m2
        area_cm2 = area_m2 * 10000.0
        vol_liters = (area_m2 * (seg['depth_cm'] / 100.0)) * 1000.0

        detailed_boxes.append({
            'class_code': code,
            'confidence': d.get('confidence', 0.0),
            'area_m2': round(area_m2, 4),
            'area_cm2': round(area_cm2, 1),
            'fill_ratio': seg['fill_ratio'],
            'depth_estimate': seg['depth_estimate'],
            'depth_cm': seg['depth_cm'],
            'volume_liters': round(vol_liters, 2),
        })

    union_weighted_px = float(np.sum(global_defect_mask * row_weights))
    total_m2 = round((union_weighted_px / total_img_pixels) * fov_m2, 4)
    total_cm2 = round(total_m2 * 10000.0, 1)

    pothole_mask = global_depth_cm_map > 0
    if np.any(pothole_mask):
        # Mỗi pixel quy đổi ra diện tích m² * độ sâu m * 1000 lít/m³
        px_area_factor = fov_m2 / total_img_pixels
        vol_m3 = float(np.sum((global_depth_cm_map / 100.0) * row_weights * pothole_mask)) * px_area_factor
        total_vol_liters = round(vol_m3 * 1000.0, 2)
    else:
        total_vol_liters = 0.0

    if total_m2 >= 0.5:
        sev_desc = f'Tổn thương diện rộng ({total_m2:.2f} m²)'
    elif total_m2 >= 0.1:
        sev_desc = f'Tổn thương mức trung bình ({total_m2:.2f} m²)'
    elif total_m2 > 0:
        sev_desc = f'Tổn thương cục bộ nhỏ ({total_cm2:.0f} cm²)'
    else:
        sev_desc = 'Không phát hiện tổn thương'

    return {
        'total_damage_m2': total_m2,
        'total_damage_cm2': total_cm2,
        'estimated_volume_liters': total_vol_liters,
        'damage_severity_desc': sev_desc,
        'detailed_boxes': detailed_boxes,
    }
