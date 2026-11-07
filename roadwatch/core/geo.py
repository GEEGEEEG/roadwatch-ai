"""Hàm địa lý: khoảng cách, gom điểm nóng, lộ trình, liên kết bản đồ."""
from urllib.parse import quote

import numpy as np

R_EARTH = 6371000.0


def haversine_m(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * R_EARTH * np.arcsin(np.sqrt(a))


def cluster_points(lats, lons, radius_m=40.0):
    """Gom theo 'điểm hạt giống': điểm thuộc cụm nếu cách hạt giống <= radius_m.
    Không nối chuỗi nên một tuyến dài không bị gộp thành một điểm nóng."""
    lats, lons = np.asarray(lats, float), np.asarray(lons, float)
    seeds, labels = [], []
    for la, lo in zip(lats, lons):
        best, best_d = None, None
        for idx, (sl, so) in enumerate(seeds):
            d = float(haversine_m(la, lo, sl, so))
            if d <= radius_m and (best_d is None or d < best_d):
                best, best_d = idx, d
        if best is None:
            seeds.append((la, lo))
            best = len(seeds) - 1
        labels.append(best)
    return np.array(labels, dtype=int)


def nearby_points(df, lat, lon, max_m, statuses=None):
    """Các bản ghi trong df cách (lat, lon) <= max_m mét, gần nhất trước.
    Trả về [(id, khoảng_cách_m, tên_vị_trí)]. statuses: chỉ lấy các trạng thái này (tùy chọn)."""
    if df is None or len(df) == 0:
        return []
    d = df.dropna(subset=['latitude', 'longitude'])
    if statuses is not None:
        d = d[d.status.isin(statuses)]
    if d.empty:
        return []
    dist = haversine_m(float(lat), float(lon), d.latitude.astype(float).values, d.longitude.astype(float).values)
    hits = [(i, float(x), n) for i, x, n in zip(d.id, dist, d.location_name) if x <= max_m]
    return sorted(hits, key=lambda t: t[1])


def maps_link(lat, lon):
    return f'https://www.google.com/maps/dir/?api=1&destination={lat},{lon}'


def maps_multi_link(points, origin=None):
    """points: [(lat, lon), ...]. Google Maps chỉ nhận khoảng 9 điểm trung gian."""
    if not points:
        return ''
    dest = points[-1]
    url = f'https://www.google.com/maps/dir/?api=1&destination={dest[0]},{dest[1]}'
    if origin:
        url += f'&origin={origin[0]},{origin[1]}'
    mid = points[:-1][:9]
    if mid:
        url += '&waypoints=' + quote('|'.join(f'{a},{b}' for a, b in mid), safe=',')
    return url


def nearest_neighbor_route(points, start=None):
    """points: [(id, lat, lon)]. Trả về [(id, lat, lon, leg_m)] theo thứ tự láng giềng gần nhất."""
    remaining = list(points)
    if not remaining:
        return []
    if start is None:
        cur = remaining.pop(0)
        route, leg = [(*cur, 0.0)], None
        pos = (cur[1], cur[2])
    else:
        route, pos = [], tuple(start)
    while remaining:
        dists = [float(haversine_m(pos[0], pos[1], p[1], p[2])) for p in remaining]
        i = int(np.argmin(dists))
        nxt = remaining.pop(i)
        route.append((*nxt, round(dists[i], 1)))
        pos = (nxt[1], nxt[2])
    return route


def reverse_geocode(lat, lon, timeout=3.5):
    """Tra cứu địa chỉ / tên đường từ tọa độ qua OpenStreetMap Nominatim.
    Không cần khóa API. Lỗi mạng hoặc quá thời gian -> None, không gây lỗi app."""
    import json
    import urllib.request
    try:
        lat_f, lon_f = float(lat), float(lon)
        if not (-90 <= lat_f <= 90 and -180 <= lon_f <= 180):
            return None
        url = (f'https://nominatim.openstreetmap.org/reverse?lat={lat_f}&lon={lon_f}'
               f'&format=jsonv2&accept-language=vi')
        req = urllib.request.Request(
            url, headers={'User-Agent': 'RoadWatchAI-Geocoding/1.0 (contact: roadwatch@example.com)'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode('utf-8'))
        addr = data.get('address', {})
        road = addr.get('road') or addr.get('pedestrian') or addr.get('highway') or addr.get('path')
        suburb = addr.get('suburb') or addr.get('quarter') or addr.get('neighbourhood') or addr.get('ward')
        district = addr.get('city_district') or addr.get('district') or addr.get('county')
        city = addr.get('city') or addr.get('state') or addr.get('province')

        parts = [p for p in (road, suburb, district, city) if p]
        if parts:
            return ', '.join(parts)
        disp = data.get('display_name', '')
        return disp[:120] if disp else None
    except Exception:
        return None
