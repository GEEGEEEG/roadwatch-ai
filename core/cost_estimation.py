"""Dự toán khối lượng vật tư và kinh phí sửa chữa mặt đường theo định mức giao thông đô thị Việt Nam (v5.0).

Cải tiến:
- Hỗ trợ tính toán chi phí nhân công & huy động máy theo số điểm thực tế (`point_count`) thay vì gộp sai cả thành phố thành 1 điểm.
- Cho phép truyền bảng đơn giá tùy chỉnh (`custom_prices`) từ cấu hình Quản trị.
"""
import math

UNIT_PRICES = {
    'carboncor_bag_25kg': 145000,   # 145.000 đ / bao 25kg
    'btn_hot_mix_m2': 380000,       # 380.000 đ / m² (gồm tưới nhũ tương dính bám & lu lèn)
    'concrete_m3': 1350000,         # 1.350.000 đ / m³
    'labor_per_point': 150000,      # Nhân công vá 1 điểm độc lập
}

DENSITY_ASPHALT_KG_M3 = 2400.0
DEFAULT_PATCH_THICKNESS_M = 0.05


def estimate_maintenance_cost(
    area_m2: float,
    volume_l: float = 0.0,
    road_material: str = 'asphalt',
    point_count: int = 1,
    custom_prices: dict | None = None,
) -> dict:
    """Tính dự trù khối lượng vật tư và kinh phí sửa chữa (VNĐ)."""
    prices = {**UNIT_PRICES, **(custom_prices or {})}
    n_pts = max(1, int(point_count or 1))
    area = max(0.05 * n_pts if area_m2 and area_m2 > 0 else 0.05, float(area_m2 or 0.0))

    if volume_l and volume_l > 0:
        vol_m3 = float(volume_l) / 1000.0
    else:
        vol_m3 = area * DEFAULT_PATCH_THICKNESS_M

    # Hệ số kinh tế theo quy mô khi thi công nhiều điểm cùng đợt (giảm 20% nhân công từ điểm thứ 2 trở đi)
    effective_points = 1.0 + 0.8 * (n_pts - 1)

    if road_material == 'concrete':
        vol_needed = round(vol_m3, 3)
        mat_cost = vol_needed * prices['concrete_m3']
        labor_cost = prices['labor_per_point'] * effective_points
        material_detail = f'{vol_needed:.2f} m³ Bê tông xi măng Mác 250'
    else:
        kg_needed = vol_m3 * DENSITY_ASPHALT_KG_M3
        bags_25kg = max(1, math.ceil(kg_needed / 25.0))

        if area < 0.5 and n_pts <= 2:
            mat_cost = bags_25kg * prices['carboncor_bag_25kg']
            labor_cost = prices['labor_per_point'] * effective_points
            material_detail = f'{bags_25kg} bao (25kg/bao) Nhựa nguội Carboncor ({kg_needed:.1f} kg)'
        else:
            mat_cost = area * prices['btn_hot_mix_m2']
            labor_cost = prices['labor_per_point'] * max(1.5, effective_points)
            material_detail = f'Thảm nhựa nóng BTN hạt mịn ({area:.2f} m² · {n_pts} vị trí)' if n_pts > 1 else f'Thảm nhựa nóng BTN hạt mịn ({area:.2f} m²)'

    total_cost = mat_cost + labor_cost
    return {
        'area_m2': round(area, 3),
        'volume_m3': round(vol_m3, 4),
        'point_count': n_pts,
        'material_detail': material_detail,
        'material_cost_vnd': int(round(mat_cost)),
        'labor_cost_vnd': int(round(labor_cost)),
        'total_estimate_vnd': int(round(total_cost)),
        'formatted_total': f'{int(round(total_cost)):,} VNĐ'.replace(',', '.'),
    }
