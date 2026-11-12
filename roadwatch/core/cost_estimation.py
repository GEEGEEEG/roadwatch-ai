"""Dự toán khối lượng vật tư và kinh phí sửa chữa mặt đường theo định mức giao thông đô thị Việt Nam.

Hỗ trợ các loại kết cấu mặt đường:
1. Nhựa đường nguội (Carboncor Asphalt / Cold Mix - vá nhanh ổ gà điểm lẻ)
2. Bê tông nhựa nóng (BTN hạt mịn C12.5 / C9.5 - thảm dặm vá diện rộng)
3. Bê tông xi măng (Đường nội bộ / nông thôn)
"""
import math

# Định mức tham chiếu theo đơn giá duy tu đường bộ hiện hành (VNĐ)
UNIT_PRICES = {
    'carboncor_bag_25kg': 145000,       # 145.000 đ / bao 25kg
    'btn_hot_mix_m2': 380000,          # 380.000 đ / m² (đã gồm lu lèn, tưới dính bám)
    'concrete_m3': 1350000,            # 1.350.000 đ / m³
    'labor_per_point': 150000,         # Chi phí nhân công dặm vá 1 điểm lẻ
}

DENSITY_ASPHALT_KG_M3 = 2400.0         # Tỷ trọng bê tông nhựa ~ 2.4 tấn/m³
DEFAULT_PATCH_THICKNESS_M = 0.05       # Độ dày vá trung bình 5 cm (0.05 m)


def estimate_maintenance_cost(area_m2, volume_l=0.0, road_material='asphalt'):
    """Tính toán dự trù khối lượng vật tư và chi phí sửa chữa.

    Trả về chi tiết:
    - Khối lượng vật tư cần xuất kho (số bao / tấn / m³)
    - Chi phí vật tư
    - Chi phí thi công & tổng dự toán (VNĐ)
    """
    area = max(0.05, float(area_m2 or 0.0))  # Tối thiểu 0.05 m² cho vết nứt nhỏ

    # Thể tích dặm vá (m³)
    if volume_l and volume_l > 0:
        vol_m3 = volume_l / 1000.0
    else:
        vol_m3 = area * DEFAULT_PATCH_THICKNESS_M

    if road_material == 'concrete':
        vol_needed = round(vol_m3, 3)
        mat_cost = vol_needed * UNIT_PRICES['concrete_m3']
        labor_cost = UNIT_PRICES['labor_per_point']
        total_cost = mat_cost + labor_cost
        material_detail = f'{vol_needed:.2f} m³ Bê tông xi măng Mác 250'
    else:
        # Nhựa đường: tính theo khối lượng (kg)
        kg_needed = vol_m3 * DENSITY_ASPHALT_KG_M3
        bags_25kg = math.ceil(kg_needed / 25.0)

        # Nếu diện tích < 0.5 m² dùng nhựa nguội bao 25kg; nếu >= 0.5 m² dùng thảm BTN
        if area < 0.5:
            mat_cost = bags_25kg * UNIT_PRICES['carboncor_bag_25kg']
            labor_cost = UNIT_PRICES['labor_per_point']
            total_cost = mat_cost + labor_cost
            material_detail = f'{bags_25kg} bao (25kg/bao) Nhựa nguội Carboncor ({kg_needed:.1f} kg)'
        else:
            mat_cost = area * UNIT_PRICES['btn_hot_mix_m2']
            labor_cost = UNIT_PRICES['labor_per_point'] * 1.5
            total_cost = mat_cost + labor_cost
            material_detail = f'Thảm nhựa nóng BTN hạt mịn ({area:.2f} m²)'

    return {
        'area_m2': round(area, 3),
        'volume_m3': round(vol_m3, 4),
        'material_detail': material_detail,
        'material_cost_vnd': int(round(mat_cost)),
        'labor_cost_vnd': int(round(labor_cost)),
        'total_estimate_vnd': int(round(total_cost)),
        'formatted_total': f'{int(round(total_cost)):,} VNĐ'.replace(',', '.'),
    }
