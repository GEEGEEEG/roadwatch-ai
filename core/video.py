"""Khảo sát bằng video + file GPX: lấy khung hình theo mốc thời gian, nội suy tọa độ."""
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


def parse_gpx(data: bytes):
    """Trả về [(epoch_seconds, lat, lon)] sắp theo thời gian."""
    root = ET.fromstring(data)
    pts = []
    for el in root.iter():
        if el.tag.split('}')[-1] != 'trkpt':
            continue
        t = next((c.text for c in el if c.tag.split('}')[-1] == 'time'), None)
        if not t:
            continue
        dt = datetime.fromisoformat(t.strip().replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        pts.append((dt.timestamp(), float(el.attrib['lat']), float(el.attrib['lon'])))
    return sorted(pts)


def interpolate(track, t):
    """Nội suy tuyến tính; ngoài khoảng GPX trả về None (không ngoại suy)."""
    if not track or t < track[0][0] or t > track[-1][0]:
        return None
    for (t0, la0, lo0), (t1, la1, lo1) in zip(track, track[1:]):
        if t0 <= t <= t1:
            f = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            return la0 + f * (la1 - la0), lo0 + f * (lo1 - lo0)
    return track[-1][1], track[-1][2]


def sample_frames(video_path, every_s=2.0, max_frames=150):
    """Sinh (giây_trong_video, PIL.Image). Cần opencv (đi kèm ultralytics)."""
    import cv2
    from PIL import Image
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    step = max(1, int(round(fps * every_s)))
    count, idx = 0, 0
    while count < max_frames:
        if total and idx >= total:
            break
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            break
        yield idx / fps, Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        idx += step
        count += 1
    cap.release()
