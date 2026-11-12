"""Phân tích tổn thương chuyên sâu: Phân đoạn (Segmentation) & Ước lượng diện tích thực tế (m²).

Dựa trên chuẩn đường bộ Việt Nam (bề rộng làn xe ~3.5m, góc chụp thông thường 30-45 độ bao quát ~8.75 m² mặt đường).
Hỗ trợ cả thuần NumPy/PIL và OpenCV khi có sẵn.
"""
import numpy as np
from PIL import Image

# Diện tích mặt đường trung bình trong 1 khung hình chụp hiện trường (m²)
DEFAULT_FOV_ROAD_AREA_M2 = 8.75


def _otsu_threshold(gray_arr):
    """Tính ngưỡng Otsu bằng thuần NumPy (không phụ thuộc bắt buộc cv2)."""
    hist, _ = np.histogram(gray_arr, bins=256, range=(0, 256))
    total = gray_arr.size
    if total == 0:
        return 128
    current_max, threshold = 0.0, 128
    sum_total = np.dot(np.arange(256), hist)
    weight_bg, sum_bg = 0, 0
    for i in range(256):
        weight_bg += hist[i]
        if weight_bg == 0:
            continue
        weight_fg = total - weight_bg
        if weight_fg == 0:
            break
        sum_bg += i * hist[i]
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_total - sum_bg) / weight_fg
        var_between = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
        if var_between > current_max:
            current_max = var_between
            threshold = i
    return threshold


def extract_defect_contour(img_rgb_np, bbox_xyxy, class_code):
    """Trích xuất mặt nạ và đường viền tổn thương thực tế bên trong Bounding Box (ROI).

    Thay vì coi toàn bộ hộp chữ nhật là hư hỏng, thuật toán phân đoạn hình thái học
    tách lấy chính xác các pixel ổ gà hoặc vết nứt thực tế.
    """
    x1, y1, x2, y2 = bbox_xyxy
    h_img, w_img = img_rgb_np.shape[:2]
    x1, y1 = max(0, int(x1)), max(0, int(y1))
    x2, y2 = min(w_img, int(x2)), min(h_img, int(y2))

    roi = img_rgb_np[y1:y2, x1:x2]
    if roi.size == 0 or (x2 - x1) < 4 or (y2 - y1) < 4:
        return {'pixel_count': 0, 'fill_ratio': 0.0, 'depth_estimate': 'Không xác định', 'depth_cm': 0.0}

    # Chuyển grayscale
    if roi.ndim == 3:
        gray = np.dot(roi[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)
    else:
        gray = roi.astype(np.uint8)

    if class_code == 'D40':  # Ổ gà: vùng trũng tối có độ tương phản với mặt đường xung quanh
        thresh_val = _otsu_threshold(gray)
        # Lòng ổ gà tối hơn mặt đường
        mask = (gray <= thresh_val)

        pothole_pixels = gray[mask]
        surround_pixels = gray[~mask]
        if len(pothole_pixels) > 0 and len(surround_pixels) > 0:
            contrast_delta = float(surround_pixels.mean() - pothole_pixels.mean())
            if contrast_delta > 40:
                depth_desc = 'Sâu (> 5 cm)'
                depth_cm = 6.0
            elif contrast_delta > 18:
                depth_desc = 'Trung bình (2 - 5 cm)'
                depth_cm = 3.5
            else:
                depth_desc = 'Nông (< 2 cm)'
                depth_cm = 1.5
        else:
            depth_desc = 'Trung bình (2 - 5 cm)'
            depth_cm = 3.0

    else:  # D00/D10/D20: Vết nứt
        # Điểm ảnh tối hơn phân vị 30% trong hộp là đường nứt
        p30 = np.percentile(gray, 30)
        mask = (gray <= p30)
        depth_desc = 'Nứt bề mặt (< 1 cm)'
        depth_cm = 0.8

    defect_pixels = int(np.count_nonzero(mask))
    roi_total = int(mask.size)
    fill_ratio = defect_pixels / roi_total if roi_total > 0 else 0.0

    return {
        'pixel_count': defect_pixels,
        'fill_ratio': round(fill_ratio, 3),
        'depth_estimate': depth_desc,
        'depth_cm': depth_cm,
    }


def analyze_image_damage(image_pil, detections, fov_m2=DEFAULT_FOV_ROAD_AREA_M2):
    """Phân tích tổng hợp diện tích hư hại thực tế (m²) và thể tích ổ gà (lít).

    Kết quả dùng để:
    - Báo cáo số liệu đo đạc khoa học
    - Tính toán khối lượng nhựa/bê tông cần dùng để dặm vá
    """
    if not detections or image_pil is None:
        return {
            'total_damage_m2': 0.0,
            'total_damage_cm2': 0.0,
            'estimated_volume_liters': 0.0,
            'damage_severity_desc': 'Không phát hiện tổn thương',
            'detailed_boxes': [],
        }

    img_rgb = np.asarray(image_pil.convert('RGB'))
    total_img_pixels = img_rgb.shape[0] * img_rgb.shape[1]

    total_damage_pixels = 0
    total_pothole_vol_m3 = 0.0
    detailed_boxes = []

    for d in detections:
        code = d['class_code']
        box = d['bbox_xyxy']
        seg = extract_defect_contour(img_rgb, box, code)

        # Diện tích hư hại = (Số pixel thực tế / Tổng pixel ảnh) * Diện tích mặt đường bao quát
        area_m2 = (seg['pixel_count'] / total_img_pixels) * fov_m2
        area_cm2 = area_m2 * 10000.0

        # Thể tích = diện tích * độ sâu (cho D40)
        vol_liters = (area_m2 * (seg['depth_cm'] / 100.0)) * 1000.0

        if code == 'D40':
            total_pothole_vol_m3 += area_m2 * (seg['depth_cm'] / 100.0)

        total_damage_pixels += seg['pixel_count']
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

    total_m2 = round((total_damage_pixels / total_img_pixels) * fov_m2, 4)
    total_cm2 = round(total_m2 * 10000.0, 1)
    total_vol_liters = round(total_pothole_vol_m3 * 1000.0, 2)

    # Đánh giá cấp độ tổn thương vật lý
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
