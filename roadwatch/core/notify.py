"""Thông báo Telegram (tùy chọn). Token/chat id lấy từ biến môi trường hoặc secrets."""
import json
import urllib.request

from .config import cfg


def telegram_configured():
    return bool(cfg('TELEGRAM_BOT_TOKEN') and cfg('TELEGRAM_CHAT_ID'))


def send_telegram(text, timeout=8):
    token, chat = cfg('TELEGRAM_BOT_TOKEN'), cfg('TELEGRAM_CHAT_ID')
    if not (token and chat):
        return False
    try:
        req = urllib.request.Request(
            f'https://api.telegram.org/bot{token}/sendMessage',
            data=json.dumps({'chat_id': chat, 'text': text}).encode('utf-8'),
            headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def alert_text(report):
    return (f"⚠️ RoadWatch: điểm cần kiểm tra sớm\n{report.get('location_name')}\n"
            f"Mã: {report.get('id')} | Điểm: {report.get('final_score')}\n"
            f"https://www.google.com/maps/search/?api=1&query={report.get('latitude')},{report.get('longitude')}")
