"""Mô hình ra quyết định đa tiêu chí AHP (Analytic Hierarchy Process) chuẩn Thomas L. Saaty (v5.0).

Tiêu chí đánh giá (đồng nhất thang 0 - 100):
- C1: Mức độ nghiêm trọng hư hại (AI & diện tích m²)
- C2: Tầm quan trọng tuyến đường (Cấp đường)
- C3: Tần suất phản ánh & mức độ bức xúc của cử tri
- C4: Rủi ro thời tiết & ngập úng (chuẩn hóa 0 - 100)
"""
import numpy as np

RI_DICT = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.89, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}

DEFAULT_AHP_MATRIX = np.array([
    [1.0, 2.0, 3.0, 4.0],
    [1/2, 1.0, 2.0, 3.0],
    [1/3, 1/2, 1.0, 2.0],
    [1/4, 1/3, 1/2, 1.0],
], dtype=float)


def build_pairwise_matrix(
    c12: float = 2.0,
    c13: float = 3.0,
    c14: float = 4.0,
    c23: float = 2.0,
    c24: float = 3.0,
    c34: float = 2.0,
) -> np.ndarray:
    """Tạo ma trận đối xứng nghịch đảo Saaty 4x4 từ 6 cặp so sánh tam giác trên (thang 1/9..9)."""
    vals = [max(1 / 9, min(9.0, float(v))) for v in (c12, c13, c14, c23, c24, c34)]
    a12, a13, a14, a23, a24, a34 = vals
    return np.array([
        [1.0,     a12,     a13,     a14],
        [1 / a12, 1.0,     a23,     a24],
        [1 / a13, 1 / a23, 1.0,     a34],
        [1 / a14, 1 / a24, 1 / a34, 1.0],
    ], dtype=float)


def normalize_weather_component(weather_bonus: float = 0.0, rain_mm: float | None = None, has_pothole: bool = True) -> float:
    """Quy đổi rủi ro thời tiết sang đúng thang 0 - 100 đồng bộ với C1, C2, C3."""
    if not has_pothole:
        return 0.0
    if rain_mm is not None:
        return float(np.clip(float(rain_mm) * 2.0, 0.0, 100.0))
    # weather_bonus mặc định từ 0..5 -> nhân 20 để quy về thang 0..100
    return float(np.clip(float(weather_bonus) * 20.0, 0.0, 100.0))


def compute_ahp_weights(matrix=None) -> dict:
    """Tính vector trọng số (Geometric Mean Eigenvector) và Tỷ số nhất quán (CR)."""
    a = np.asarray(matrix if matrix is not None else DEFAULT_AHP_MATRIX, dtype=float)
    n = a.shape[0]

    geom_means = np.prod(a, axis=1) ** (1.0 / n)
    weights = geom_means / np.sum(geom_means)

    aw = np.dot(a, weights)
    lambda_max = float(np.mean(aw / weights))

    ci = max(0.0, (lambda_max - n) / (n - 1)) if n > 1 else 0.0
    ri = RI_DICT.get(n, 1.49)
    cr = (ci / ri) if ri > 0 else 0.0

    return {
        'weights': np.round(weights, 4),
        'lambda_max': round(lambda_max, 4),
        'CI': round(ci, 4),
        'CR': round(cr, 4),
        'is_consistent': bool(cr < 0.10),
    }


def compute_ahp_priority(severity_score, road_score, frequency_score, weather_score: float = 0.0, custom_matrix=None):
    """Tính điểm ưu tiên sửa chữa (0 - 100) theo phương pháp toán học AHP."""
    res = compute_ahp_weights(custom_matrix)
    w = res['weights']
    s = (
        w[0] * float(np.clip(severity_score, 0.0, 100.0))
        + w[1] * float(np.clip(road_score, 0.0, 100.0))
        + w[2] * float(np.clip(frequency_score, 0.0, 100.0))
        + w[3] * float(np.clip(weather_score, 0.0, 100.0))
    )
    return round(float(np.clip(s, 0.0, 100.0)), 2), res
