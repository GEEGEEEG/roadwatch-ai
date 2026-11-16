"""Dự báo mưa 3 ngày từ Open-Meteo (không cần khóa). Lỗi mạng -> None, không làm hỏng ứng dụng."""
import json
import urllib.request


def fetch_rain_forecast(lat, lon, days=3, timeout=6):
    url = ('https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&daily=precipitation_sum'
           '&forecast_days=%d&timezone=auto' % (lat, lon, days))
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            data = json.loads(r.read().decode('utf-8'))
        vals = [float(v or 0) for v in data['daily']['precipitation_sum']]
        return {'total_mm': round(sum(vals), 1), 'daily_mm': vals, 'dates': data['daily']['time']}
    except Exception:
        return None


def rain_bonus(total_mm, has_pothole, max_bonus=5.0):
    """Quy tắc giả định: có ổ gà + dự báo mưa nhiều -> cộng tối đa max_bonus điểm."""
    if not has_pothole or not total_mm:
        return 0.0
    return round(min(max_bonus, max_bonus * total_mm / 50.0), 2)
