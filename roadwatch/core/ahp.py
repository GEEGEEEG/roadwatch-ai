"""Mô hình ra quyết định đa tiêu chí AHP (Analytic Hierarchy Process) theo chuẩn Thomas L. Saaty.

Hỗ trợ xếp hạng thứ tự ưu tiên duy tu đường bộ dựa trên ma trận so sánh cặp giữa các tiêu chí:
- C1: Mức độ nghiêm trọng hư hại (AI & diện tích m²)
- C2: Tầm quan trọng tuyến đường (Cấp đường)
- C3: Tần suất phản ánh & mức độ bức xúc của cử tri
- C4: Rủi ro thời tiết & ngập úng
"""
import numpy as np

# Bảng chỉ số ngẫu nhiên ngẫu nhiên Saaty (Random Index - RI) cho n=1..10
RI_DICT = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.89, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}

# Ma trận so sánh cặp mặc định chuyên ngành giao thông (4 tiêu chí: Nghiêm trọng, Cấp đường, Cử tri, Thời tiết)
# Tỷ lệ thang điểm Saaty 1-9:
# C1 ưu tiên hơn C2 gấp 2 lần, ưu tiên hơn C3 gấp 3 lần, ưu tiên hơn C4 gấp 4 lần
DEFAULT_AHP_MATRIX = np.array([
    [1.0, 2.0, 3.0, 4.0],      # C1: Mức độ nghiêm trọng
    [1/2, 1.0, 2.0, 3.0],      # C2: Cấp đường
    [1/3, 1/2, 1.0, 2.0],      # C3: Tần suất cử tri
    [1/4, 1/3, 1/2, 1.0],      # C4: Thời tiết / ngập úng
], dtype=float)


def compute_ahp_weights(matrix=None):
    """Tính toán vector trọng số (Eigenvector) và Tỷ số nhất quán (Consistency Ratio - CR).

    Trả về:
    {
        'weights': array([w1, w2, w3, w4]),
        'lambda_max': float,
        'CI': float (Consistency Index),
        'CR': float (Consistency Ratio),
        'is_consistent': bool (CR < 0.10)
    }
    """
    a = np.asarray(matrix if matrix is not None else DEFAULT_AHP_MATRIX, dtype=float)
    n = a.shape[0]

    # Phương pháp trung bình hình học chuẩn hóa (Geometric Mean Method)
    geom_means = np.prod(a, axis=1) ** (1.0 / n)
    weights = geom_means / np.sum(geom_means)

    # Tính lambda_max
    aw = np.dot(a, weights)
    lambda_max = float(np.mean(aw / weights))

    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    ri = RI_DICT.get(n, 1.49)
    cr = (ci / ri) if ri > 0 else 0.0

    return {
        'weights': np.round(weights, 4),
        'lambda_max': round(lambda_max, 4),
        'CI': round(ci, 4),
        'CR': round(cr, 4),
        'is_consistent': bool(cr < 0.10),
    }


def compute_ahp_priority(severity_score, road_score, frequency_score, weather_score=0.0, custom_matrix=None):
    """Tính điểm ưu tiên sửa chữa (0 - 100) theo phương pháp toán học AHP."""
    res = compute_ahp_weights(custom_matrix)
    w = res['weights']
    s = (w[0] * float(severity_score) +
         w[1] * float(road_score) +
         w[2] * float(frequency_score) +
         w[3] * float(weather_score))
    return round(float(np.clip(s, 0.0, 100.0)), 2), res
