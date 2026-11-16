"""Điểm nóng + xếp hạng ưu tiên (mặc định 50% mức độ - 30% tần suất - 20% tuyến đường)."""
import numpy as np
import pandas as pd

from .constants import ACTIVE_STATUSES, LEVEL_POINTS, LEVELS
from .geo import cluster_points

DEFAULT_WEIGHTS = (0.50, 0.30, 0.20)


def normalize_weights(weights):
    a, b, c = [max(0.0, float(w)) for w in weights]
    total = a + b + c
    return DEFAULT_WEIGHTS if total == 0 else (a / total, b / total, c / total)


def final_score(ai_level, ai_score, manual_level):
    """Giữ nguyên điểm quy tắc nếu người duyệt đồng ý; nếu đổi mức thì dịch điểm theo chênh lệch mức."""
    if manual_level == ai_level:
        return float(ai_score)
    delta = LEVEL_POINTS[manual_level] - LEVEL_POINTS[ai_level]
    return float(np.clip(float(ai_score) + delta, 0, 100))


def level_from_score(score):
    return 'Cần kiểm tra sớm' if score >= 70 else ('Trung bình' if score >= 45 else ('Nhẹ' if score > 0 else 'Không phát hiện'))


def build_hotspots(df, weights=DEFAULT_WEIGHTS, radius_m=40.0, use_trend=True, weather_bonus=None):
    """df: các bản ghi đã xác minh. weather_bonus: dict {hotspot_id: điểm cộng} (tùy chọn)."""
    if df is None or df.empty:
        return pd.DataFrame()
    d = df[df.status.isin(ACTIVE_STATUSES)].copy()
    d = d.dropna(subset=['latitude', 'longitude'])
    if d.empty:
        return pd.DataFrame()
    d = d.sort_values('created_at').reset_index(drop=True)
    d['hotspot_id'] = cluster_points(d.latitude, d.longitude, radius_m)
    a, b, c = normalize_weights(weights)
    merged_by_parent = {}
    if 'merged_into' in df.columns:
        m = df[(df.status == 'merged') & df.merged_into.notna()]
        merged_by_parent = m.groupby('merged_into').id.apply(list).to_dict()
    rows = []
    for hid, g in d.groupby('hotspot_id'):
        g = g.sort_values('created_at')
        worst = g.loc[g.final_score.fillna(0).idxmax()]
        merged_ids = [x for pid in g.id for x in merged_by_parent.get(pid, [])]
        count = len(g) + len(merged_ids)
        sev = float(np.clip(g.final_score.fillna(0).max(), 0, 100))
        freq = min(count, 10) * 10.0
        road = float(np.clip(g.road_score.fillna(0).max(), 0, 100))
        trend_delta = float(g.final_score.iloc[-1] - g.final_score.iloc[0]) if count >= 2 else 0.0
        trend_bonus = float(np.clip(trend_delta / 10, 0, 5)) if use_trend else 0.0
        wb = float((weather_bonus or {}).get(hid, 0.0))
        score = float(np.clip(a * sev + b * freq + c * road + trend_bonus + wb, 0, 100))
        extra = f'; gồm {len(merged_ids)} phản ánh đã gộp' if merged_ids else ''
        reason = f'{a:.0%} mức độ ({sev:.0f}) + {b:.0%} tần suất ({freq:.0f}{extra}) + {c:.0%} tuyến ({road:.0f})'
        if trend_bonus:
            reason += f' + xu hướng nặng thêm (+{trend_bonus:.1f})'
        if wb:
            reason += f' + dự báo mưa (+{wb:.1f})'
        rows.append({
            'hotspot_id': int(hid), 'location_name': g.location_name.iloc[-1],
            'latitude': round(float(g.latitude.mean()), 6), 'longitude': round(float(g.longitude.mean()), 6),
            'report_count': count, 'severity_component': round(sev, 1), 'frequency_component': freq,
            'road_component': road, 'trend_bonus': round(trend_bonus, 2), 'weather_bonus': round(wb, 2),
            'priority_score': round(score, 2), 'severity_label': level_from_score(sev),
            'road_type': worst.road_type, 'worst_report_id': worst.id,
            'member_ids': list(g.id), 'merged_count': len(merged_ids), 'merged_ids': merged_ids, 'first_seen': g.created_at.iloc[0], 'last_seen': g.created_at.iloc[-1],
            'has_pothole': bool((g.count_D40.fillna(0) > 0).any()), 'ranking_reason': reason,
        })
    out = pd.DataFrame(rows).sort_values('priority_score', ascending=False).reset_index(drop=True)
    out['priority_rank'] = out.index + 1
    return out


def compare_rankings(df, weights_a, weights_b, radius_m=40.0):
    """Bảng so sánh thứ hạng giữa hai bộ trọng số + hệ số Spearman (Pearson trên hạng, hạng không trùng)."""
    ra = build_hotspots(df, weights_a, radius_m, use_trend=False)
    rb = build_hotspots(df, weights_b, radius_m, use_trend=False)
    if ra.empty or rb.empty:
        return pd.DataFrame(), None
    m = ra[['hotspot_id', 'location_name', 'priority_score', 'priority_rank']].merge(
        rb[['hotspot_id', 'priority_score', 'priority_rank']], on='hotspot_id', suffixes=('_A', '_B'))
    m['rank_change'] = m['priority_rank_A'] - m['priority_rank_B']   # dương = lên hạng khi chuyển sang B
    rho = None
    if len(m) >= 2:
        rho = float(np.corrcoef(m.priority_rank_A, m.priority_rank_B)[0, 1])
    return m, rho
