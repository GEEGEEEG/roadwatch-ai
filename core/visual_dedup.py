"""Nhận diện trùng lặp đa góc chụp bằng AI Thị giác (Visual Deduplication v5.0).

Cải tiến cốt lõi:
- Mã hóa `dhash_64` (16 ký tự hex) và `color_vec` (JSON 16-bin histogram) lưu trực tiếp vào bảng PostgreSQL/SQLite.
- Khi kiểm tra trùng lặp trên Streamlit Cloud, so khớp trực tiếp từ vector trong DB (< 1 ms, không cần tải lại file ảnh cũ).
- Vẫn tương thích ngược với các bản ghi cũ chưa có cột `dhash_64`.
"""
import json
import numpy as np
from PIL import Image, ImageOps

from .config import data_dir
from .geo import haversine_m


def compute_dhash(image_pil, hash_size: int = 8) -> np.ndarray:
    """Tính toán Difference Hash (dHash) 64-bit cho ảnh."""
    img = ImageOps.exif_transpose(image_pil).convert('L')
    resized = img.resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
    pixels = np.asarray(resized, dtype=np.int32)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return diff.flatten()


def dhash_to_hex(dhash_arr: np.ndarray) -> str:
    bits = np.asarray(dhash_arr, dtype=np.uint8).flatten()
    packed = np.packbits(bits)
    return packed.tobytes().hex()


def hex_to_dhash(hex_str: str, length: int = 64) -> np.ndarray | None:
    if not hex_str or not isinstance(hex_str, str):
        return None
    try:
        raw = bytes.fromhex(hex_str.strip())
        bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8))[:length]
        return bits.astype(bool) if len(bits) == length else None
    except Exception:
        return None


def compute_color_vector(image_pil) -> np.ndarray:
    """Tính vector phân bố sắc thái/độ sáng lòng đường (16 bins)."""
    img = ImageOps.exif_transpose(image_pil).convert('L')
    small = img.resize((64, 64), Image.Resampling.BILINEAR)
    arr = np.asarray(small, dtype=float)
    hist, _ = np.histogram(arr, bins=16, range=(0, 256), density=True)
    return hist


def image_fingerprint(image_pil) -> dict:
    """Trích xuất mã định danh thị giác tổng hợp (fingerprint) của ảnh."""
    dhash = compute_dhash(image_pil)
    color = compute_color_vector(image_pil)
    return {
        'dhash': dhash,
        'dhash_hex': dhash_to_hex(dhash),
        'color': color,
        'color_json': json.dumps([round(float(x), 6) for x in color]),
    }


def fingerprint_from_row(row) -> dict | None:
    """Khôi phục fingerprint trực tiếp từ dữ liệu dòng DB mà không cần mở file ảnh."""
    dhash = hex_to_dhash(row.get('dhash_64') or '')
    c_raw = row.get('color_vec') or ''
    if dhash is None or not c_raw:
        return None
    try:
        c_arr = np.asarray(json.loads(c_raw), dtype=float)
        if c_arr.shape != (16,):
            return None
        return {'dhash': dhash, 'color': c_arr}
    except Exception:
        return None


def visual_similarity(fp1, fp2) -> float:
    """Đo độ tương đồng thị giác giữa 2 ảnh (0.0 đến 1.0)."""
    if fp1 is None or fp2 is None:
        return 0.0

    matches = np.count_nonzero(fp1['dhash'] == fp2['dhash'])
    hash_sim = matches / len(fp1['dhash'])

    c1, c2 = fp1['color'], fp2['color']
    norm1 = float(np.linalg.norm(c1))
    norm2 = float(np.linalg.norm(c2))
    hist_sim = float(np.dot(c1, c2) / (norm1 * norm2)) if (norm1 > 0 and norm2 > 0) else 0.0

    total_sim = 0.70 * hash_sim + 0.30 * max(0.0, hist_sim)
    return round(float(total_sim), 3)


def check_visual_duplicate(
    df_active,
    current_image,
    current_lat: float,
    current_lon: float,
    radius_m: float = 35.0,
    threshold: float = 0.72,
    cur_fp: dict | None = None,
) -> list[dict]:
    """Kiểm tra ảnh hiện tại có trùng góc chụp với báo cáo nào trong bán kính `radius_m`."""
    if df_active is None or df_active.empty or (current_image is None and cur_fp is None):
        return []

    d = df_active.dropna(subset=['latitude', 'longitude']).copy()
    if d.empty:
        return []

    dists = haversine_m(
        float(current_lat),
        float(current_lon),
        d['latitude'].astype(float).values,
        d['longitude'].astype(float).values,
    )
    d = d.assign(_dist_m=dists)
    near_df = d[d['_dist_m'] <= radius_m]
    if near_df.empty:
        return []

    cur_fp = cur_fp or image_fingerprint(current_image)
    matches = []
    root = data_dir()

    for _, row in near_df.iterrows():
        old_fp = fingerprint_from_row(row)
        if old_fp is None:
            img_rel = row.get('image_file')
            if img_rel:
                p = root / str(img_rel)
                if p.is_file():
                    try:
                        with Image.open(p) as old_img:
                            old_fp = image_fingerprint(old_img)
                    except Exception:
                        old_fp = None
        if old_fp is None:
            continue

        sim = visual_similarity(cur_fp, old_fp)
        if sim >= threshold:
            matches.append({
                'id': row['id'],
                'similarity': sim,
                'distance_m': round(float(row['_dist_m']), 1),
                'location_name': row.get('location_name', 'Không rõ vị trí'),
            })

    return sorted(matches, key=lambda x: x['similarity'], reverse=True)
