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
  color-scheme: dark;
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

[data-testid="stExpander"] summary > span:first-child {
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
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
  max-width: 1380px !important;
  width: 100% !important;
  padding-top: 1.75rem !important;
  padding-bottom: 3.5rem !important;
  padding-left: clamp(1rem, 2.2vw, 2rem) !important;
  padding-right: clamp(1rem, 2.2vw, 2rem) !important;
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
[data-testid="stMainBlockContainer"] [data-testid="stWidgetLabel"],
[data-testid="stMainBlockContainer"] [data-testid="stWidgetLabel"] *,
[data-testid="stMainBlockContainer"] [data-testid="stRadio"] label,
[data-testid="stMainBlockContainer"] [data-testid="stRadio"] label p,
[data-testid="stMainBlockContainer"] [data-testid="stRadioOption"],
[data-testid="stMainBlockContainer"] [data-testid="stCheckbox"] label,
[data-testid="stMainBlockContainer"] [data-testid="stCheckbox"] label p,
[data-testid="stMainBlockContainer"] [data-testid="stToggle"] label,
[data-testid="stMainBlockContainer"] [data-testid="stToggle"] label p,
[data-testid="stMainBlockContainer"] [data-testid="stSpinner"],
[data-testid="stMainBlockContainer"] [data-testid="stSpinner"] *,
[data-testid="stMainBlockContainer"] [data-testid="stProgress"],
[data-testid="stMainBlockContainer"] [data-testid="stProgress"] *,
[data-testid="stMainBlockContainer"] [data-testid="stText"] {
  color: #F1F5F9;
}

[data-testid="stMainBlockContainer"] [data-testid="stCaptionContainer"] p,
[data-testid="stMainBlockContainer"] [data-testid="stCaptionContainer"] span,
[data-testid="stMainBlockContainer"] [data-testid="stCaptionContainer"] em,
[data-testid="stMainBlockContainer"] [data-testid="stImageCaption"],
[data-testid="stMainBlockContainer"] [data-testid="stRadioCaption"] {
  color: #CBD5E1 !important;
}

[data-testid="stMainBlockContainer"] [data-testid="stTooltipIcon"] svg {
  color: #CBD5E1 !important;
  fill: #CBD5E1 !important;
}

[data-testid="stMainBlockContainer"] .stMarkdown a:not([data-testid="stPageLink-NavLink"]),
section[data-testid="stSidebar"] .stMarkdown a {
  color: #7DD3FC !important;
  text-decoration-color: rgba(125, 211, 252, 0.45);
}
[data-testid="stMainBlockContainer"] .stMarkdown a:not([data-testid="stPageLink-NavLink"]):hover,
section[data-testid="stSidebar"] .stMarkdown a:hover {
  color: #BAE6FD !important;
}

[data-testid="stMainBlockContainer"] hr,
[data-testid="stMainBlockContainer"] [data-testid="stDivider"] {
  border-color: rgba(255, 255, 255, 0.16) !important;
}
[data-testid="stMainBlockContainer"] .stMarkdown blockquote {
  border-left: 3px solid #38BDF8 !important;
  background: rgba(10, 20, 38, 0.45) !important;
  padding: 8px 14px !important;
  border-radius: 0 10px 10px 0;
  color: #E2E8F0 !important;
}
[data-testid="stMainBlockContainer"] .stMarkdown table {
  border-collapse: collapse;
  width: 100%;
}
[data-testid="stMainBlockContainer"] .stMarkdown th,
[data-testid="stMainBlockContainer"] .stMarkdown td {
  border-color: rgba(255, 255, 255, 0.16) !important;
  color: #E2E8F0 !important;
}

/* Deep Frosted Glass Command Sidebar */
section[data-testid="stSidebar"] {
  background: radial-gradient(circle at 18% 0%, rgba(56, 189, 248, 0.13) 0%, transparent 46%),
    linear-gradient(180deg, rgba(5, 12, 27, 0.88) 0%, rgba(9, 21, 43, 0.93) 100%) !important;
  backdrop-filter: blur(28px) saturate(165%) !important;
  -webkit-backdrop-filter: blur(28px) saturate(165%) !important;
  border-right: 1px solid rgba(148, 163, 184, 0.16) !important;
  box-shadow: 6px 0 34px rgba(2, 6, 23, 0.45), inset -1px 0 0 rgba(255, 255, 255, 0.04) !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarHeader"],
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] * {
  color: #CBD5E1 !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
  height: auto !important;
  min-height: 62px !important;
  padding: 8px 14px 8px !important;
  margin-bottom: 2px !important;
  align-items: center !important;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12) !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarLogo"],
section[data-testid="stSidebar"] [data-testid="stLogo"],
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] img {
  height: 52px !important;
  width: auto !important;
  max-width: 172px !important;
  object-fit: contain !important;
  filter: drop-shadow(0 3px 14px rgba(251, 191, 36, 0.22));
}

[data-testid="stHeader"] [data-testid="stLogo"] {
  height: 30px !important;
  width: auto !important;
  object-fit: contain !important;
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
  background: rgba(255, 255, 255, 0.06) !important;
  color: #E2E8F0 !important;
  border: 1px solid rgba(148, 163, 184, 0.22) !important;
  border-radius: 10px !important;
  min-height: 34px !important;
  padding: 4px 10px !important;
  font-size: 0.82rem !important;
  font-weight: 600 !important;
  transition: all 0.18s ease !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(239, 68, 68, 0.20) !important;
  border-color: rgba(248, 113, 113, 0.65) !important;
  color: #FFFFFF !important;
}

@media (min-width: 900px) {
  section[data-testid="stSidebar"][aria-expanded="true"] {
    min-width: 268px !important;
    width: 268px !important;
  }
}

[data-testid="stSidebarNavItems"] {
  max-height: none !important;
}

[data-testid="stSidebarNavViewButton"] {
  display: none !important;
}

[data-testid="stSidebarNav"] a {
  display: flex !important;
  align-items: center !important;
  border-radius: 10px !important;
  min-height: 33px !important;
  margin: 1px 8px !important;
  padding: 4px 10px !important;
  gap: 10px !important;
  color: #CBD5E1 !important;
  font-size: 0.855rem !important;
  font-weight: 500;
  border: 1px solid transparent !important;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

[data-testid="stSidebarNav"] a span,
[data-testid="stSidebarNav"] a p {
  color: #CBD5E1 !important;
}

[data-testid="stSidebarNav"] a [data-testid="stIconMaterial"] {
  color: #7C96B8 !important;
  font-size: 1.12rem !important;
  transition: color 0.18s ease, transform 0.18s ease !important;
}

[data-testid="stSidebarNav"] a:hover {
  background: rgba(148, 163, 184, 0.11) !important;
  border-color: rgba(148, 163, 184, 0.14) !important;
  color: #FFFFFF !important;
  transform: translateX(2px);
}

[data-testid="stSidebarNav"] a:hover span,
[data-testid="stSidebarNav"] a:hover p {
  color: #FFFFFF !important;
}

[data-testid="stSidebarNav"] a:hover [data-testid="stIconMaterial"] {
  color: #7DD3FC !important;
}

[data-testid="stSidebarNav"] a[aria-current="page"] [data-testid="stIconMaterial"] {
  color: #38BDF8 !important;
}

[data-testid="stSidebarNav"] a:hover span,
[data-testid="stSidebarNav"] a:hover p {
  color: #FFFFFF !important;
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
  position: relative !important;
  background: linear-gradient(90deg, rgba(56, 189, 248, 0.22) 0%, rgba(59, 130, 246, 0.11) 68%, rgba(15, 23, 42, 0.05) 100%) !important;
  border: 1px solid rgba(125, 211, 252, 0.34) !important;
  color: #F0F9FF !important;
  font-weight: 700 !important;
  padding-left: 14px !important;
  box-shadow: 0 6px 20px rgba(2, 6, 23, 0.30), inset 0 1px 0 rgba(255, 255, 255, 0.14) !important;
}

[data-testid="stSidebarNav"] a[aria-current="page"]::before {
  content: "";
  position: absolute;
  left: 4px;
  top: 7px;
  bottom: 7px;
  width: 3.5px;
  border-radius: 999px;
  background: linear-gradient(180deg, #7DD3FC 0%, #38BDF8 50%, #3B82F6 100%);
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.85);
}

[data-testid="stSidebarNav"] a[aria-current="page"]:hover {
  transform: none !important;
  background: linear-gradient(90deg, rgba(56, 189, 248, 0.28) 0%, rgba(59, 130, 246, 0.14) 68%, rgba(15, 23, 42, 0.08) 100%) !important;
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
  color: #F0F9FF !important;
}

[data-testid="stNavSectionHeader"] {
  color: rgba(147, 197, 253, 0.82) !important;
  font-size: 0.69rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.11em !important;
  text-transform: uppercase !important;
  padding: 10px 14px 4px !important;
}

[data-testid="stSidebarNavSeparator"] {
  margin: 6px 14px !important;
  border-color: rgba(148, 163, 184, 0.14) !important;
  opacity: 0.85 !important;
}

.rw-sidebar-brand {
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 16px;
  background:
    linear-gradient(160deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.03) 100%),
    rgba(10, 22, 44, 0.52);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  padding: 16px 14px 14px;
  margin: 4px 6px 14px;
  text-align: center;
  box-shadow: 0 10px 26px rgba(2, 6, 23, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.22);
}

.rw-brand-logo-img {
  width: 100%;
  max-width: 176px;
  height: auto;
  display: block;
  margin: 0 auto 8px;
  object-fit: contain;
  filter: drop-shadow(0 3px 12px rgba(251, 191, 36, 0.24));
}

.rw-logo {
  display: flex;
  align-items: center;
  justify-content: center;
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
  color: #CBD5E1 !important;
  font-size: 0.78rem;
  margin: 4px 0 0;
  text-align: center;
}

.rw-sidebar-info {
  font-size: 0.78rem;
  line-height: 1.4;
  color: #CBD5E1 !important;
  padding: 10px 12px;
  border-radius: 11px;
  background: rgba(15, 23, 42, 0.55);
  margin: 6px 8px 8px;
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.rw-officer-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 11px;
  margin: 6px 8px 8px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.72) 0%, rgba(30, 58, 138, 0.24) 100%);
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.rw-officer-avatar {
  position: relative;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0284C7 0%, #2563EB 100%);
  color: #F8FAFC !important;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.03em;
  box-shadow: 0 3px 10px rgba(37, 99, 235, 0.35);
}

.rw-officer-avatar::after {
  content: "";
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #22C55E;
  border: 2px solid #09152B;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.75);
}

.rw-officer-meta {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.rw-officer-name {
  font-size: 0.83rem;
  font-weight: 700;
  color: #F8FAFC !important;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rw-officer-role {
  display: inline-block;
  align-self: flex-start;
  font-size: 0.68rem;
  font-weight: 600;
  color: #7DD3FC !important;
  background: rgba(56, 189, 248, 0.14);
  border: 1px solid rgba(56, 189, 248, 0.28);
  border-radius: 999px;
  padding: 1px 7px;
  line-height: 1.3;
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
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0.04) 48%, rgba(14, 165, 233, 0.16) 100%),
    linear-gradient(135deg, rgba(37, 99, 235, 0.88) 0%, rgba(14, 165, 233, 0.82) 100%) !important;
  backdrop-filter: blur(20px) saturate(200%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(200%) !important;
  color: #FFFFFF !important;
  border: 1px solid rgba(186, 230, 253, 0.62) !important;
  border-radius: 12px !important;
  padding: 8px 18px !important;
  font-weight: 700 !important;
  box-shadow:
    0 10px 26px rgba(37, 99, 235, 0.42),
    inset 0 1.5px 1px rgba(255, 255, 255, 0.60),
    inset 0 -1px 2px rgba(6, 182, 212, 0.34) !important;
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
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0.04) 48%, rgba(14, 165, 233, 0.16) 100%),
    linear-gradient(135deg, rgba(37, 99, 235, 0.88) 0%, rgba(14, 165, 233, 0.82) 100%) !important;
  backdrop-filter: blur(20px) saturate(200%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(200%) !important;
  color: #FFFFFF !important;
  border: 1px solid rgba(186, 230, 253, 0.62) !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
  box-shadow:
    0 10px 26px rgba(37, 99, 235, 0.42),
    inset 0 1.5px 1px rgba(255, 255, 255, 0.60),
    inset 0 -1px 2px rgba(6, 182, 212, 0.34) !important;
}
[data-testid="stCameraInput"] button * {
  color: #FFFFFF !important;
}

/* DataFrames & Standalone Vega Charts (Dark Frosted Glass to match base="dark") */
[data-testid="stDataFrame"] {
  border: 1px solid rgba(255, 255, 255, 0.20) !important;
  border-radius: 14px !important;
  overflow: hidden !important;
  box-shadow: 0 20px 44px rgba(2, 6, 23, 0.36) !important;
  background: rgba(10, 20, 38, 0.78) !important;
  backdrop-filter: blur(18px) saturate(170%) !important;
  -webkit-backdrop-filter: blur(18px) saturate(170%) !important;
}
[data-testid="stDataFrame"] * {
  text-shadow: none !important;
}

[data-testid="stMainBlockContainer"] [data-testid="stVegaLiteChart"] {
  background:
    linear-gradient(155deg, rgba(255, 255, 255, 0.10) 0%, rgba(255, 255, 255, 0.02) 100%),
    var(--rw-glass-bg, rgba(10, 20, 40, 0.62));
  backdrop-filter: blur(18px) saturate(170%);
  -webkit-backdrop-filter: blur(18px) saturate(170%);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 16px;
  padding: 12px;
  box-shadow: 0 16px 38px rgba(2, 6, 23, 0.34);
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

/* Semantic Dark-Glass Alerts (crisp light ink in both light & dark Streamlit bases) */
[data-testid="stMainBlockContainer"] [data-testid="stAlert"],
section[data-testid="stSidebar"] [data-testid="stAlert"] {
  border-radius: 14px !important;
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.32) !important;
}
[data-testid="stMainBlockContainer"] [data-testid="stAlertContainer"],
section[data-testid="stSidebar"] [data-testid="stAlertContainer"],
[data-testid="stMainBlockContainer"] [data-testid="stAlert"] > div {
  background: rgba(12, 32, 66, 0.84) !important;
  border: 1px solid rgba(96, 165, 250, 0.44) !important;
  border-radius: 14px !important;
  backdrop-filter: blur(18px) saturate(165%) !important;
  -webkit-backdrop-filter: blur(18px) saturate(165%) !important;
  color: #E0F2FE !important;
}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) {
  background: rgba(12, 36, 72, 0.86) !important;
  border-color: rgba(56, 189, 248, 0.50) !important;
}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) {
  background: rgba(8, 48, 36, 0.86) !important;
  border-color: rgba(52, 211, 153, 0.50) !important;
}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {
  background: rgba(66, 42, 8, 0.88) !important;
  border-color: rgba(251, 191, 36, 0.54) !important;
}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {
  background: rgba(74, 16, 26, 0.88) !important;
  border-color: rgba(248, 113, 113, 0.54) !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] li,
[data-testid="stAlert"] span,
[data-testid="stAlert"] strong,
[data-testid="stAlert"] a {
  color: #F8FAFC !important;
  text-shadow: none !important;
}
[data-testid="stAlertContentInfo"] p,
[data-testid="stAlertContentInfo"] li,
[data-testid="stAlertContentInfo"] strong {
  color: #E0F2FE !important;
}
[data-testid="stAlertContentSuccess"] p,
[data-testid="stAlertContentSuccess"] li,
[data-testid="stAlertContentSuccess"] strong {
  color: #D1FAE5 !important;
}
[data-testid="stAlertContentWarning"] p,
[data-testid="stAlertContentWarning"] li,
[data-testid="stAlertContentWarning"] strong {
  color: #FEF3C7 !important;
}
[data-testid="stAlertContentError"] p,
[data-testid="stAlertContentError"] li,
[data-testid="stAlertContentError"] strong {
  color: #FEE2E2 !important;
}
[data-testid="stAlert"] code {
  background: rgba(255, 255, 255, 0.14) !important;
  color: #FEF08A !important;
  border: 1px solid rgba(255, 255, 255, 0.22) !important;
  padding: 2px 6px !important;
  border-radius: 5px !important;
}

/* Dropdown popovers, Virtual Selectboxes & DateInput Calendars */
[data-testid="stSelectboxVirtualDropdown"],
[data-testid="stMultiSelectDropdown"],
[data-testid="stDateInputCalendar"],
[data-testid="stDateInputQuickSelectPopover"],
[data-baseweb="popover"],
[role="listbox"] {
  background: rgba(10, 20, 38, 0.96) !important;
  border: 1px solid rgba(255, 255, 255, 0.18) !important;
  color: #F8FAFC !important;
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
}
[role="option"],
[data-testid="stSelectboxVirtualDropdown"] li,
[data-testid="stMultiSelectDropdown"] li,
[data-testid="stDateInputCalendar"] [role="gridcell"],
[data-testid="stDateInputCalendar"] button,
[data-testid="stDateInputCalendar"] span {
  color: #F8FAFC !important;
}
[role="option"] {
  background: transparent !important;
}
[role="option"]:hover,
[role="option"][aria-selected="true"],
[data-testid="stSelectboxVirtualDropdown"] li:hover,
[data-testid="stMultiSelectDropdown"] li:hover {
  background: rgba(56, 189, 248, 0.22) !important;
  color: #FFFFFF !important;
}

/* Inputs, Textareas, NumberInputs, Selectboxes, DateInputs, Code & Sliders (Dark Glass + Crisp Bright Ink) */
[data-testid="stMainBlockContainer"] [data-baseweb="input"],
[data-testid="stMainBlockContainer"] [data-baseweb="base-input"],
[data-testid="stMainBlockContainer"] [data-baseweb="textarea"],
[data-testid="stMainBlockContainer"] [data-testid="stTextInputRootElement"],
[data-testid="stMainBlockContainer"] [data-testid="stTextAreaRootElement"],
[data-testid="stMainBlockContainer"] [data-testid="stNumberInputContainer"],
[data-testid="stMainBlockContainer"] [data-testid="stDateInputField"],
[data-testid="stMainBlockContainer"] [data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stMainBlockContainer"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
[data-testid="stMainBlockContainer"] [data-baseweb="select"] > div {
  border-radius: 12px !important;
  border: 1px solid rgba(255, 255, 255, 0.24) !important;
  min-height: 46px;
  background: rgba(8, 17, 34, 0.78) !important;
  background-color: rgba(8, 17, 34, 0.78) !important;
  color: #F8FAFC !important;
  transition: all 0.2s ease !important;
}

[data-testid="stMainBlockContainer"] [data-testid="stTextArea"] textarea,
[data-testid="stMainBlockContainer"] [data-baseweb="textarea"] textarea {
  background: rgba(8, 17, 34, 0.78) !important;
  background-color: rgba(8, 17, 34, 0.78) !important;
  color: #F8FAFC !important;
  -webkit-text-fill-color: #F8FAFC !important;
  caret-color: #38BDF8 !important;
}

[data-testid="stMainBlockContainer"] [data-testid="stTextInput"] input,
[data-testid="stMainBlockContainer"] [data-testid="stNumberInput"] input,
[data-testid="stMainBlockContainer"] [data-testid="stDateInput"] input,
[data-testid="stMainBlockContainer"] [data-testid="stSelectbox"] input,
[data-testid="stMainBlockContainer"] [data-testid="stMultiSelect"] input,
[data-testid="stMainBlockContainer"] [data-baseweb="input"] input,
[data-testid="stMainBlockContainer"] [data-baseweb="base-input"] input {
  background: transparent !important;
  background-color: transparent !important;
  color: #F8FAFC !important;
  -webkit-text-fill-color: #F8FAFC !important;
  caret-color: #38BDF8 !important;
}

[data-testid="stMainBlockContainer"] [data-testid="stSelectbox"] [data-baseweb="select"] *,
[data-testid="stMainBlockContainer"] [data-testid="stMultiSelect"] [data-baseweb="select"] *,
[data-testid="stMainBlockContainer"] [data-testid="stDateInputField"] *,
[data-testid="stMainBlockContainer"] [data-baseweb="select"] span,
[data-testid="stMainBlockContainer"] [data-baseweb="select"] div {
  color: #F8FAFC !important;
}
[data-testid="stMainBlockContainer"] [data-testid="stSelectbox"] [data-baseweb="select"] > div > div,
[data-testid="stMainBlockContainer"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div > div {
  background: transparent !important;
  background-color: transparent !important;
}

[data-testid="stMainBlockContainer"] [data-baseweb="tag"] {
  background: rgba(56, 189, 248, 0.22) !important;
  border: 1px solid rgba(125, 211, 252, 0.45) !important;
  color: #F8FAFC !important;
}

[data-testid="stMainBlockContainer"] [data-baseweb="input"] input::placeholder,
[data-testid="stMainBlockContainer"] [data-baseweb="textarea"] textarea::placeholder,
[data-testid="stMainBlockContainer"] textarea::placeholder,
[data-testid="stMainBlockContainer"] input::placeholder {
  color: #94A3B8 !important;
  -webkit-text-fill-color: #94A3B8 !important;
  opacity: 1 !important;
}

[data-testid="stMainBlockContainer"] textarea::selection,
[data-testid="stMainBlockContainer"] input::selection {
  background: rgba(56, 189, 248, 0.42) !important;
  color: #FFFFFF !important;
}

[data-testid="stMainBlockContainer"] [data-baseweb="select"] svg {
  color: #CBD5E1 !important;
  fill: #CBD5E1 !important;
}

[data-testid="stMainBlockContainer"] [data-testid="stNumberInputStepDown"],
[data-testid="stMainBlockContainer"] [data-testid="stNumberInputStepUp"] {
  background: rgba(255, 255, 255, 0.08) !important;
  color: #F8FAFC !important;
  border: none !important;
  box-shadow: none !important;
  min-height: auto !important;
}
[data-testid="stMainBlockContainer"] [data-testid="stNumberInputStepDown"] svg,
[data-testid="stMainBlockContainer"] [data-testid="stNumberInputStepUp"] svg {
  color: #E2E8F0 !important;
  fill: #E2E8F0 !important;
}

[data-testid="stMainBlockContainer"] [data-testid="stTextInput"] button,
[data-testid="stMainBlockContainer"] [data-testid="stTextInputClearButton"],
[data-testid="stMainBlockContainer"] [data-testid="stNumberInputClearButton"],
[data-testid="stMainBlockContainer"] [data-testid="stDateInputCalendarButton"],
[data-testid="stMainBlockContainer"] [data-testid="stDateInputClearButton"] {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  min-height: auto !important;
  color: #CBD5E1 !important;
}

[data-testid="stMainBlockContainer"] [data-testid="stCode"],
[data-testid="stMainBlockContainer"] pre {
  background: rgba(6, 13, 28, 0.86) !important;
  border: 1px solid rgba(255, 255, 255, 0.18) !important;
  border-radius: 12px !important;
  color: #E2E8F0 !important;
}
[data-testid="stMainBlockContainer"] pre code {
  background: transparent !important;
  color: #E2E8F0 !important;
}

[data-testid="stMainBlockContainer"] [data-testid="stSliderThumbValue"],
[data-testid="stMainBlockContainer"] [data-testid="stSliderTickBarMin"],
[data-testid="stMainBlockContainer"] [data-testid="stSliderTickBarMax"] {
  color: #E2E8F0 !important;
}

[data-baseweb="input"]:focus-within,
[data-baseweb="base-input"]:focus-within,
[data-baseweb="textarea"]:focus-within,
[data-testid="stTextInputRootElement"]:focus-within,
[data-testid="stTextAreaRootElement"]:focus-within,
[data-testid="stNumberInputContainer"]:focus-within,
[data-testid="stDateInputField"]:focus-within,
[data-baseweb="select"] > div:focus-within {
  border-color: #38BDF8 !important;
  box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.28) !important;
}

/* Modern Liquid Glass Buttons */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button, .stLinkButton > a {
  min-height: 48px;
  border-radius: 14px !important;
  font-weight: 700 !important;
  letter-spacing: -0.01em;
  transition: all 0.24s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

[data-testid="stMainBlockContainer"] .stButton > button:not([kind="primary"]),
[data-testid="stMainBlockContainer"] .stDownloadButton > button:not([kind="primary"]),
[data-testid="stMainBlockContainer"] .stFormSubmitButton > button:not([kind="primary"]),
[data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondary"],
[data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondaryFormSubmit"],
[data-testid="stMainBlockContainer"] .stLinkButton > a {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.24) 0%, rgba(255, 255, 255, 0.08) 48%, rgba(56, 189, 248, 0.14) 100%),
    rgba(15, 28, 54, 0.44) !important;
  backdrop-filter: blur(22px) saturate(200%) !important;
  -webkit-backdrop-filter: blur(22px) saturate(200%) !important;
  border: 1px solid rgba(255, 255, 255, 0.36) !important;
  border-radius: 14px !important;
  color: #FFFFFF !important;
  box-shadow:
    0 10px 28px rgba(2, 8, 23, 0.42),
    inset 0 1.5px 1px rgba(255, 255, 255, 0.50),
    inset 0 -1px 2px rgba(56, 189, 248, 0.24) !important;
}

[data-testid="stMainBlockContainer"] .stButton > button:not([kind="primary"]) *,
[data-testid="stMainBlockContainer"] .stDownloadButton > button:not([kind="primary"]) *,
[data-testid="stMainBlockContainer"] .stFormSubmitButton > button:not([kind="primary"]) *,
[data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondary"] *,
[data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondaryFormSubmit"] *,
[data-testid="stMainBlockContainer"] .stLinkButton > a * {
  color: #FFFFFF !important;
}

[data-testid="stMainBlockContainer"] .stButton > button:not([kind="primary"]):hover,
[data-testid="stMainBlockContainer"] .stDownloadButton > button:not([kind="primary"]):hover,
[data-testid="stMainBlockContainer"] .stFormSubmitButton > button:not([kind="primary"]):hover,
[data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondary"]:hover,
[data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondaryFormSubmit"]:hover,
[data-testid="stMainBlockContainer"] .stLinkButton > a:hover {
  transform: translateY(-2px) scale(1.008) !important;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.84) 0%, rgba(14, 165, 233, 0.78) 100%) !important;
  border-color: rgba(186, 230, 253, 0.78) !important;
  box-shadow:
    0 14px 34px rgba(37, 99, 235, 0.48),
    inset 0 1.5px 1px rgba(255, 255, 255, 0.65),
    inset 0 -1px 2px rgba(56, 189, 248, 0.35) !important;
}

.stButton > button:hover, .stLinkButton > a:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 32px rgba(2, 8, 23, 0.36) !important;
}

.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"],
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"],
button[kind="primary"],
button[kind="primaryFormSubmit"] {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0.04) 48%, rgba(14, 165, 233, 0.16) 100%),
    linear-gradient(135deg, rgba(37, 99, 235, 0.88) 0%, rgba(14, 165, 233, 0.82) 100%) !important;
  backdrop-filter: blur(20px) saturate(200%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(200%) !important;
  border: 1px solid rgba(186, 230, 253, 0.62) !important;
  border-radius: 14px !important;
  color: #FFFFFF !important;
  box-shadow:
    0 12px 32px rgba(37, 99, 235, 0.48),
    inset 0 1.5px 1px rgba(255, 255, 255, 0.62),
    inset 0 -1px 2px rgba(6, 182, 212, 0.36) !important;
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
  transform: translateY(-2px) scale(1.008) !important;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.30) 0%, rgba(255, 255, 255, 0.06) 48%, rgba(56, 189, 248, 0.22) 100%),
    linear-gradient(135deg, rgba(59, 130, 246, 0.94) 0%, rgba(6, 182, 212, 0.90) 100%) !important;
  border-color: rgba(224, 242, 254, 0.84) !important;
  box-shadow:
    0 16px 38px rgba(37, 99, 235, 0.56),
    inset 0 1.5px 1px rgba(255, 255, 255, 0.72),
    inset 0 -1px 2px rgba(6, 182, 212, 0.45) !important;
}

[data-testid="stMainBlockContainer"] button:disabled {
  opacity: 0.52 !important;
  color: #CBD5E1 !important;
  cursor: not-allowed !important;
}

/* Modern Tabs (Dark Glass Pill Bar — Streamlit 1.6x React Aria & BaseWeb) */
[data-testid="stTabs"] [role="tablist"],
[data-baseweb="tab-list"] {
  background: rgba(10, 20, 38, 0.62) !important;
  backdrop-filter: blur(18px) saturate(165%) !important;
  -webkit-backdrop-filter: blur(18px) saturate(165%) !important;
  border: 1px solid rgba(255, 255, 255, 0.16) !important;
  border-radius: 14px !important;
  padding: 5px 6px !important;
  gap: 6px !important;
  box-shadow: 0 10px 26px rgba(2, 6, 23, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.14) !important;
}

[data-testid="stTabs"] [role="tablist"]::after {
  display: none !important;
  background: transparent !important;
}

[data-testid="stTabs"] [data-testid="stTab"],
[data-testid="stTabs"] [role="tab"],
button[data-baseweb="tab"] {
  min-height: 42px !important;
  height: auto !important;
  font-weight: 700 !important;
  font-size: 0.94rem !important;
  border-radius: 10px !important;
  padding: 8px 16px !important;
  background: transparent !important;
  border: 1px solid transparent !important;
  color: #E2E8F0 !important;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

[data-testid="stTabs"] [data-testid="stTab"] *,
[data-testid="stTabs"] [role="tab"] *,
button[data-baseweb="tab"] p {
  color: #E2E8F0 !important;
  text-shadow: none !important;
  min-height: auto !important;
  padding: 0 !important;
  margin: 0 !important;
  font-weight: 700 !important;
}

[data-testid="stTabs"] [data-testid="stTab"]:hover,
[data-testid="stTabs"] [data-testid="stTab"][data-hovered],
[data-testid="stTabs"] [role="tab"]:hover,
button[data-baseweb="tab"]:hover {
  background: rgba(255, 255, 255, 0.10) !important;
  color: #FFFFFF !important;
}

[data-testid="stTabs"] [data-testid="stTab"]:hover *,
[data-testid="stTabs"] [data-testid="stTab"][data-hovered] *,
[data-testid="stTabs"] [role="tab"]:hover *,
button[data-baseweb="tab"]:hover * {
  color: #FFFFFF !important;
}

[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"],
[data-testid="stTabs"] [data-testid="stTab"][data-selected="true"],
[data-testid="stTabs"] [data-testid="stTab"][data-selected],
[data-testid="stTabs"] [role="tab"][aria-selected="true"],
button[data-baseweb="tab"][aria-selected="true"] {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.24) 0%, rgba(255, 255, 255, 0.05) 50%, rgba(56, 189, 248, 0.18) 100%),
    linear-gradient(135deg, rgba(37, 99, 235, 0.86) 0%, rgba(14, 165, 233, 0.80) 100%) !important;
  border: 1px solid rgba(186, 230, 253, 0.56) !important;
  color: #FFFFFF !important;
  box-shadow:
    0 8px 22px rgba(37, 99, 235, 0.36),
    inset 0 1.5px 1px rgba(255, 255, 255, 0.50) !important;
}

[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] *,
[data-testid="stTabs"] [data-testid="stTab"][data-selected="true"] *,
[data-testid="stTabs"] [data-testid="stTab"][data-selected] *,
[data-testid="stTabs"] [role="tab"][aria-selected="true"] *,
button[data-baseweb="tab"][aria-selected="true"] * {
  color: #FFFFFF !important;
}

[data-testid="stTabs"] .react-aria-SelectionIndicator {
  display: none !important;
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
.rw-visual-head{display:flex;align-items:center;justify-content:space-between;gap:8px;white-space:nowrap;font-size:.78rem;font-weight:700;color:white;margin-bottom:14px}
.rw-visual-dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:#10B981;margin-right:6px;box-shadow:0 0 0 4px rgba(16,185,129,.22)}
.rw-visual-road{height:108px;position:relative;border-radius:14px;background:linear-gradient(137deg,#1E293B,#334155);border:1px solid rgba(255,255,255,.12);overflow:hidden}
.rw-visual-road:after{content:"";position:absolute;left:24%;top:-35px;width:52%;height:190px;transform:rotate(23deg);background:#1E293B;border-left:4px solid #E2E8F0;border-right:4px solid #E2E8F0}
/* Hero animated story (8s loop): AI scan -> D40 detected -> verified -> fixed */
.rw-road-line{position:absolute;left:49%;top:-35px;width:4px;height:190px;transform:rotate(23deg);z-index:1;background:repeating-linear-gradient(to bottom,#FBBF24 0 15px,transparent 15px 31px);animation:rwDash 1.1s linear infinite}
.rw-road-scan{position:absolute;left:0;right:0;top:0;height:2px;z-index:3;pointer-events:none;opacity:0;background:linear-gradient(90deg,transparent,#22D3EE 20%,#A5F3FC 50%,#22D3EE 80%,transparent);box-shadow:0 0 10px 2px rgba(34,211,238,.65);animation:rwScan 8s linear infinite}
.rw-road-scan::before{content:"";position:absolute;left:0;right:0;bottom:2px;height:26px;background:linear-gradient(to top,rgba(34,211,238,.22),transparent)}
.rw-road-pin{position:absolute;z-index:2;left:53%;top:28px;background:rgba(239,68,68,.2);border:2px solid #EF4444;width:36px;height:28px;border-radius:6px;box-shadow:0 0 16px rgba(239,68,68,.45);animation:rwPin 8s ease-in-out infinite}
.rw-pin-tag{position:absolute;top:-17px;left:-2px;white-space:nowrap;font-style:normal;font-size:9px;font-weight:800;line-height:1.35;padding:1px 5px;border-radius:3px;opacity:0}
.rw-tag-red{background:#DC2626;color:#FFFFFF;animation:rwTagRed 8s ease-in-out infinite}
.rw-tag-amber{background:#F59E0B;color:#111827;animation:rwTagAmber 8s ease-in-out infinite}
.rw-tag-green{background:#059669;color:#FFFFFF;animation:rwTagGreen 8s ease-in-out infinite}
.rw-visual-flow{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:14px}
.rw-visual-flow span{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.20);border-radius:9px;text-align:center;color:#F8FAFC;font-size:.70rem;padding:6px 5px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rw-visual-flow span:nth-child(1){animation:rwStep1 8s ease-in-out infinite}
.rw-visual-flow span:nth-child(2){animation:rwStep2 8s ease-in-out infinite}
.rw-visual-flow span:nth-child(3){animation:rwStep3 8s ease-in-out infinite}
.rw-visual-flow span:nth-child(4){animation:rwStep4 8s ease-in-out infinite}
@keyframes rwDash{from{background-position:0 0}to{background-position:0 31px}}
@keyframes rwScan{0%,6%{opacity:0;transform:translateY(-8px)}7%{opacity:1}29%{opacity:1;transform:translateY(112px)}30%,100%{opacity:0;transform:translateY(112px)}}
@keyframes rwPin{
  0%,12%{opacity:0;transform:scale(1.35);border-color:#EF4444;background:rgba(239,68,68,.2);box-shadow:0 0 16px rgba(239,68,68,.45)}
  16%{opacity:1;transform:scale(1)}
  38%{border-color:#EF4444;background:rgba(239,68,68,.2);box-shadow:0 0 16px rgba(239,68,68,.45)}
  42%,63%{border-color:#F59E0B;background:rgba(245,158,11,.2);box-shadow:0 0 16px rgba(245,158,11,.45)}
  67%,92%{opacity:1;transform:scale(1);border-color:#10B981;background:rgba(16,185,129,.22);box-shadow:0 0 18px rgba(16,185,129,.55)}
  100%{opacity:0;transform:scale(1);border-color:#10B981;background:rgba(16,185,129,.22);box-shadow:0 0 18px rgba(16,185,129,.55)}
}
@keyframes rwTagRed{0%,13%{opacity:0;transform:translateY(3px)}17%,38%{opacity:1;transform:translateY(0)}42%,100%{opacity:0;transform:translateY(0)}}
@keyframes rwTagAmber{0%,39%{opacity:0}43%,63%{opacity:1}67%,100%{opacity:0}}
@keyframes rwTagGreen{0%,64%{opacity:0}68%,92%{opacity:1}97%,100%{opacity:0}}
@keyframes rwStep1{0%{background:rgba(255,255,255,.14);border-color:rgba(255,255,255,.20);box-shadow:none}2%,5%{background:rgba(56,189,248,.28);border-color:#38BDF8;box-shadow:0 0 12px rgba(56,189,248,.45)}8%,100%{background:rgba(255,255,255,.14);border-color:rgba(255,255,255,.20);box-shadow:none}}
@keyframes rwStep2{0%,5%{background:rgba(255,255,255,.14);border-color:rgba(255,255,255,.20);box-shadow:none}8%,37%{background:rgba(34,211,238,.26);border-color:#22D3EE;box-shadow:0 0 12px rgba(34,211,238,.45)}41%,100%{background:rgba(255,255,255,.14);border-color:rgba(255,255,255,.20);box-shadow:none}}
@keyframes rwStep3{0%,38%{background:rgba(255,255,255,.14);border-color:rgba(255,255,255,.20);box-shadow:none}42%,62%{background:rgba(245,158,11,.26);border-color:#F59E0B;box-shadow:0 0 12px rgba(245,158,11,.45)}66%,100%{background:rgba(255,255,255,.14);border-color:rgba(255,255,255,.20);box-shadow:none}}
@keyframes rwStep4{0%,63%{background:rgba(255,255,255,.14);border-color:rgba(255,255,255,.20);box-shadow:none}67%,93%{background:rgba(16,185,129,.28);border-color:#10B981;box-shadow:0 0 12px rgba(16,185,129,.45)}97%,100%{background:rgba(255,255,255,.14);border-color:rgba(255,255,255,.20);box-shadow:none}}
@media (prefers-reduced-motion: reduce){
  .rw-road-scan{display:none}
  .rw-road-line,.rw-road-pin,.rw-pin-tag,.rw-visual-flow span{animation:none !important}
  .rw-tag-red{opacity:1}
}

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
.rw-defect-card::before{content:"";position:absolute;top:0;left:18px;right:18px;height:3px;border-radius:0 0 999px 999px;background:var(--defect-accent, #38BDF8);box-shadow:0 0 12px var(--defect-accent, #38BDF8);opacity:.9}
.rw-defect-card:hover{transform:translateY(-3px);box-shadow:0 24px 52px rgba(2,6,23,.48);border-color:rgba(255,255,255,.34)}
.rw-defect-top{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.rw-defect-code{display:inline-flex;align-items:center;white-space:nowrap;flex-shrink:0;font-size:.72rem;line-height:1.2;font-weight:800;padding:4px 10px;border-radius:999px;letter-spacing:.02em}
.rw-defect-weight{white-space:nowrap;font-size:.72rem;font-weight:600;color:#94A3B8;font-variant-numeric:tabular-nums;letter-spacing:.01em}
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
[data-testid="stMainBlockContainer"] code,
section[data-testid="stSidebar"] code,
[data-testid="stMainBlockContainer"] .rw-empty code,
[data-testid="stMainBlockContainer"] .rw-hint code,
[data-testid="stMainBlockContainer"] .rw-glass-card code {
  background: rgba(15, 28, 54, 0.86) !important;
  background-color: rgba(15, 28, 54, 0.86) !important;
  color: #FEF08A !important;
  border: 1px solid rgba(125, 211, 252, 0.32) !important;
  padding: 2px 7px !important;
  border-radius: 6px !important;
  font-size: 0.88em !important;
  font-weight: 600 !important;
  text-shadow: none !important;
}
[data-testid="stMainBlockContainer"] pre code,
section[data-testid="stSidebar"] pre code {
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  padding: 0 !important;
  color: #E2E8F0 !important;
  font-weight: 400 !important;
}
.rw-preview-banner{background:linear-gradient(135deg, rgba(15,23,42,.88) 0%, rgba(30,58,138,.88) 100%);backdrop-filter:blur(16px);border:1px solid rgba(96,165,250,.65);color:#FFFFFF;padding:12px 20px;border-radius:14px;font-size:.93rem;font-weight:600;letter-spacing:.02em;margin:16px 0 12px;display:flex;align-items:center;gap:10px;box-shadow:0 12px 28px rgba(2,8,23,.30)}

/* CTA Page Links & Two-Column Panels (Liquid Glass) */
[data-testid="stPageLink-NavLink"]{
  display:flex !important;align-items:center;justify-content:flex-start !important;width:100% !important;min-height:50px;padding:12px 18px !important;
  border-radius:14px !important;border:1px solid rgba(255,255,255,.34) !important;
  background:linear-gradient(180deg, rgba(255,255,255,.24) 0%, rgba(255,255,255,.08) 48%, rgba(56,189,248,.14) 100%), rgba(15,28,54,.44) !important;
  backdrop-filter:blur(22px) saturate(200%) !important;-webkit-backdrop-filter:blur(22px) saturate(200%) !important;
  color:#FFFFFF !important;font-weight:700 !important;
  box-shadow:0 10px 28px rgba(2,8,23,.40), inset 0 1.5px 1px rgba(255,255,255,.48), inset 0 -1px 2px rgba(56,189,248,.22);
  transition:all .24s cubic-bezier(0.16,1,0.3,1) !important;text-decoration:none !important;
}
[data-testid="stPageLink-NavLink"] *{color:#FFFFFF !important;}
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

[data-testid="stMainBlockContainer"] [data-testid="stExpander"] summary:hover {
  background: rgba(255, 255, 255, 0.06) !important;
  color: #FFFFFF !important;
}

[data-testid="stColumn"], [data-testid="column"] {
  transition: flex-basis 0.25s ease, min-width 0.25s ease, transform 0.25s ease;
}

@media (max-width: 820px) {
  [data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
    gap: 14px !important;
  }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"] > [data-testid="column"] {
    flex: 1 1 calc(50% - 14px) !important;
    min-width: min(100%, 220px) !important;
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
  [data-testid="stMainBlockContainer"],
  .stMainBlockContainer,
  .main .block-container,
  .block-container {
    padding: 1rem 0.9rem 108px 0.9rem !important;
  }
  .sol-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
  [data-testid="stHorizontalBlock"]:not(.st-key-rw_mobile_dock [data-testid="stHorizontalBlock"]) {
    flex-wrap: wrap !important;
    gap: 0.9rem !important;
  }
  [data-testid="stHorizontalBlock"]:not(.st-key-rw_mobile_dock [data-testid="stHorizontalBlock"]) > [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"]:not(.st-key-rw_mobile_dock [data-testid="stHorizontalBlock"]) > [data-testid="column"] {
    flex: 1 1 100% !important;
    min-width: 100% !important;
  }
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

@keyframes rwLivePulse{0%,100%{box-shadow:0 0 0 0 rgba(52,211,153,.55);opacity:1}60%{box-shadow:0 0 0 7px rgba(52,211,153,0);opacity:.85}}
@keyframes rwHeadShimmer{0%{transform:translateX(-120%)}100%{transform:translateX(260%)}}
.rw-page-head{position:relative;overflow:hidden;margin:0 0 18px;padding:16px 20px;border-radius:16px;background:linear-gradient(135deg,rgba(14,32,64,.78) 0%,rgba(8,20,42,.64) 100%);border:1px solid rgba(125,211,252,.22);border-left:4px solid #38BDF8;backdrop-filter:blur(18px) saturate(165%);-webkit-backdrop-filter:blur(18px) saturate(165%);box-shadow:0 14px 34px rgba(2,6,23,.34),inset 0 1px 0 rgba(255,255,255,.14)}
.rw-page-head::after{content:"";position:absolute;top:0;left:0;width:36%;height:2px;background:linear-gradient(90deg,transparent,rgba(56,189,248,.85),rgba(125,211,252,.95),transparent);animation:rwHeadShimmer 7s ease-in-out infinite;pointer-events:none}
.rw-page-head-top{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:4px}
.rw-page-head h1{font-family:var(--rw-font) !important;color:#FFFFFF !important;font-size:clamp(1.28rem,2vw,1.65rem) !important;font-weight:800 !important;line-height:1.25 !important;margin:0 !important;letter-spacing:-0.015em}
.rw-page-head p{color:#CBD5E1 !important;font-size:.88rem !important;margin:0 !important;line-height:1.5}
.rw-live-pill{display:inline-flex;align-items:center;gap:7px;font-size:.72rem;font-weight:700;color:#A7F3D0;background:rgba(16,185,129,.14);border:1px solid rgba(52,211,153,.32);border-radius:999px;padding:4px 11px;white-space:nowrap}
.rw-live-dot{width:7px;height:7px;border-radius:50%;background:#34D399;animation:rwLivePulse 2.4s ease-out infinite;display:inline-block}
.rw-kpi-row{display:grid;gap:12px;margin:10px 0 18px}
.rw-kpi-cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}
.rw-kpi-cols-3{grid-template-columns:repeat(3,minmax(0,1fr))}
.rw-kpi-cols-4{grid-template-columns:repeat(4,minmax(0,1fr))}
.rw-kpi-cols-5{grid-template-columns:repeat(5,minmax(0,1fr))}
.rw-kpi-card{position:relative;overflow:hidden;background:linear-gradient(155deg,rgba(255,255,255,.08) 0%,rgba(255,255,255,.02) 100%),rgba(11,24,48,.76);border:1px solid rgba(148,163,184,.24);border-radius:15px;padding:14px 16px;min-width:0;box-shadow:0 10px 26px rgba(2,6,23,.28),inset 0 1px 0 rgba(255,255,255,.14);transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease}
.rw-kpi-card::before{content:"";position:absolute;top:0;left:14px;right:14px;height:3px;border-radius:0 0 6px 6px;background:var(--kpi-accent,#38BDF8);box-shadow:0 0 12px var(--kpi-glow,rgba(56,189,248,.55))}
.rw-kpi-card:hover{transform:translateY(-3px);border-color:rgba(125,211,252,.42);box-shadow:0 16px 34px rgba(2,6,23,.38)}
.rw-kpi-blue{--kpi-accent:#38BDF8;--kpi-glow:rgba(56,189,248,.55)}
.rw-kpi-green{--kpi-accent:#34D399;--kpi-glow:rgba(52,211,153,.55)}
.rw-kpi-amber{--kpi-accent:#FBBF24;--kpi-glow:rgba(251,191,36,.55)}
.rw-kpi-red{--kpi-accent:#F87171;--kpi-glow:rgba(248,113,113,.55)}
.rw-kpi-slate{--kpi-accent:#94A3B8;--kpi-glow:rgba(148,163,184,.4)}
.rw-kpi-card small{display:block;color:#94A3B8;font-size:.75rem;font-weight:600;margin-bottom:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rw-kpi-card strong{display:block;color:#F8FAFC;font-size:clamp(1.02rem,1.45vw,1.35rem);font-weight:800;line-height:1.25;font-variant-numeric:tabular-nums;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rw-kpi-sub{display:block;color:#94A3B8;font-size:.72rem;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
[data-testid="stVerticalBlockBorderWrapper"]{transition:border-color .22s ease,box-shadow .22s ease}
[data-testid="stVerticalBlockBorderWrapper"]:hover{border-color:rgba(125,211,252,.28) !important}
iframe[title*="streamlit_folium"]{border-radius:14px !important;border:1px solid rgba(148,163,184,.28) !important;box-shadow:0 14px 32px rgba(2,6,23,.42) !important}
@media (max-width: 960px){.rw-kpi-cols-4,.rw-kpi-cols-5{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width: 520px){.rw-kpi-row{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (prefers-reduced-motion: reduce){.rw-page-head::after,.rw-live-dot{animation:none !important}.rw-kpi-card:hover{transform:none}}

/* Wrap tablist gracefully at 1280px, prevent long RW codes overflowing, hide blank geolocation iframe */
[data-testid="stTabs"] [role="tablist"] {
  flex-wrap: wrap !important;
  row-gap: 6px !important;
}
.rw-empty code {
  overflow-wrap: anywhere !important;
  word-break: break-word !important;
}
iframe[title*="streamlit_js_eval"] {
  height: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  display: block !important;
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
  [data-testid="stMainBlockContainer"],
  .stMainBlockContainer,
  .main .block-container,
  .block-container {
    padding: 1rem 0.9rem 108px 0.9rem !important;
  }
  .sol-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
  [data-testid="stHorizontalBlock"]:not(.st-key-rw_mobile_dock [data-testid="stHorizontalBlock"]) {
    flex-wrap: wrap !important;
    gap: 0.9rem !important;
  }
  [data-testid="stHorizontalBlock"]:not(.st-key-rw_mobile_dock [data-testid="stHorizontalBlock"]) > [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"]:not(.st-key-rw_mobile_dock [data-testid="stHorizontalBlock"]) > [data-testid="column"] {
    flex: 1 1 100% !important;
    min-width: 100% !important;
  }
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
