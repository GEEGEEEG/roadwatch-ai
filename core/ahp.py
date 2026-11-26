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

SAATY_SCALE = np.array([
    1/9, 1/8, 1/7, 1/6, 1/5, 1/4, 1/3, 1/2,
    1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0,
], dtype=float)


def _snap_saaty(ratio: float) -> float:
    """Làm tròn tỷ số trọng số về mức gần nhất trên thang Saaty 1/9..9."""
    val = max(1 / 9, min(9.0, float(ratio)))
    idx = int(np.argmin(np.abs(np.log(SAATY_SCALE) - np.log(val))))
    return float(SAATY_SCALE[idx])


def build_auto_ahp_matrix(
    weights: tuple[float, float, float] = (50.0, 30.0, 20.0),
    rain_mm: float | None = None,
    severe_ratio: float = 0.0,
) -> tuple[np.ndarray, dict]:
    """Tự động sinh ma trận so sánh cặp Saaty 4x4 tối ưu ở backend, luôn đảm bảo CR < 0.10.

    - weights: (w_severity, w_frequency, w_road) từ kịch bản ưu tiên hiện hành.
    - rain_mm: tổng lượng mưa dự báo 3 ngày (mm); mưa lớn tự nâng trọng số C4 (thời tiết/ngập).
    - severe_ratio: tỷ lệ điểm nóng mức 'Cần kiểm tra sớm' (0..1); tăng nhẹ ưu tiên C1.
    """
    w_sev, w_freq, w_road = [max(5.0, float(x)) for x in weights]
    sev_boost = 1.0 + 0.20 * float(np.clip(severe_ratio, 0.0, 1.0))
    c1_raw = w_sev * sev_boost
    c2_raw = w_road
    c3_raw = w_freq
    c123_sum = c1_raw + c2_raw + c3_raw

    if rain_mm is not None and float(rain_mm) > 5.0:
        rain_factor = min(1.0, (float(rain_mm) - 5.0) / 45.0)
        p4 = 0.095 + 0.145 * rain_factor
    else:
        p4 = 0.095

    rem = 1.0 - p4
    p1 = rem * (c1_raw / c123_sum)
    p2 = rem * (c2_raw / c123_sum)
    p3 = rem * (c3_raw / c123_sum)

    snapped = build_pairwise_matrix(
        _snap_saaty(p1 / p2),
        _snap_saaty(p1 / p3),
        _snap_saaty(p1 / p4),
        _snap_saaty(p2 / p3),
        _snap_saaty(p2 / p4),
        _snap_saaty(p3 / p4),
    )
    meta = compute_ahp_weights(snapped)
    if meta['is_consistent']:
        return snapped, meta

    exact = build_pairwise_matrix(p1 / p2, p1 / p3, p1 / p4, p2 / p3, p2 / p4, p3 / p4)
    return exact, compute_ahp_weights(exact)


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
