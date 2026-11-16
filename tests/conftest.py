import io
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def tmp_data(tmp_path, monkeypatch):
    monkeypatch.setenv('ROADWATCH_DATA', str(tmp_path / 'data'))
    monkeypatch.setenv('ROADWATCH_OFFICER_PASSWORD', 'secret')
    monkeypatch.delenv('TELEGRAM_BOT_TOKEN', raising=False)
    from core import db
    db.init()
    return tmp_path


def make_jpeg(seed=0, size=(640, 480)):
    img = Image.new('RGB', size, (120, 120, 120))
    d = ImageDraw.Draw(img)
    import random
    rnd = random.Random(seed)
    for _ in range(60):
        x, y = rnd.randint(0, size[0]), rnd.randint(0, size[1])
        d.line((x, y, x + rnd.randint(-80, 80), y + rnd.randint(-80, 80)), fill=(rnd.randint(0, 255),) * 3, width=2)
    buf = io.BytesIO()
    img.save(buf, 'JPEG')
    return buf.getvalue()


class FakeDetector:
    """Chỉ dùng trong kiểm thử: trả về kết quả cố định, không phải dữ liệu thật."""
    def __init__(self, dets=None):
        self.dets = dets if dets is not None else [
            {'class_code': 'D40', 'class_name': 'Ổ gà', 'confidence': 0.8, 'bbox_xyxy': [10, 10, 200, 200], 'bbox_area_percent': 11.8}]

    def predict_image(self, image, threshold=0.25, imgsz=640, tta=False, class_thresholds=None):
        from core.detector import draw_detections, severity_rule
        dets = [d for d in self.dets if d['confidence'] >= threshold]
        w, h = image.size
        return {'annotated_image': draw_detections(image.convert('RGB'), dets), 'detections': dets,
                'elapsed_ms': 12.0, 'severity': severity_rule(dets, w, h), 'image_size': (w, h)}
