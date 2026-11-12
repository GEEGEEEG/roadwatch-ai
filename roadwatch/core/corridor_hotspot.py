"""Gom cụm tuyến đường xuống cấp diện rộng (Pavement Hotspot Corridor Clustering).

Phát hiện các cụm hư hỏng tập trung theo trục đường giao thông (DBSCAN / khoảng cách không gian)
để đề xuất cơ quan quản lý chuyển đổi phương án: từ 'dặm vá chắp vá cục bộ' sang 'thảm lại toàn diện mặt đường'.
"""
import numpy as np
import pandas as pd

from .constants import ACTIVE_STATUSES
from .cost_estimation import estimate_maintenance_cost
from .geo import haversine_m


def analyze_corridor_clusters(df_reports, max_distance_m=250.0, min_cluster_size=3):
    """Phân tích các hành lang hư hỏng diện rộng.

    df_reports: DataFrame chứa các điểm đã duyệt (verified) hoặc đang xử lý.
    max_distance_m: Khoảng cách tối đa giữa các điểm để coi là cùng một đoạn hư hỏng liên hoàn (mặc định 250m).
    min_cluster_size: Số lượng điểm tối thiểu để nâng cấp lên cảnh báo 'Xuống cấp diện rộng' (mặc định 3 điểm).
    """
    if df_reports is None or df_reports.empty:
        return []

    d = df_reports[df_reports.status.isin(ACTIVE_STATUSES)].copy()
    d = d.dropna(subset=['latitude', 'longitude']).reset_index(drop=True)
    if d.empty:
        return []

    n = len(d)
    lats = d['latitude'].astype(float).values
    lons = d['longitude'].astype(float).values

    # Tính ma trận khoảng cách Haversine giữa các điểm
    dist_matrix = np.zeros((n, n), dtype=float)
    for i in range(n):
        dist_matrix[i] = haversine_m(lats[i], lons[i], lats, lons)

    # Gom cụm kiểu liên kết láng giềng (Connected components với ngưỡng max_distance_m)
    visited = set()
    clusters = []

    for i in range(n):
        if i in visited:
            continue
        cluster_indices = []
        queue = [i]
        visited.add(i)

        while queue:
            curr = queue.pop(0)
            cluster_indices.append(curr)
            neighbors = np.where(dist_matrix[curr] <= max_distance_m)[0]
            for nb in neighbors:
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)

        sub_df = d.iloc[cluster_indices]
        c_size = len(sub_df)
        c_lats = sub_df['latitude'].astype(float)
        c_lons = sub_df['longitude'].astype(float)

        # Đo chiều dài đoạn đường bị ảnh hưởng (m)
        max_span_m = float(dist_matrix[cluster_indices][:, cluster_indices].max()) if c_size > 1 else 0.0

        # Tính tổng diện tích hư hại & chi phí dự kiến cho cả cụm
        tot_area_m2 = float(sub_df.get('damage_area_m2', pd.Series([0.15] * c_size)).fillna(0.15).sum())
        tot_volume_l = float(sub_df.get('damage_volume_l', pd.Series([5.0] * c_size)).fillna(5.0).sum())
        cost_est = estimate_maintenance_cost(tot_area_m2, tot_volume_l)

        # Tên tuyến đường đại diện
        loc_names = sub_df['location_name'].dropna().tolist()
        rep_loc = loc_names[0] if loc_names else 'Tuyến đường chưa đặt tên'

        is_wide_degradation = c_size >= min_cluster_size
        if is_wide_degradation:
            proposal = '🚨 Xuống cấp diện rộng: Khuyến nghị thảm lại toàn bộ mặt đường (Overhaul)'
            action_code = 'RESURFACE'
        else:
            proposal = '🛠️ Hư hỏng điểm lẻ: Khuyến nghị dặm vá cục bộ (Patching)'
            action_code = 'PATCH'

        clusters.append({
            'cluster_size': c_size,
            'location_summary': rep_loc,
            'is_wide_degradation': is_wide_degradation,
            'proposal': proposal,
            'action_code': action_code,
            'span_length_m': round(max_span_m, 1),
            'center_lat': round(float(c_lats.mean()), 6),
            'center_lon': round(float(c_lons.mean()), 6),
            'total_area_m2': round(tot_area_m2, 3),
            'total_cost_vnd': cost_est['total_estimate_vnd'],
            'formatted_cost': cost_est['formatted_total'],
            'material_detail': cost_est['material_detail'],
            'report_ids': sub_df['id'].tolist(),
        })

    # Sắp xếp các cụm xuống cấp diện rộng và chi phí lớn lên đầu
    return sorted(clusters, key=lambda x: (x['is_wide_degradation'], x['cluster_size'], x['total_cost_vnd']), reverse=True)
