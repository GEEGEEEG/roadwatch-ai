"""Cấu hình: ưu tiên biến môi trường, sau đó st.secrets, sau đó giá trị mặc định."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def cfg(name, default=''):
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def data_dir() -> Path:
    path = Path(cfg('ROADWATCH_DATA', str(PROJECT_ROOT / 'data')))
    for sub in ('images', 'annotated', 'after', 'test_images'):
        (path / sub).mkdir(parents=True, exist_ok=True)
    return path


def model_path() -> Path:
    return Path(cfg('ROADWATCH_MODEL', str(PROJECT_ROOT / 'models' / 'model.pt')))
