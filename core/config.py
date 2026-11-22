"""Cấu hình hệ thống: ưu tiên biến môi trường, sau đó st.secrets, cuối cùng là mặc định."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def cfg(name: str, default: str = '') -> str:
    value = os.environ.get(name) or os.environ.get(name.lower())
    if value:
        return str(value).strip()
    try:
        import streamlit as st
        val = st.secrets.get(name, '') or st.secrets.get(name.lower(), '')
        if val != '':
            return str(val).strip()
    except Exception:
        pass
    return str(default).strip() if default is not None else ''


def cfg_bool(name: str, default: bool = False) -> bool:
    raw = cfg(name, '')
    if not raw:
        return default
    return raw.lower() in ('1', 'true', 'yes', 'on', 'enabled')


def demo_mode_enabled() -> bool:
    """Bật chế độ Demo cho Hội đồng chấm thi khi đặt ROADWATCH_DEMO_MODE = 'true' trong Secrets.
    Nếu chạy hoàn toàn offline ở máy cá nhân (chưa cấu hình Supabase & chưa đặt mật khẩu quản trị),
    tự động bật chế độ Demo cục bộ để sinh viên/giảng viên chạy thử ngay."""
    explicit = cfg('ROADWATCH_DEMO_MODE', '')
    if explicit:
        return explicit.lower() in ('1', 'true', 'yes', 'on')
    has_cloud = bool(cfg('SUPABASE_URL') or cfg('SUPABASE_SERVICE_ROLE_KEY') or cfg('SUPABASE_KEY'))
    has_admin_pw = bool(cfg('ROADWATCH_ADMIN_PASSWORD') or cfg('ROADWATCH_OFFICER_PASSWORD'))
    return not has_cloud and not has_admin_pw


def data_dir() -> Path:
    path = Path(cfg('ROADWATCH_DATA', str(PROJECT_ROOT / 'data')))
    for sub in ('images', 'annotated', 'after', 'test_images'):
        (path / sub).mkdir(parents=True, exist_ok=True)
    return path


def model_path() -> Path:
    custom = cfg('ROADWATCH_MODEL', '')
    if custom:
        return Path(custom)
    for base in (PROJECT_ROOT, PROJECT_ROOT.parent):
        onnx_cand = base / 'models' / 'model.onnx'
        if onnx_cand.is_file():
            return onnx_cand
        pt_cand = base / 'models' / 'model.pt'
        if pt_cand.is_file():
            return pt_cand
    return PROJECT_ROOT / 'models' / 'model.pt'
