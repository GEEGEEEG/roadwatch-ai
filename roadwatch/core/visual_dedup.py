"""Nhận diện trùng lặp đa góc chụp bằng AI (Visual Deduplication).

Sử dụng Perceptual Difference Hash (dHash) kết hợp phân bố sắc thái bề mặt (HSV Color Distribution)
để phát hiện hai bức ảnh chụp cùng một vị trí hư hỏng dù góc chụp hoặc điều kiện ánh sáng khác nhau.
"""
import numpy as np
from PIL import Image, ImageOps

from .config import data_dir
from .geo import haversine_m


def compute_dhash(image_pil, hash_size=8):
    """Tính toán Difference Hash (dHash) 64-bit cho ảnh.

    dHash theo dõi độ dốc cường độ sáng (gradient) giữa các pixel liền kề,
    chống chịu rất tốt với việc thay đổi góc chụp, phóng to/thu nhỏ và tương phản.
    """
    img = ImageOps.exif_transpose(image_pil).convert('L')
    resized = img.resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
    pixels = np.asarray(resized, dtype=np.int32)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return diff.flatten()


def compute_color_vector(image_pil):
    """Tính vector phân bố màu sắc/độ sáng lòng đường (16 bins)."""
    img = ImageOps.exif_transpose(image_pil).convert('L')
    small = img.resize((64, 64), Image.Resampling.BILINEAR)
    arr = np.asarray(small, dtype=float)
    hist, _ = np.histogram(arr, bins=16, range=(0, 256), density=True)
    return hist


def image_fingerprint(image_pil):
    """Trích xuất mã định danh thị giác tổng hợp (fingerprint) của ảnh."""
    dhash = compute_dhash(image_pil)
    color = compute_color_vector(image_pil)
    return {'dhash': dhash, 'color': color}


def visual_similarity(fp1, fp2):
    """Đo độ tương đồng thị giác giữa 2 ảnh: kết hợp dHash và Color Correlation.

    Trả về giá trị từ 0.0 (hoàn toàn khác) đến 1.0 (trùng khớp tuyệt đối).
    """
    if fp1 is None or fp2 is None:
        return 0.0

    # 1. Độ tương đồng Hash (Hamming similarity)
    matches = np.count_nonzero(fp1['dhash'] == fp2['dhash'])
    hash_sim = matches / len(fp1['dhash'])  # 0.0 đến 1.0

    # 2. Độ tương đồng phân bố sắc thái (Cosine similarity của histogram)
    c1, c2 = fp1['color'], fp2['color']
    norm1 = np.linalg.norm(c1)
    norm2 = np.linalg.norm(c2)
    if norm1 > 0 and norm2 > 0:
        hist_sim = float(np.dot(c1, c2) / (norm1 * norm2))
    else:
        hist_sim = 0.0

    # Trọng số: 70% hình thái gradient (dHash) + 30% phân bố sắc thái
    total_sim = 0.70 * hash_sim + 0.30 * max(0.0, hist_sim)
    return round(float(total_sim), 3)


def check_visual_duplicate(df_active, current_image, current_lat, current_lon, radius_m=35.0, threshold=0.72):
    """Kiểm tra xem ảnh hiện tại có trùng với bất kỳ báo cáo nào đã có trong bán kính radius_m.

    Trả về danh sách các trùng lặp phát hiện được:
    [(existing_id, similarity_score, distance_m, location_name)]
    """
    if df_active is None or df_active.empty or current_image is None:
        return []

    d = df_active.dropna(subset=['latitude', 'longitude']).copy()
    if d.empty:
        return []

    cur_fp = image_fingerprint(current_image)
    matches = []
    root = data_dir()

    for _, row in d.iterrows():
        dist = haversine_m(current_lat, current_lon, float(row['latitude']), float(row['longitude']))
        if dist > radius_m:
            continue

        # Đọc ảnh đã lưu của báo cáo cũ
        img_rel = row.get('image_file')
        if not img_rel:
            continue
        p = root / img_rel
        if not p.is_file():
            continue

        try:
            with Image.open(p) as old_img:
                old_fp = image_fingerprint(old_img)
            sim = visual_similarity(cur_fp, old_fp)
            if sim >= threshold:
                matches.append({
                    'id': row['id'],
                    'similarity': sim,
                    'distance_m': round(dist, 1),
                    'location_name': row.get('location_name', 'Không rõ vị trí'),
                })
        except Exception:
            continue

    return sorted(matches, key=lambda x: x['similarity'], reverse=True)
