"""Sao lưu / khôi phục toàn bộ dữ liệu (DB + ảnh) thành một file zip."""
import io
import zipfile
from pathlib import Path

from .config import data_dir


def make_backup() -> bytes:
    root = data_dir()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in root.rglob('*'):
            if p.is_file() and 'test_images' not in p.parts:
                z.write(p, p.relative_to(root).as_posix())
    return buf.getvalue()


def restore_backup(data: bytes):
    root = data_dir().resolve()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            target = (root / info.filename).resolve()
            if root not in target.parents and target != root:
                raise ValueError('File zip chứa đường dẫn không an toàn.')
        z.extractall(root)
