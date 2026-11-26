"""Gom cụm tuyến đường xuống cấp diện rộng (Pavement Hotspot Corridor Clustering v5.0).

Cải tiến:
- Tính toán dự toán chi phí đúng theo số lượng điểm trong cụm (`point_count=c_size`).
- Trả thêm `ordered_coords` sắp dọc theo trục chính của đoạn đường để vẽ trực tiếp Hành lang đỏ lên bản đồ GIS Folium.
"""
import numpy as np
import pandas as pd

from .constants import ACTIVE_STATUSES
from .cost_estimation import estimate_maintenance_cost
from .geo import haversine_m


def analyze_corridor_clusters(df_reports, max_distance_m: float = 250.0, min_cluster_size: int = 3) -> list[dict]:
    """Phân tích các hành lang hư hỏng diện rộng trên tập báo cáo đang hoạt động."""
    if df_reports is None or df_reports.empty:
        return []

    d = df_reports[df_reports.status.isin(ACTIVE_STATUSES)].copy()
    d = d.dropna(subset=['latitude', 'longitude']).reset_index(drop=True)
    if d.empty:
        return []

    n = len(d)
    lats = d['latitude'].astype(float).values
    lons = d['longitude'].astype(float).values

    dist_matrix = np.zeros((n, n), dtype=float)
    for i in range(n):
        dist_matrix[i] = haversine_m(lats[i], lons[i], lats, lons)

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
        c_lats = sub_df['latitude'].astype(float).values
        c_lons = sub_df['longitude'].astype(float).values

        max_span_m = float(dist_matrix[cluster_indices][:, cluster_indices].max()) if c_size > 1 else 0.0

        if 'damage_area_m2' in sub_df.columns:
            tot_area_m2 = float(sub_df['damage_area_m2'].fillna(0.15).clip(lower=0.05).sum())
        else:
            tot_area_m2 = 0.15 * c_size

        if 'damage_volume_l' in sub_df.columns:
            tot_volume_l = float(sub_df['damage_volume_l'].fillna(5.0).clip(lower=0.0).sum())
        else:
            tot_volume_l = 5.0 * c_size

        cost_est = estimate_maintenance_cost(tot_area_m2, tot_volume_l, point_count=c_size)

        loc_names = [str(x).strip() for x in sub_df['location_name'].dropna().tolist() if str(x).strip()]
        rep_loc = loc_names[0] if loc_names else 'Tuyến đường chưa đặt tên'

        # Sắp xếp tọa độ dọc theo phương trải dài chính để vẽ đường bao hành lang mượt trên bản đồ
        lat_span = float(np.ptp(c_lats))
        lon_span = float(np.ptp(c_lons))
        order_idx = np.argsort(c_lats if lat_span >= lon_span else c_lons)
        ordered_coords = [(round(float(c_lats[k]), 6), round(float(c_lons[k]), 6)) for k in order_idx]

        is_wide_degradation = c_size >= min_cluster_size
        if is_wide_degradation:
            proposal = 'Xuống cấp diện rộng: Khuyến nghị thảm lại toàn bộ mặt đường'
            action_code = 'RESURFACE'
        else:
            proposal = 'Hư hỏng cục bộ: Khuyến nghị dặm vá tại chỗ'
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
            'ordered_coords': ordered_coords,
            'total_area_m2': round(tot_area_m2, 3),
            'total_cost_vnd': cost_est['total_estimate_vnd'],
            'formatted_cost': cost_est['formatted_total'],
            'material_detail': cost_est['material_detail'],
            'report_ids': sub_df['id'].tolist(),
        })

    return sorted(clusters, key=lambda x: (x['is_wide_degradation'], x['cluster_size'], x['total_cost_vnd']), reverse=True)
