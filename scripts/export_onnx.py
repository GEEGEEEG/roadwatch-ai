"""Tiện ích xuất trọng số YOLOv8 (.pt) sang ONNX Runtime (.onnx) giúp giảm ~65% RAM trên Streamlit Cloud.

Cách chạy trên máy cá nhân (tùy chọn):
    python scripts/export_onnx.py
"""
import json
from pathlib import Path


def export_model_to_onnx(pt_path: Path | None = None, imgsz: int = 800) -> Path:
    root = Path(__file__).resolve().parent.parent
    src = Path(pt_path) if pt_path else (root / 'models' / 'model.pt')
    if not src.is_file():
        raise FileNotFoundError(f'Không tìm thấy checkpoint gốc tại: {src}')

    from ultralytics import YOLO
    model = YOLO(str(src))
    exported = Path(model.export(format='onnx', imgsz=imgsz, simplify=True, dynamic=False))
    meta_file = exported.with_suffix('.json')
    meta_file.write_text(json.dumps({'names': model.names, 'imgsz': imgsz}, ensure_ascii=False, indent=2), encoding='utf-8')
    return exported


if __name__ == '__main__':
    out_file = export_model_to_onnx()
    print(f'✅ Đã xuất mô hình ONNX thành công tại: {out_file}')
