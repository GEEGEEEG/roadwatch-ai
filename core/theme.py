"""RoadWatch AI - Modern Dashboard & Glassmorphism Design System v5.0."""
import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st

_BG_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'bg'

BG_PRESETS = {
    'golden': {
        'file': 'golden_highway.jpg',
        'bg_pos': 'center 52%',
        'hero_pos': 'center 54%',
        'scrim': 'linear-gradient(106deg, rgba(6, 15, 34, 0.62) 0%, rgba(10, 22, 48, 0.34) 55%, rgba(6, 15, 34, 0.24) 100%)',
        'title': '#FFFFFF',
        'lead': '#F8FAFC',
        'shadow': '0 3px 22px rgba(4, 10, 24, 0.72)',
        'kicker_bg': 'rgba(15, 23, 42, 0.48)',
        'kicker_border': 'rgba(253, 224, 71, 0.50)',
        'kicker_text': '#FEF08A',
        'overline': '#FDE047',
        'glass_bg': 'rgba(10, 20, 40, 0.56)',
        'accent': '#38BDF8',
    },
    'urban': {
        'file': 'urban_avenue.jpg',
        'bg_pos': 'center 50%',
        'hero_pos': 'center 56%',
        'scrim': 'linear-gradient(106deg, rgba(6, 24, 34, 0.74) 0%, rgba(10, 34, 44, 0.46) 58%, rgba(6, 20, 30, 0.30) 100%)',
        'title': '#FFFFFF',
        'lead': '#ECFDF5',
        'shadow': '0 3px 22px rgba(4, 14, 22, 0.72)',
        'kicker_bg': 'rgba(6, 28, 34, 0.56)',
        'kicker_border': 'rgba(110, 231, 183, 0.50)',
        'kicker_text': '#A7F3D0',
        'overline': '#6EE7B7',
        'glass_bg': 'rgba(8, 24, 34, 0.58)',
        'accent': '#34D399',
    },
    'coastal': {
        'file': 'coastal_highway.jpg',
        'bg_pos': 'center 55%',
        'hero_pos': 'center 62%',
        'scrim': 'linear-gradient(106deg, rgba(7, 16, 30, 0.70) 0%, rgba(12, 26, 44, 0.40) 58%, rgba(7, 16, 30, 0.28) 100%)',
        'title': '#FFFFFF',
        'lead': '#E0F2FE',
        'shadow': '0 3px 22px rgba(4, 10, 24, 0.72)',
        'kicker_bg': 'rgba(7, 20, 38, 0.54)',
        'kicker_border': 'rgba(125, 211, 252, 0.50)',
        'kicker_text': '#BAE6FD',
        'overline': '#7DD3FC',
        'glass_bg': 'rgba(9, 19, 36, 0.58)',
        'accent': '#38BDF8',
    },
    'horizon': {
        'file': 'horizon_road.jpg',
        'bg_pos': 'center 64%',
        'hero_pos': 'center 68%',
        'scrim': 'linear-gradient(106deg, rgba(10, 15, 28, 0.78) 0%, rgba(15, 23, 42, 0.52) 56%, rgba(10, 15, 28, 0.36) 100%)',
        'title': '#FFFFFF',
        'lead': '#F1F5F9',
        'shadow': '0 3px 22px rgba(4, 10, 24, 0.76)',
        'kicker_bg': 'rgba(15, 23, 42, 0.62)',
        'kicker_border': 'rgba(251, 191, 36, 0.55)',
        'kicker_text': '#FDE68A',
        'overline': '#FCD34D',
        'glass_bg': 'rgba(13, 19, 34, 0.60)',
        'accent': '#FBBF24',
    },
}

PAGE_BG_MAP = {
    'home': 'golden',
    'submit': 'urban',
    'track': 'urban',
    'compare': 'urban',
    'map': 'coastal',
    'route': 'coastal',
    'video': 'coastal',
    'detail': 'coastal',
    'queue': 'horizon',
    'priority': 'horizon',
    'reports': 'horizon',
    'admin': 'horizon',
    'login': 'horizon',
    'officer-profile': 'horizon',
    'evaluation': 'horizon',
}


@lru_cache(maxsize=8)
def _bg_data_uri(filename: str) -> str:
    p = _BG_DIR / filename
    if not p.is_file():
        return 'none'
    b64 = base64.b64encode(p.read_bytes()).decode('ascii')
    return f'url("data:image/jpeg;base64,{b64}")'

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');

:root {
  color-scheme: light;
  --rw-navy: #0A192F;
  --rw-ink: #0F172A;
  --rw-sub: #475569;
  --rw-blue: #2563EB;
  --rw-blue-dark: #1D4ED8;
  --rw-blue-light: #3B82F6;
  --rw-sky: #F0F7FF;
  --rw-line: #E2E8F0;
  --rw-border-glass: rgba(203, 213, 225, 0.85);
  --rw-bg: #F1F5F9;
  --rw-card-bg: #FFFFFF;
  --rw-shadow-sm: 0 1px 3px rgba(15, 23, 42, 0.05), 0 4px 12px rgba(15, 23, 42, 0.03);
  --rw-shadow-md: 0 8px 24px rgba(15, 23, 42, 0.07);
  --rw-shadow-lg: 0 18px 44px rgba(15, 23, 42, 0.10);
  --rw-radius: 16px;
  --rw-font: 'Be Vietnam Pro', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
p, h1, h2, h3, h4, h5, h6, label, input, textarea, select, button, td, th, li, a,
.stMarkdown, [data-testid="stText"] {
  font-family: var(--rw-font) !important;
}

/* Material Symbols & Icon protection */
[data-testid*="Icon"], 
[class*="material-symbols"], 
[class*="MaterialSymbols"], 
[class*="material-icons"],
[data-testid="stIconMaterial"],
[data-testid="stSidebarCollapseButton"] *,
[data-testid="collapsedControl"] *,
[data-testid="stExpanderToggleIcon"],
[data-testid="stExpander"] summary span:first-child,
.material-symbols-rounded,
.material-symbols-outlined {
  font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
  font-style: normal !important;
  font-weight: normal !important;
  font-variant: normal !important;
  text-transform: none !important;
  display: inline-block !important;
  white-space: nowrap !important;
  direction: ltr !important;
  -webkit-font-smoothing: antialiased !important;
}

/* Main app container — Blurred & Darkened Photographic Backdrop */
.stApp {
  background: #060D1A !important;
  position: relative;
  color: #F8FAFC;
  font-size: 15px;
  line-height: 1.65;
}

.stApp::before {
  content: "";
  position: fixed;
  inset: -32px;
  background-image: var(--rw-page-bg-img, none);
  background-size: cover;
  background-position: var(--rw-bg-pos, center center);
  background-repeat: no-repeat;
  filter: blur(18px) brightness(0.46) saturate(1.22);
  transform: scale(1.08);
  z-index: 0;
  pointer-events: none;
}

.stApp::after {
  content: "";
  position: fixed;
  inset: 0;
  background:
    radial-gradient(circle at 18% 14%, rgba(56, 189, 248, 0.12), transparent 46%),
    linear-gradient(180deg, rgba(6, 12, 24, 0.34) 0%, rgba(6, 12, 24, 0.58) 100%);
  z-index: 0;
  pointer-events: none;
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main {
  background: transparent !important;
  position: relative;
  z-index: 1;
}

[data-testid="stHeader"] {
  background: rgba(6, 15, 32, 0.44) !important;
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

[data-testid="stHeader"] * {
  color: #E2E8F0;
}

[data-testid="stMainBlockContainer"],
.stMainBlockContainer,
.main .block-container,
.block-container {
  max-width: 1320px !important;
  width: 100% !important;
  padding-top: 2rem !important;
  padding-bottom: 4rem !important;
}

/* Typography (adaptive bright inks on dark blurred backdrop outside glass cards) */
h1, h2, h3, h4 {
  font-family: var(--rw-font) !important;
  font-weight: 700 !important;
  color: #F8FAFC;
  letter-spacing: -0.015em !important;
  line-height: 1.26 !important;
}

h1 { font-size: clamp(1.85rem, 3.8vw, 2.55rem); }
h2 { font-size: clamp(1.38rem, 2.4vw, 1.9rem); }
h3 { font-size: 1.15rem; }

[data-testid="stMainBlockContainer"] h1,
[data-testid="stMainBlockContainer"] h2,
[data-testid="stMainBlockContainer"] h3,
[data-testid="stMainBlockContainer"] h4 {
  color: #F8FAFC;
  text-shadow: 0 2px 12px rgba(2, 8, 23, 0.48);
}

[data-testid="stMainBlockContainer"] .stMarkdown p,
[data-testid="stMainBlockContainer"] .stMarkdown li,
[data-testid="stMainBlockContainer"] [data-testid="stWidgetLabel"] p,
[data-testid="stMainBlockContainer"] [data-testid="stRadio"] label p,
[data-testid="stMainBlockContainer"] [data-testid="stCheckbox"] label p,
[data-testid="stMainBlockContainer"] [data-testid="stToggle"] label p {
  color: #F1F5F9;
}

[data-testid="stMainBlockContainer"] [data-testid="stCaptionContainer"] p {
  color: #CBD5E1;
}

/* Deep Frosted Glass Command Sidebar */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(6, 15, 32, 0.78) 0%, rgba(10, 24, 48, 0.84) 100%) !important;
  backdrop-filter: blur(26px) saturate(160%) !important;
  -webkit-backdrop-filter: blur(26px) saturate(160%) !important;
  border-right: 1px solid rgba(255, 255, 255, 0.14) !important;
  box-shadow: 4px 0 30px rgba(2, 8, 23, 0.36) !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarHeader"],
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] * {
  color: #CBD5E1 !important;
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] label p,
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
  color: #E2E8F0 !important;
}

section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
  color: #94A3B8 !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background: rgba(255, 255, 255, 0.08) !important;
  border-color: rgba(255, 255, 255, 0.18) !important;
  color: #F8FAFC !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] span,
section[data-testid="stSidebar"] [data-baseweb="select"] div,
section[data-testid="stSidebar"] [data-baseweb="select"] svg {
  color: #F8FAFC !important;
  fill: #CBD5E1 !important;
}

section[data-testid="stSidebar"] [data-testid="stExpander"] {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.14) !important;
  box-shadow: none !important;
}

section[data-testid="stSidebar"] [data-testid="stExpander"] summary,
section[data-testid="stSidebar"] [data-testid="stExpander"] summary p,
section[data-testid="stSidebar"] [data-testid="stExpanderToggleIcon"] {
  color: #E2E8F0 !important;
}

section[data-testid="stSidebar"] .stButton > button {
  background: rgba(255, 255, 255, 0.09) !important;
  color: #F8FAFC !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  min-height: 42px;
}

section[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(239, 68, 68, 0.22) !important;
  border-color: #F87171 !important;
  color: #FFFFFF !important;
}

@media (min-width: 900px) {
  section[data-testid="stSidebar"][aria-expanded="true"] {
    min-width: 268px !important;
    width: 268px !important;
  }
}

[data-testid="stSidebarNav"] a {
  display: flex !important;
  align-items: center !important;
  border-radius: 12px !important;
  min-height: 42px;
  margin: 2px 6px;
  padding: 8px 10px;
  gap: 10px;
  color: #CBD5E1 !important;
  font-weight: 600;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

[data-testid="stSidebarNav"] a span,
[data-testid="stSidebarNav"] a p {
  color: #CBD5E1 !important;
}

[data-testid="stSidebarNav"] a:hover {
  background: rgba(255, 255, 255, 0.1) !important;
  color: #FFFFFF !important;
  transform: translateX(3px);
}

[data-testid="stSidebarNav"] a:hover span,
[data-testid="stSidebarNav"] a:hover p {
  color: #FFFFFF !important;
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
  background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
  color: #FFFFFF !important;
  font-weight: 700;
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.45);
}

[data-testid="stSidebarNav"] a > span:first-child {
  font-size: 1.15rem !important;
  line-height: 1 !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  flex-shrink: 0 !important;
  margin-top: 0 !important;
}

[data-testid="stSidebarNav"] a > span:last-child {
  display: block !important;
  flex: 1 1 auto !important;
  min-width: 0 !important;
  line-height: 1.35 !important;
  font-size: 0.9rem !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}

[data-testid="stSidebarNav"] a[aria-current="page"] span,
[data-testid="stSidebarNav"] a[aria-current="page"] p {
  color: #FFFFFF !important;
}

[data-testid="stNavSectionHeader"] {
  color: #60A5FA !important;
  font-size: 0.74rem !important;
  font-weight: 800 !important;
  letter-spacing: 0.09em !important;
  text-transform: uppercase !important;
  padding: 12px 14px 4px !important;
}

.rw-sidebar-brand {
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(8px);
  padding: 15px;
  margin: 4px 6px 14px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
}

.rw-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #FFFFFF !important;
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.rw-logo-mark {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 0.95rem;
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.45);
}

.rw-sidebar-sub {
  color: #94A3B8 !important;
  font-size: 0.78rem;
  margin: 6px 0 0 50px;
}

.rw-sidebar-info {
  font-size: 0.8rem;
  color: #E2E8F0 !important;
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.07);
  margin: 4px 6px 8px;
  border: 1px solid rgba(255, 255, 255, 0.14);
}

/* Smoked Atmospheric Frosted Glass Cards, Forms & Interactive Widgets */
[data-testid="stForm"],
[data-testid="stMainBlockContainer"] [data-testid="stExpander"],
[data-testid="stVerticalBlockBorderWrapper"],
[class*="st-key-rw_glass_"],
.rw-glass-card {
  border: 1px solid rgba(255, 255, 255, 0.17) !important;
  border-radius: var(--rw-radius) !important;
  background:
    linear-gradient(155deg, rgba(255, 255, 255, 0.11) 0%, rgba(255, 255, 255, 0.03) 55%, rgba(255, 255, 255, 0.01) 100%),
    var(--rw-glass-bg, rgba(10, 20, 40, 0.58)) !important;
  backdrop-filter: blur(24px) saturate(180%) !important;
  -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
  box-shadow: 0 20px 48px rgba(2, 6, 23, 0.42), inset 0 1px 0 rgba(255, 255, 255, 0.22) !important;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

[class*="st-key-rw_glass_"] {
  padding: 16px !important;
}

[data-testid="stForm"]:hover,
[data-testid="stMainBlockContainer"] [data-testid="stExpander"]:hover,
[data-testid="stVerticalBlockBorderWrapper"]:hover,
[class*="st-key-rw_glass_"]:hover,
.rw-glass-card:hover {
  border-color: rgba(255, 255, 255, 0.32) !important;
  box-shadow: 0 24px 56px rgba(2, 6, 23, 0.52), inset 0 1px 0 rgba(255, 255, 255, 0.30) !important;
}

/* Modern Metric Cards (Smoked Frosted Glass) */
[data-testid="stMetric"] {
  border: 1px solid rgba(255, 255, 255, 0.17) !important;
  border-top: 3px solid var(--rw-accent, #38BDF8) !important;
  border-radius: var(--rw-radius) !important;
  background:
    linear-gradient(155deg, rgba(255, 255, 255, 0.11) 0%, rgba(255, 255, 255, 0.03) 55%, rgba(255, 255, 255, 0.01) 100%),
    var(--rw-glass-bg, rgba(10, 20, 40, 0.58)) !important;
  backdrop-filter: blur(22px) saturate(180%) !important;
  -webkit-backdrop-filter: blur(22px) saturate(180%) !important;
  padding: 1.15rem 1.25rem !important;
  box-shadow: 0 18px 42px rgba(2, 6, 23, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.22) !important;
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease, border-color 0.2s ease;
}

[data-testid="stMetric"]:hover {
  transform: translateY(-2px);
  box-shadow: 0 22px 48px rgba(2, 6, 23, 0.48) !important;
  border-color: rgba(255, 255, 255, 0.32) !important;
  border-top-color: var(--rw-accent, #7DD3FC) !important;
}

[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] > div,
[data-testid="stMetricLabel"] p {
  color: #CBD5E1 !important;
  font-size: 0.82rem !important;
  font-weight: 600 !important;
  text-shadow: none !important;
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: unset !important;
  overflow-wrap: break-word !important;
}

[data-testid="stMetricValue"],
[data-testid="stMetricValue"] > div,
[data-testid="stMetricValue"] p {
  font-size: clamp(1.15rem, 1.45vw, 1.48rem) !important;
  line-height: 1.3 !important;
  font-weight: 800 !important;
  font-variant-numeric: tabular-nums !important;
  color: #FFFFFF !important;
  text-shadow: none !important;
  letter-spacing: -0.02em;
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: unset !important;
  overflow-wrap: break-word !important;
}

/* Dropzone Uploader, Camera & DataFrames */
[data-testid="stFileUploader"] section {
  border: 2px dashed rgba(125, 211, 252, 0.48) !important;
  border-radius: 16px !important;
  background: rgba(10, 22, 42, 0.60) !important;
  backdrop-filter: blur(22px) saturate(175%) !important;
  -webkit-backdrop-filter: blur(22px) saturate(175%) !important;
  padding: 1.25rem !important;
  box-shadow: 0 18px 42px rgba(2, 6, 23, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.16) !important;
  transition: all 0.2s ease !important;
}
[data-testid="stFileUploader"] section:hover {
  border-color: rgba(125, 211, 252, 0.85) !important;
  background: rgba(12, 26, 50, 0.70) !important;
  box-shadow: 0 22px 48px rgba(37, 99, 235, 0.28) !important;
}
[data-testid="stFileUploader"] section,
[data-testid="stFileUploader"] section span,
[data-testid="stFileUploader"] section p,
[data-testid="stFileUploader"] section div {
  color: #F8FAFC !important;
  text-shadow: none !important;
}
[data-testid="stFileUploader"] section svg {
  color: #7DD3FC !important;
  fill: #7DD3FC !important;
}
[data-testid="stFileUploader"] section small {
  color: #CBD5E1 !important;
  text-shadow: none !important;
}
[data-testid="stFileUploader"] section button {
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
  color: #FFFFFF !important;
  border: 1px solid rgba(147, 197, 253, 0.45) !important;
  border-radius: 10px !important;
  padding: 8px 18px !important;
  font-weight: 700 !important;
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35) !important;
}
[data-testid="stFileUploader"] section button * {
  color: #FFFFFF !important;
}
[data-testid="stFileUploaderFile"] {
  background: rgba(12, 24, 44, 0.72) !important;
  backdrop-filter: blur(18px) saturate(165%) !important;
  -webkit-backdrop-filter: blur(18px) saturate(165%) !important;
  border: 1px solid rgba(255, 255, 255, 0.20) !important;
  border-radius: 12px !important;
  padding: 8px 12px !important;
  box-shadow: 0 10px 26px rgba(2, 6, 23, 0.28) !important;
}
[data-testid="stFileUploaderFile"] * {
  color: #F8FAFC !important;
  text-shadow: none !important;
}

[data-testid="stCameraInput"] {
  border: 1px solid rgba(255, 255, 255, 0.20) !important;
  border-radius: 16px !important;
  background: rgba(10, 22, 42, 0.62) !important;
  backdrop-filter: blur(22px) saturate(175%) !important;
  -webkit-backdrop-filter: blur(22px) saturate(175%) !important;
  padding: 12px !important;
  box-shadow: 0 18px 42px rgba(2, 6, 23, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.16) !important;
}
[data-testid="stCameraInput"] button {
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 10px !important;
  font-weight: 700 !important;
}
[data-testid="stCameraInput"] button * {
  color: #FFFFFF !important;
}

/* DataFrames & Standalone Vega Charts stay bright-backed for Glide/canvas legibility */
[data-testid="stDataFrame"] {
  border: 1px solid rgba(255, 255, 255, 0.28) !important;
  border-radius: 14px !important;
  overflow: hidden !important;
  box-shadow: 0 20px 44px rgba(2, 6, 23, 0.36) !important;
  background: rgba(255, 255, 255, 0.92) !important;
  backdrop-filter: blur(18px) saturate(170%) !important;
  -webkit-backdrop-filter: blur(18px) saturate(170%) !important;
}
[data-testid="stDataFrame"] * {
  text-shadow: none !important;
}

[data-testid="stMainBlockContainer"] [data-testid="stVegaLiteChart"] {
  background: rgba(255, 255, 255, 0.90);
  backdrop-filter: blur(18px) saturate(170%);
  -webkit-backdrop-filter: blur(18px) saturate(170%);
  border: 1px solid rgba(255, 255, 255, 0.65);
  border-radius: 16px;
  padding: 12px;
  box-shadow: 0 16px 38px rgba(2, 6, 23, 0.28);
}

[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVegaLiteChart"],
[class*="st-key-rw_glass_"] [data-testid="stVegaLiteChart"] {
  background: transparent !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  border: none !important;
  padding: 0 !important;
  box-shadow: none !important;
}

/* Alerts & Dropdown popovers */
[data-testid="stMainBlockContainer"] [data-testid="stAlert"] {
  border-radius: 14px !important;
  backdrop-filter: blur(16px) saturate(160%) !important;
  -webkit-backdrop-filter: blur(16px) saturate(160%) !important;
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28) !important;
}
[data-testid="stMainBlockContainer"] [data-testid="stAlert"] p,
[data-testid="stMainBlockContainer"] [data-testid="stAlert"] li,
[data-testid="stMainBlockContainer"] [data-testid="stAlert"] span,
[data-testid="stMainBlockContainer"] [data-testid="stAlert"] strong {
  color: #0F172A !important;
  text-shadow: none !important;
}
[data-testid="stMainBlockContainer"] [data-testid="stAlert"] code {
  background: rgba(15, 23, 42, 0.08) !important;
  color: #1E3A8A !important;
  padding: 2px 6px;
  border-radius: 5px;
}
[data-testid="stMainBlockContainer"] .rw-hint code,
[data-testid="stMainBlockContainer"] .rw-glass-card code {
  background: rgba(255, 255, 255, 0.14) !important;
  color: #FEF08A !important;
  padding: 2px 6px;
  border-radius: 5px;
}

[data-baseweb="popover"],
[role="listbox"] {
  background: rgba(10, 20, 38, 0.96) !important;
  border: 1px solid rgba(255, 255, 255, 0.16) !important;
  color: #F8FAFC !important;
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
}
[role="option"] {
  color: #F8FAFC !important;
  background: transparent !important;
}
[role="option"]:hover,
[role="option"][aria-selected="true"] {
  background: rgba(56, 189, 248, 0.22) !important;
  color: #FFFFFF !important;
}

/* Inputs, Textareas, Selectboxes (Smoked Dark Glass) */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {
  border-radius: 12px !important;
  border-color: rgba(255, 255, 255, 0.22) !important;
  min-height: 46px;
  background: rgba(6, 13, 28, 0.56) !important;
  color: #F8FAFC !important;
  transition: all 0.2s ease !important;
}

[data-testid="stMainBlockContainer"] [data-baseweb="input"] input,
[data-testid="stMainBlockContainer"] [data-baseweb="textarea"] textarea,
[data-testid="stMainBlockContainer"] [data-baseweb="select"] span,
[data-testid="stMainBlockContainer"] [data-baseweb="select"] div {
  color: #F8FAFC !important;
}

[data-testid="stMainBlockContainer"] [data-baseweb="input"] input::placeholder,
[data-testid="stMainBlockContainer"] [data-baseweb="textarea"] textarea::placeholder {
  color: #94A3B8 !important;
  opacity: 1 !important;
}

[data-testid="stMainBlockContainer"] [data-baseweb="select"] svg {
  color: #CBD5E1 !important;
  fill: #CBD5E1 !important;
}

[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"] > div:focus-within {
  border-color: #38BDF8 !important;
  box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.24) !important;
}

/* Modern Buttons */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button, .stLinkButton > a {
  min-height: 48px;
  border-radius: 12px !important;
  font-weight: 700 !important;
  letter-spacing: -0.01em;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

[data-testid="stMainBlockContainer"] .stButton > button:not([kind="primary"]),
[data-testid="stMainBlockContainer"] .stDownloadButton > button:not([kind="primary"]),
[data-testid="stMainBlockContainer"] .stFormSubmitButton > button:not([kind="primary"]),
[data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondary"],
[data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondaryFormSubmit"],
[data-testid="stMainBlockContainer"] .stLinkButton > a {
  background: rgba(14, 27, 50, 0.64) !important;
  backdrop-filter: blur(18px) saturate(165%) !important;
  -webkit-backdrop-filter: blur(18px) saturate(165%) !important;
  border: 1px solid rgba(255, 255, 255, 0.24) !important;
  color: #F8FAFC !important;
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.30), inset 0 1px 0 rgba(255, 255, 255, 0.16) !important;
}

[data-testid="stMainBlockContainer"] .stButton > button:not([kind="primary"]) *,
[data-testid="stMainBlockContainer"] .stDownloadButton > button:not([kind="primary"]) *,
[data-testid="stMainBlockContainer"] .stFormSubmitButton > button:not([kind="primary"]) *,
[data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondary"] *,
[data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondaryFormSubmit"] *,
[data-testid="stMainBlockContainer"] .stLinkButton > a * {
  color: #F8FAFC !important;
}

[data-testid="stMainBlockContainer"] .stButton > button:not([kind="primary"]):hover,
[data-testid="stMainBlockContainer"] .stDownloadButton > button:not([kind="primary"]):hover,
[data-testid="stMainBlockContainer"] .stFormSubmitButton > button:not([kind="primary"]):hover,
[data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondary"]:hover,
[data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondaryFormSubmit"]:hover,
[data-testid="stMainBlockContainer"] .stLinkButton > a:hover {
  background: rgba(37, 99, 235, 0.36) !important;
  border-color: rgba(125, 211, 252, 0.65) !important;
}

.stButton > button:hover, .stLinkButton > a:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(2, 8, 23, 0.28) !important;
}

.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"],
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"],
button[kind="primary"],
button[kind="primaryFormSubmit"] {
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
  border: 1px solid rgba(147, 197, 253, 0.4) !important;
  color: #FFFFFF !important;
  box-shadow: 0 8px 22px rgba(37, 99, 235, 0.38) !important;
}

.stButton > button[kind="primary"] *,
.stFormSubmitButton > button[kind="primary"] *,
[data-testid="stBaseButton-primary"] *,
[data-testid="stBaseButton-primaryFormSubmit"] *,
button[kind="primary"] *,
button[kind="primaryFormSubmit"] * {
  color: #FFFFFF !important;
}

.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover,
button[kind="primary"]:hover,
button[kind="primaryFormSubmit"]:hover {
  background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
  box-shadow: 0 10px 28px rgba(37, 99, 235, 0.48) !important;
}

/* Modern Tabs (Dark Glass Pill Bar) */
[data-baseweb="tab-list"] {
  background: rgba(10, 20, 38, 0.50) !important;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 14px;
  padding: 4px 6px;
}

button[data-baseweb="tab"],
button[data-baseweb="tab"] p {
  min-height: 44px;
  font-weight: 700 !important;
  font-size: 0.94rem !important;
  border-radius: 10px !important;
  padding: 8px 16px !important;
  color: #CBD5E1 !important;
}

button[data-baseweb="tab"] p {
  min-height: auto;
  padding: 0 !important;
}

button[data-baseweb="tab"][aria-selected="true"],
button[data-baseweb="tab"][aria-selected="true"] p {
  color: #FFFFFF !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
  background: rgba(59, 130, 246, 0.24) !important;
  border-bottom: 3px solid #38BDF8 !important;
}

/* ==========================================================================
   CUSTOM STEPPER 3 BƯỚC TRỰC QUAN
   ========================================================================== */
.rw-stepper-box {
  background:
    linear-gradient(155deg, rgba(255, 255, 255, 0.11) 0%, rgba(255, 255, 255, 0.03) 55%, rgba(255, 255, 255, 0.01) 100%),
    var(--rw-glass-bg, rgba(10, 20, 40, 0.58));
  backdrop-filter: blur(22px) saturate(180%);
  -webkit-backdrop-filter: blur(22px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.17);
  border-radius: 18px;
  padding: 20px 24px;
  margin: 16px 0 24px;
  box-shadow: 0 18px 42px rgba(2, 6, 23, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.22);
}

.rw-stepper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  max-width: 860px;
  margin: 0 auto;
}

.rw-step-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 2;
  text-align: center;
}

.rw-step-circle {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1rem;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.rw-step-node.completed .rw-step-circle {
  background: #10B981;
  color: #FFFFFF;
  box-shadow: 0 0 0 5px rgba(16, 185, 129, 0.22);
}

.rw-step-node.active .rw-step-circle {
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  color: #FFFFFF;
  box-shadow: 0 0 0 6px rgba(56, 189, 248, 0.26);
  transform: scale(1.08);
}

.rw-step-node.pending .rw-step-circle {
  background: rgba(255, 255, 255, 0.10);
  border: 2px solid rgba(255, 255, 255, 0.28);
  color: #CBD5E1;
}

.rw-step-label {
  margin-top: 10px;
  font-size: 0.85rem;
  font-weight: 700;
  color: #CBD5E1;
  transition: color 0.2s ease;
}

.rw-step-node.active .rw-step-label {
  color: #7DD3FC;
}

.rw-step-node.completed .rw-step-label {
  color: #6EE7B7;
}

.rw-step-line {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.18);
  margin: -24px 12px 0;
  position: relative;
  z-index: 1;
  border-radius: 2px;
}

.rw-step-line.completed-line {
  background: linear-gradient(90deg, #10B981 0%, #38BDF8 100%);
}

/* ==========================================================================
   GRID CARDS CHO HÀNG CHỜ VÀ BÁO CÁO
   ========================================================================== */
.rw-queue-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

/* Queue Cards (Smoked Frosted Glass) */
.rw-queue-card {
  background:
    linear-gradient(155deg, rgba(255, 255, 255, 0.11) 0%, rgba(255, 255, 255, 0.03) 55%, rgba(255, 255, 255, 0.01) 100%),
    var(--rw-glass-bg, rgba(10, 20, 40, 0.58));
  backdrop-filter: blur(22px) saturate(180%);
  -webkit-backdrop-filter: blur(22px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.17);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 18px 42px rgba(2, 6, 23, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.20);
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  color: #E2E8F0;
}

.rw-queue-card:hover {
  transform: translateY(-4px);
  border-color: rgba(125, 211, 252, 0.50);
  box-shadow: 0 22px 48px rgba(2, 6, 23, 0.48);
}

.rw-queue-card.selected {
  border: 2px solid #38BDF8;
  background: rgba(14, 34, 66, 0.72);
  box-shadow: 0 12px 30px rgba(56, 189, 248, 0.24);
}

/* Badges with Translucent Glowing Glass */
.rw-badge-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 750;
  letter-spacing: 0.02em;
}

.rw-badge-danger {
  background: rgba(239, 68, 68, 0.18);
  color: #FCA5A5;
  border: 1px solid rgba(248, 113, 113, 0.42);
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.20);
}

.rw-badge-warning {
  background: rgba(245, 158, 11, 0.18);
  color: #FDE68A;
  border: 1px solid rgba(251, 191, 36, 0.42);
  box-shadow: 0 0 12px rgba(245, 158, 11, 0.20);
}

.rw-badge-success {
  background: rgba(16, 185, 129, 0.18);
  color: #6EE7B7;
  border: 1px solid rgba(52, 211, 153, 0.42);
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.20);
}

/* Defect Semantic Badges (Translucent Glowing Pills) */
.rw-badge-d40 {
  background: rgba(239, 68, 68, 0.18);
  color: #FCA5A5;
  border: 1px solid rgba(248, 113, 113, 0.42);
  font-weight: 700;
}

.rw-badge-d20 {
  background: rgba(245, 158, 11, 0.18);
  color: #FDE68A;
  border: 1px solid rgba(251, 191, 36, 0.42);
  font-weight: 700;
}

.rw-badge-d10 {
  background: rgba(234, 179, 8, 0.18);
  color: #FEF08A;
  border: 1px solid rgba(250, 204, 21, 0.42);
  font-weight: 700;
}

.rw-badge-d00 {
  background: rgba(16, 185, 129, 0.18);
  color: #6EE7B7;
  border: 1px solid rgba(52, 211, 153, 0.42);
  font-weight: 700;
}

/* Micro-animations */
@keyframes pulseGlow {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.05); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.8; }
}

.rw-pulse {
  animation: pulseGlow 2s infinite ease-in-out;
}

/* Hero Banner with Unblurred Full-Resolution Background Image & Adaptive Typography */
.rw-hero{position:relative;overflow:hidden;background-color:#071224;background-image:var(--rw-hero-scrim), var(--rw-page-bg-img) !important;background-size:cover !important;background-position:var(--rw-hero-pos, center center) !important;background-repeat:no-repeat !important;
 border:1px solid rgba(255,255,255,.28);border-radius:24px;min-height:320px;padding:clamp(24px,4vw,46px);box-shadow:0 24px 60px rgba(2,8,23,.48);color:#FFFFFF;margin-bottom:22px}
.rw-hero-grid{position:relative;z-index:1;display:grid;grid-template-columns:1.18fr .82fr;align-items:center;gap:32px}
.rw-kicker{display:inline-flex;align-items:center;gap:8px;font-size:.74rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
 background:var(--rw-hero-kicker-bg, rgba(15,23,42,.52));border:1px solid var(--rw-hero-kicker-border, rgba(255,255,255,.32));border-radius:999px;padding:6px 14px;margin-bottom:14px;color:var(--rw-hero-kicker-text, #E0F2FE);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}
.rw-kicker-dot{width:8px;height:8px;border-radius:50%;background:#10B981;box-shadow:0 0 0 4px rgba(16,185,129,.25);display:inline-block}
.rw-hero h1{font-family:var(--rw-font) !important;color:var(--rw-hero-title, #FFFFFF) !important;font-size:clamp(1.75rem,3.2vw,2.55rem) !important;font-weight:800 !important;line-height:1.22 !important;letter-spacing:-0.02em !important;margin:0 0 14px;text-shadow:var(--rw-hero-shadow, 0 3px 20px rgba(4,10,24,.65))}
.rw-hero .rw-lead{color:var(--rw-hero-lead, #F1F5F9) !important;font-size:clamp(.95rem,1.45vw,1.04rem);line-height:1.7;max-width:560px;margin:0;text-shadow:0 1px 10px rgba(4,10,24,.55)}
.rw-hero-visual{position:relative;background:rgba(8, 18, 36, 0.54) !important;border:1px solid rgba(255,255,255,.26) !important;
 border-radius:20px;padding:20px;backdrop-filter:blur(18px) saturate(165%) !important;-webkit-backdrop-filter:blur(18px) saturate(165%) !important;box-shadow:0 18px 40px rgba(2,8,23,.42) !important}
.rw-visual-head{display:flex;align-items:center;justify-content:space-between;font-size:.82rem;font-weight:700;color:white;margin-bottom:14px}
.rw-visual-dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:#10B981;margin-right:6px;box-shadow:0 0 0 4px rgba(16,185,129,.22)}
.rw-visual-road{height:108px;position:relative;border-radius:14px;background:linear-gradient(137deg,#1E293B,#334155);border:1px solid rgba(255,255,255,.12);overflow:hidden}
.rw-visual-road:after{content:"";position:absolute;left:24%;top:-35px;width:52%;height:190px;transform:rotate(23deg);background:#1E293B;border-left:4px solid #E2E8F0;border-right:4px solid #E2E8F0}
.rw-road-line{position:absolute;left:49%;top:-35px;width:4px;height:190px;transform:rotate(23deg);z-index:1;background:repeating-linear-gradient(to bottom,#FBBF24 0 15px,transparent 15px 31px)}
.rw-road-pin{position:absolute;z-index:2;left:53%;top:28px;background:rgba(239,68,68,.2);border:2px solid #EF4444;width:36px;height:28px;border-radius:6px;box-shadow:0 0 16px rgba(239,68,68,.45)}
.rw-road-pin::after{content:"D40";position:absolute;top:-16px;left:-2px;background:#EF4444;color:#fff;font-size:9px;font-weight:800;padding:1px 4px;border-radius:3px}
.rw-visual-flow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:14px}
.rw-visual-flow span{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.20);border-radius:9px;text-align:center;color:#F8FAFC;font-size:.72rem;padding:8px 4px;font-weight:700}

.rw-section{margin-top:34px;margin-bottom:16px}
.rw-section .rw-overline{display:block;color:var(--rw-section-overline, #7DD3FC) !important;font-weight:800;text-transform:uppercase;letter-spacing:.08em;font-size:.75rem;margin-bottom:6px;text-shadow:0 1px 8px rgba(2,8,23,.5)}
.rw-section h2{font-size:clamp(1.35rem,2.3vw,1.85rem);color:#FFFFFF !important;margin:0 0 8px;text-shadow:0 2px 12px rgba(2,8,23,.45)}
.rw-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.rw-card{border:1px solid rgba(255,255,255,.17);border-radius:18px;background:linear-gradient(155deg, rgba(255,255,255,.11) 0%, rgba(255,255,255,.03) 55%, rgba(255,255,255,.01) 100%), var(--rw-glass-bg, rgba(10,20,40,.58));backdrop-filter:blur(22px) saturate(180%);-webkit-backdrop-filter:blur(22px) saturate(180%);padding:24px;box-shadow:0 20px 48px rgba(2,6,23,.40), inset 0 1px 0 rgba(255,255,255,.22);transition:all .2s ease}
.rw-card:hover{transform:translateY(-3px);border-color:rgba(255,255,255,.32);box-shadow:0 24px 54px rgba(2,6,23,.48)}
.rw-card-icon{display:flex;align-items:center;justify-content:center;width:48px;height:48px;border-radius:14px;background:rgba(56,189,248,.16);border:1px solid rgba(125,211,252,.32);color:#7DD3FC;font-size:1.4rem;margin-bottom:16px}
[data-testid="stMainBlockContainer"] .rw-card h3{font-size:1.08rem;margin:0 0 8px;color:#FFFFFF !important;text-shadow:none !important}
[data-testid="stMainBlockContainer"] .rw-card p{font-size:.88rem;color:#E2E8F0 !important;text-shadow:none !important;margin:0}

/* 4-Class AI Recognition Showcase Grid (Smoked Frosted Glass) */
.rw-defect-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:14px 0 8px}
.rw-defect-card{background:linear-gradient(155deg, rgba(255,255,255,.11) 0%, rgba(255,255,255,.03) 55%, rgba(255,255,255,.01) 100%), var(--rw-glass-bg, rgba(10,20,40,.58));backdrop-filter:blur(22px) saturate(180%);-webkit-backdrop-filter:blur(22px) saturate(180%);border:1px solid rgba(255,255,255,.18);border-radius:18px;padding:18px;box-shadow:0 18px 42px rgba(2,6,23,.38), inset 0 1px 0 rgba(255,255,255,.22);transition:all .22s cubic-bezier(0.16,1,0.3,1);position:relative;overflow:hidden}
.rw-defect-card:hover{transform:translateY(-3px);box-shadow:0 24px 52px rgba(2,6,23,.48);border-color:rgba(255,255,255,.34)}
.rw-defect-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
.rw-defect-code{font-size:.78rem;font-weight:800;padding:4px 10px;border-radius:999px;letter-spacing:.03em}
.rw-defect-weight{font-size:.74rem;font-weight:700;color:#CBD5E1;font-variant-numeric:tabular-nums}
.rw-defect-card h4{font-size:1rem !important;margin:0 0 6px !important;color:#FFFFFF !important;text-shadow:none !important}
[data-testid="stMainBlockContainer"] .rw-defect-card p{font-size:.83rem;color:#CBD5E1 !important;text-shadow:none !important;margin:0;line-height:1.5}

/* Officer Queue Case Summary Banner */
.rw-case-banner{background:linear-gradient(155deg, rgba(255,255,255,.11) 0%, rgba(255,255,255,.03) 55%, rgba(255,255,255,.01) 100%), var(--rw-glass-bg, rgba(10,20,40,.58));backdrop-filter:blur(22px) saturate(180%);-webkit-backdrop-filter:blur(22px) saturate(180%);border:1px solid rgba(255,255,255,.18);border-left:4px solid var(--rw-accent, #38BDF8);border-radius:16px;padding:14px 18px;margin:10px 0 16px;box-shadow:0 18px 42px rgba(2,6,23,.36), inset 0 1px 0 rgba(255,255,255,.20);display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px}
.rw-case-title{font-size:1.02rem;font-weight:700;color:#FFFFFF !important;text-shadow:none !important;margin:0}
.rw-case-meta{font-size:.82rem;color:#CBD5E1 !important;text-shadow:none !important;margin-top:3px}

.rw-overview{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.rw-kpi{background:linear-gradient(155deg, rgba(255,255,255,.11) 0%, rgba(255,255,255,.03) 55%, rgba(255,255,255,.01) 100%), var(--rw-glass-bg, rgba(10,20,40,.58));backdrop-filter:blur(22px) saturate(180%);-webkit-backdrop-filter:blur(22px) saturate(180%);border:1px solid rgba(255,255,255,.17);padding:22px;border-radius:18px;box-shadow:0 18px 42px rgba(2,6,23,.38), inset 0 1px 0 rgba(255,255,255,.22);transition:all .2s ease}
.rw-kpi:hover{transform:translateY(-2px);border-color:rgba(255,255,255,.32);box-shadow:0 22px 48px rgba(2,6,23,.48)}
.rw-kpi small{display:block;color:#CBD5E1;margin-bottom:8px;font-size:.82rem;font-weight:600}
.rw-kpi strong{display:block;color:#FFFFFF;font-size:clamp(1.5rem,2.5vw,2.1rem);line-height:1.2;font-weight:800}
.rw-kpi em{display:block;font-size:.76rem;font-style:normal;color:#94A3B8;margin-top:6px}

.rw-page-intro{position:relative;overflow:hidden;background-color:#071224;background-image:var(--rw-hero-scrim), var(--rw-page-bg-img) !important;background-size:cover !important;background-position:var(--rw-hero-pos, center center) !important;background-repeat:no-repeat !important;padding:clamp(22px,3vw,34px) clamp(24px,3.5vw,36px);border:1px solid rgba(255,255,255,.28);border-radius:22px;margin-bottom:22px;box-shadow:0 22px 54px rgba(2,8,23,.44);color:#FFFFFF}
.rw-page-intro .rw-overline{position:relative;display:inline-block;font-size:.74rem;color:var(--rw-hero-kicker-text, #E0F2FE);background:var(--rw-hero-kicker-bg, rgba(15,23,42,.52));border:1px solid var(--rw-hero-kicker-border, rgba(255,255,255,.32));border-radius:999px;padding:5px 13px;letter-spacing:.08em;font-weight:700;text-transform:uppercase;margin-bottom:10px;backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}
.rw-page-intro h1{position:relative;font-family:var(--rw-font) !important;color:var(--rw-hero-title, #FFFFFF) !important;font-size:clamp(1.5rem,2.7vw,2.15rem);font-weight:800 !important;letter-spacing:-0.02em !important;line-height:1.24 !important;margin:4px 0 8px;text-shadow:var(--rw-hero-shadow, 0 3px 20px rgba(4,10,24,.65))}
.rw-page-intro p{position:relative;color:var(--rw-hero-lead, #F1F5F9) !important;margin:0;font-size:.95rem;line-height:1.6;max-width:760px;text-shadow:0 1px 10px rgba(4,10,24,.55)}

[data-testid="stMainBlockContainer"] .rw-hint{background:rgba(30,58,138,.42);backdrop-filter:blur(18px) saturate(165%);-webkit-backdrop-filter:blur(18px) saturate(165%);border:1px solid rgba(96,165,250,.36);border-left:4px solid #38BDF8;padding:14px 18px;border-radius:0 14px 14px 0;font-size:.88rem;color:#E0F2FE !important;text-shadow:none !important;margin-bottom:18px;box-shadow:0 14px 32px rgba(2,6,23,.28)}
[data-testid="stMainBlockContainer"] .rw-hint *{color:#E0F2FE !important;text-shadow:none !important}
[data-testid="stMainBlockContainer"] .rw-empty{background:rgba(10,20,38,.54);backdrop-filter:blur(18px) saturate(165%);-webkit-backdrop-filter:blur(18px) saturate(165%);padding:24px;border:2px dashed rgba(148,163,184,.42);border-radius:16px;color:#E2E8F0 !important;text-shadow:none !important;text-align:center;box-shadow:0 14px 32px rgba(2,6,23,.28)}
[data-testid="stMainBlockContainer"] .rw-empty *{color:#E2E8F0 !important;text-shadow:none !important}
.rw-preview-banner{background:linear-gradient(135deg, rgba(15,23,42,.88) 0%, rgba(30,58,138,.88) 100%);backdrop-filter:blur(16px);border:1px solid rgba(96,165,250,.65);color:#FFFFFF;padding:12px 20px;border-radius:14px;font-size:.93rem;font-weight:600;letter-spacing:.02em;margin:16px 0 12px;display:flex;align-items:center;gap:10px;box-shadow:0 12px 28px rgba(2,8,23,.30)}

/* CTA Page Links & Two-Column Panels (Smoked Frosted Glass) */
[data-testid="stPageLink-NavLink"]{
  display:flex !important;align-items:center;justify-content:flex-start !important;width:100% !important;min-height:50px;padding:12px 18px !important;
  border-radius:14px !important;border:1px solid rgba(255,255,255,.22) !important;
  background:linear-gradient(135deg, rgba(255,255,255,.13) 0%, rgba(255,255,255,.04) 100%), rgba(12,23,44,.56) !important;
  backdrop-filter:blur(18px) saturate(175%) !important;-webkit-backdrop-filter:blur(18px) saturate(175%) !important;
  color:#F8FAFC !important;font-weight:700 !important;box-shadow:0 12px 30px rgba(2,6,23,.30), inset 0 1px 0 rgba(255,255,255,.20);
  transition:all .2s cubic-bezier(0.16,1,0.3,1) !important;text-decoration:none !important;
}
[data-testid="stPageLink-NavLink"] *{color:#F8FAFC !important;}
[data-testid="stPageLink-NavLink"]:hover{
  transform:translateY(-2px);background:linear-gradient(135deg,#2563EB 0%,#0EA5E9 100%) !important;
  color:#FFFFFF !important;border-color:rgba(125,211,252,.75) !important;box-shadow:0 14px 34px rgba(37,99,235,.42) !important;
}
[data-testid="stPageLink-NavLink"]:hover *{color:#FFFFFF !important;}

.rw-two-col{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:14px}
.rw-white-panel{background:linear-gradient(155deg, rgba(255,255,255,.11) 0%, rgba(255,255,255,.03) 55%, rgba(255,255,255,.01) 100%), var(--rw-glass-bg, rgba(10,20,40,.58));backdrop-filter:blur(22px) saturate(180%);-webkit-backdrop-filter:blur(22px) saturate(180%);border:1px solid rgba(255,255,255,.18);border-radius:18px;padding:24px;box-shadow:0 18px 42px rgba(2,6,23,.38), inset 0 1px 0 rgba(255,255,255,.22);transition:all .2s ease}
.rw-white-panel:hover{transform:translateY(-2px);box-shadow:0 24px 52px rgba(2,6,23,.48);border-color:rgba(255,255,255,.32)}
.rw-panel-title{display:inline-block;font-size:.74rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#7DD3FC;background:rgba(56,189,248,.16);border:1px solid rgba(125,211,252,.32);padding:4px 10px;border-radius:999px;margin-bottom:10px}
[data-testid="stMainBlockContainer"] .rw-white-panel h3{margin:4px 0 8px;font-size:1.12rem;color:#FFFFFF !important;text-shadow:none !important}
[data-testid="stMainBlockContainer"] .rw-white-panel p{margin:0;color:#CBD5E1 !important;text-shadow:none !important;font-size:.9rem}
[data-testid="stMainBlockContainer"] .rw-footnote{margin-top:22px;padding:14px 18px;border-radius:14px;background:rgba(10,18,34,.50);backdrop-filter:blur(18px) saturate(165%);-webkit-backdrop-filter:blur(18px) saturate(165%);border:1px solid rgba(255,255,255,.14);color:#CBD5E1 !important;text-shadow:none !important;font-size:.84rem;text-align:center;box-shadow:0 12px 28px rgba(2,6,23,.26)}

/* Reset crisp bright inks inside Smoked Frosted Glass containers */
[data-testid="stForm"] h1, [data-testid="stForm"] h2, [data-testid="stForm"] h3, [data-testid="stForm"] h4,
[data-testid="stMainBlockContainer"] [data-testid="stExpander"] h1,
[data-testid="stMainBlockContainer"] [data-testid="stExpander"] h2,
[data-testid="stMainBlockContainer"] [data-testid="stExpander"] h3,
[data-testid="stMainBlockContainer"] [data-testid="stExpander"] h4,
[data-testid="stVerticalBlockBorderWrapper"] h1,
[data-testid="stVerticalBlockBorderWrapper"] h2,
[data-testid="stVerticalBlockBorderWrapper"] h3,
[data-testid="stVerticalBlockBorderWrapper"] h4,
[class*="st-key-rw_glass_"] h1,
[class*="st-key-rw_glass_"] h2,
[class*="st-key-rw_glass_"] h3,
[class*="st-key-rw_glass_"] h4,
[data-testid="stMainBlockContainer"] .rw-glass-card h1,
[data-testid="stMainBlockContainer"] .rw-glass-card h2,
[data-testid="stMainBlockContainer"] .rw-glass-card h3,
[data-testid="stMainBlockContainer"] .rw-glass-card h4 {
  color: #FFFFFF !important;
  text-shadow: none !important;
}

[data-testid="stForm"] [data-testid="stWidgetLabel"] p,
[data-testid="stForm"] label p,
[data-testid="stForm"] .stMarkdown p,
[data-testid="stForm"] .stMarkdown li,
[data-testid="stMainBlockContainer"] [data-testid="stExpander"] summary,
[data-testid="stMainBlockContainer"] [data-testid="stExpander"] summary p,
[data-testid="stMainBlockContainer"] [data-testid="stExpander"] [data-testid="stWidgetLabel"] p,
[data-testid="stMainBlockContainer"] [data-testid="stExpander"] label p,
[data-testid="stMainBlockContainer"] [data-testid="stExpander"] .stMarkdown p,
[data-testid="stMainBlockContainer"] [data-testid="stExpander"] .stMarkdown li,
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stWidgetLabel"] p,
[data-testid="stVerticalBlockBorderWrapper"] label p,
[data-testid="stVerticalBlockBorderWrapper"] .stMarkdown p,
[data-testid="stVerticalBlockBorderWrapper"] .stMarkdown li,
[class*="st-key-rw_glass_"] [data-testid="stWidgetLabel"] p,
[class*="st-key-rw_glass_"] label p,
[class*="st-key-rw_glass_"] .stMarkdown p,
[class*="st-key-rw_glass_"] .stMarkdown li,
[data-testid="stMainBlockContainer"] .rw-glass-card p,
[data-testid="stMainBlockContainer"] .rw-glass-card li,
[data-testid="stMainBlockContainer"] .rw-glass-card td,
[data-testid="stMainBlockContainer"] .rw-glass-card th {
  color: #E2E8F0 !important;
  text-shadow: none !important;
}

[data-testid="stForm"] [data-testid="stAlert"] p,
[data-testid="stForm"] [data-testid="stAlert"] li,
[data-testid="stForm"] [data-testid="stAlert"] span,
[data-testid="stForm"] [data-testid="stAlert"] strong,
[data-testid="stMainBlockContainer"] [data-testid="stExpander"] [data-testid="stAlert"] p,
[data-testid="stMainBlockContainer"] [data-testid="stExpander"] [data-testid="stAlert"] strong,
[class*="st-key-rw_glass_"] [data-testid="stAlert"] p,
[class*="st-key-rw_glass_"] [data-testid="stAlert"] strong {
  color: #0F172A !important;
  text-shadow: none !important;
}

[data-testid="stForm"] [data-testid="stCaptionContainer"] p,
[data-testid="stMainBlockContainer"] [data-testid="stExpander"] [data-testid="stCaptionContainer"] p,
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] p,
[class*="st-key-rw_glass_"] [data-testid="stCaptionContainer"] p {
  color: #CBD5E1 !important;
  text-shadow: none !important;
}

[data-testid="stMainBlockContainer"] [data-testid="stExpander"] [data-testid="stExpanderToggleIcon"] {
  color: #E2E8F0 !important;
}

[data-testid="stColumn"], [data-testid="column"] {
  transition: flex-basis 0.25s ease, min-width 0.25s ease, transform 0.25s ease;
}

@media (max-width: 1100px) {
  [data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
    gap: 14px !important;
  }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"] > [data-testid="column"] {
    flex: 1 1 calc(50% - 14px) !important;
    min-width: min(100%, 300px) !important;
  }
  .rw-hero-grid { grid-template-columns: 1fr; }
  .rw-overview, .rw-defect-grid { grid-template-columns: repeat(2, 1fr); }
}

/* ==========================================================================
   MOBILE APP MODE (BOTTOM DOCK NAVIGATION & COMPACT RESPONSIVE)
   ========================================================================== */
@media (min-width: 769px) {
  .st-key-rw_mobile_dock {
    display: none !important;
  }
}

@media (max-width: 768px) {
  .st-key-rw_mobile_dock {
    position: fixed !important;
    bottom: 0 !important;
    left: 0 !important;
    right: 0 !important;
    z-index: 999990 !important;
    background: rgba(8, 16, 32, 0.86) !important;
    backdrop-filter: blur(18px) saturate(170%) !important;
    -webkit-backdrop-filter: blur(18px) saturate(170%) !important;
    border-top: 1px solid rgba(255, 255, 255, 0.16) !important;
    padding: 6px 8px calc(6px + env(safe-area-inset-bottom)) 8px !important;
    box-shadow: 0 -8px 28px rgba(2, 6, 23, 0.42) !important;
    margin: 0 !important;
  }
  .st-key-rw_mobile_dock [data-testid="stHorizontalBlock"] {
    display: grid !important;
    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
    gap: 4px !important;
    flex-wrap: nowrap !important;
    margin: 0 !important;
  }
  .st-key-rw_mobile_dock [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
  .st-key-rw_mobile_dock [data-testid="stHorizontalBlock"] > [data-testid="column"] {
    flex: 1 1 0% !important;
    min-width: 0 !important;
    width: 100% !important;
  }
  .st-key-rw_mobile_dock [data-testid="stPageLink-NavLink"] {
    flex-direction: column !important;
    justify-content: center !important;
    gap: 2px !important;
    min-height: 48px !important;
    padding: 5px 2px !important;
    border: none !important;
    background: transparent !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
    box-shadow: none !important;
    border-radius: 10px !important;
    font-size: 0.70rem !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    color: #E2E8F0 !important;
  }
  .st-key-rw_mobile_dock [data-testid="stPageLink-NavLink"] * {
    color: #E2E8F0 !important;
  }
  .st-key-rw_mobile_dock [data-testid="stPageLink-NavLink"]:hover {
    transform: none !important;
    background: rgba(56, 189, 248, 0.18) !important;
    color: #38BDF8 !important;
    box-shadow: none !important;
  }
  .st-key-rw_mobile_dock [data-testid="stPageLink-NavLink"]:hover * {
    color: #38BDF8 !important;
  }
}

@media (max-width: 740px) {
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"] > [data-testid="column"] {
    flex: 1 1 100% !important;
    min-width: 100% !important;
  }
  [data-testid="stMainBlockContainer"],
  .stMainBlockContainer,
  .main .block-container,
  .block-container {
    padding: 1rem 0.9rem 92px 0.9rem !important;
  }
  .rw-hero { padding: 20px; border-radius: 18px; min-height: auto; }
  .rw-page-intro { padding: 18px; border-radius: 16px; }
  .rw-cards, .rw-two-col { grid-template-columns: 1fr; }
  .rw-overview { grid-template-columns: repeat(2, 1fr); }
  .rw-stepper-box { padding: 14px 10px; }
  .rw-step-circle { width: 34px; height: 34px; font-size: 0.85rem; }
  .rw-step-label { font-size: 0.72rem; margin-top: 6px; }
  .rw-step-line { margin: -20px 4px 0; height: 3px; }
}

@media (max-width: 560px) {
  .rw-hero-visual { display: none; }
}

@media (max-width: 480px) {
  .rw-overview, .rw-defect-grid { grid-template-columns: 1fr; }
}
</style>
"""

def apply(page_key: str = 'home'):
    preset_key = PAGE_BG_MAP.get(str(page_key or 'home').strip(), 'golden')
    preset = BG_PRESETS.get(preset_key, BG_PRESETS['golden'])
    bg_uri = _bg_data_uri(preset['file'])
    vars_css = (
        f'<style>:root {{'
        f' --rw-page-bg-img: {bg_uri};'
        f' --rw-bg-pos: {preset["bg_pos"]};'
        f' --rw-hero-pos: {preset["hero_pos"]};'
        f' --rw-hero-scrim: {preset["scrim"]};'
        f' --rw-hero-title: {preset["title"]};'
        f' --rw-hero-lead: {preset["lead"]};'
        f' --rw-hero-shadow: {preset["shadow"]};'
        f' --rw-hero-kicker-bg: {preset["kicker_bg"]};'
        f' --rw-hero-kicker-border: {preset["kicker_border"]};'
        f' --rw-hero-kicker-text: {preset["kicker_text"]};'
        f' --rw-section-overline: {preset["overline"]};'
        f' --rw-glass-bg: {preset["glass_bg"]};'
        f' --rw-accent: {preset["accent"]};'
        f' }}</style>'
    )
    st.markdown(vars_css + CSS, unsafe_allow_html=True)
    # Khi mở trực tiếp *.streamlit.app trên mobile (không phải ?embed=true của PWA/APK),
    # Streamlit Cloud đặt avatar + nút vương miện đỏ ở góc dưới phải (~98px) nên chừa lề phải cho dock.
    is_embed = str(st.query_params.get('embed', '')).lower() == 'true'
    if not is_embed:
        st.markdown(
            """<style>
@media (max-width: 768px) {
  .st-key-rw_mobile_dock {
    padding-right: 102px !important;
  }
  .st-key-rw_mobile_dock [data-testid="stPageLink-NavLink"] {
    font-size: 0.64rem !important;
  }
}
</style>""",
            unsafe_allow_html=True,
        )
