LABELS = {'D00': 'Nứt dọc', 'D10': 'Nứt ngang', 'D20': 'Nứt dạng mạng', 'D40': 'Ổ gà'}
BASE = {'D00': 25, 'D10': 35, 'D20': 60, 'D40': 75}
COLORS = {'D00': '#38A3D1', 'D10': '#1BA673', 'D20': '#E89D33', 'D40': '#D94848'}

LEVELS = ['Không phát hiện', 'Nhẹ', 'Trung bình', 'Cần kiểm tra sớm']
LEVEL_POINTS = {'Không phát hiện': 0.0, 'Nhẹ': 30.0, 'Trung bình': 60.0, 'Cần kiểm tra sớm': 90.0}

ROAD_TYPES = {
    'Trục chính / Quốc lộ (minh họa)': 90,
    'Đường gần trường học, bệnh viện (minh họa)': 75,
    'Đường khu dân cư (minh họa)': 50,
    'Đường nhánh ít lưu lượng (minh họa)': 30,
}

STATUS_LABELS = {
    'pending': 'Chờ xác minh', 'verified': 'Đã xác minh', 'rejected': 'Từ chối',
    'assigned': 'Đã giao kiểm tra', 'fixed': 'Đã xử lý', 'merged': 'Đã gộp',
}
DUP_FLAG_M = 30.0    # trong bán kính này: gắn nhãn "có thể trùng điểm"
MERGE_MAX_M = 50.0   # cán bộ được phép gộp vào điểm hiện hữu trong bán kính này
ACTIVE_STATUSES = ('verified', 'assigned')   # chỉ các trạng thái này được tính vào xếp hạng

DISCLAIMER = ('Bản demo hỗ trợ học tập/kỹ thuật. Mức độ và điểm ưu tiên là **quy tắc do nhóm thiết kế**, '
              'không đo độ sâu, diện tích thực, chi phí hay rủi ro tai nạn; luôn cần cán bộ kỹ thuật kiểm tra hiện trường.')
