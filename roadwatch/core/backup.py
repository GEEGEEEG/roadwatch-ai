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
    if len(data) > 150 * 1024 * 1024:
        raise ValueError('Bản sao lưu vượt giới hạn 150 MB.')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos=z.infolist()
        if len(infos)>2000 or sum(i.file_size for i in infos)>500*1024*1024:
            raise ValueError('Bản sao lưu quá lớn hoặc có quá nhiều tệp.')
        for info in infos:
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Không cho phép symbolic link trong bản sao lưu.')
            target = (root / info.filename).resolve()
            if root not in target.parents and target != root:
                raise ValueError('File zip chứa đường dẫn không an toàn.')
        z.extractall(root)
