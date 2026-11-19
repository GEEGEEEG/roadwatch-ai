"""RoadWatch AI - Modern Dashboard & Glassmorphism Design System v5.0."""
import streamlit as st

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

/* Main app container — Aurora Mesh + Tech Coordinate Dot Grid */
.stApp {
  background-color: #F1F5F9;
  background-image:
    radial-gradient(circle at 15% 12%, rgba(56, 189, 248, 0.14), transparent 36%),
    radial-gradient(circle at 88% 8%, rgba(37, 99, 235, 0.13), transparent 40%),
    radial-gradient(circle at 82% 85%, rgba(16, 185, 129, 0.08), transparent 38%),
    radial-gradient(rgba(100, 116, 139, 0.16) 1px, transparent 1px);
  background-size: 100% 100%, 100% 100%, 100% 100%, 24px 24px;
  background-attachment: fixed;
  color: var(--rw-ink);
  font-size: 15px;
  line-height: 1.65;
}

[data-testid="stHeader"] {
  background: rgba(241, 245, 249, 0.72) !important;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid rgba(203, 213, 225, 0.55);
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

/* Typography */
h1, h2, h3, h4 {
  font-family: var(--rw-font) !important;
  font-weight: 700 !important;
  color: var(--rw-navy);
  letter-spacing: -0.015em !important;
  line-height: 1.26 !important;
}

h1 { font-size: clamp(1.85rem, 3.8vw, 2.55rem); }
h2 { font-size: clamp(1.38rem, 2.4vw, 1.9rem); }
h3 { font-size: 1.15rem; }

/* Deep Midnight Navy Command Sidebar */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #071326 0%, #0A1B38 55%, #0F2952 100%) !important;
  border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
  box-shadow: 4px 0 28px rgba(7, 19, 38, 0.22) !important;
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

/* Glassmorphism Cards & Forms */
[data-testid="stForm"], [data-testid="stExpander"] {
  border: 1px solid var(--rw-border-glass) !important;
  border-radius: var(--rw-radius) !important;
  background: var(--rw-card-bg) !important;
  box-shadow: var(--rw-shadow-sm) !important;
  transition: all 0.25s ease;
}

[data-testid="stForm"]:hover, [data-testid="stExpander"]:hover {
  box-shadow: var(--rw-shadow-md) !important;
}

/* Modern Metric Cards */
[data-testid="stMetric"] {
  border: 1px solid var(--rw-line) !important;
  border-top: 3px solid var(--rw-blue) !important;
  border-radius: var(--rw-radius) !important;
  background: #FFFFFF !important;
  padding: 1.15rem 1.25rem !important;
  box-shadow: var(--rw-shadow-sm) !important;
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease, border-color 0.2s ease;
}

[data-testid="stMetric"]:hover {
  transform: translateY(-2px);
  box-shadow: var(--rw-shadow-md) !important;
  border-color: #93C5FD !important;
  border-top-color: var(--rw-blue-dark) !important;
}

[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] > div,
[data-testid="stMetricLabel"] p {
  color: #64748B !important;
  font-size: 0.82rem !important;
  font-weight: 600 !important;
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
  color: var(--rw-navy) !important;
  letter-spacing: -0.02em;
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: unset !important;
  overflow-wrap: break-word !important;
}

/* Dropzone Uploader & DataFrames */
[data-testid="stFileUploader"] section {
  border: 2px dashed #93C5FD !important;
  border-radius: 16px !important;
  background: linear-gradient(180deg, #F8FAFF 0%, #EFF6FF 100%) !important;
  padding: 1.25rem !important;
  transition: all 0.2s ease !important;
}
[data-testid="stFileUploader"] section:hover {
  border-color: #2563EB !important;
  background: #EFF6FF !important;
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.1) !important;
}

[data-testid="stDataFrame"] {
  border: 1px solid var(--rw-line) !important;
  border-radius: 14px !important;
  overflow: hidden !important;
  box-shadow: var(--rw-shadow-sm) !important;
  background: #FFFFFF !important;
}

/* Inputs, Textareas, Selectboxes */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {
  border-radius: 12px !important;
  border-color: #CBD5E1 !important;
  min-height: 46px;
  background: #FFFFFF !important;
  transition: all 0.2s ease !important;
}

[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"] > div:focus-within {
  border-color: #2563EB !important;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
}

/* Modern Buttons */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button, .stLinkButton > a {
  min-height: 48px;
  border-radius: 12px !important;
  font-weight: 700 !important;
  letter-spacing: -0.01em;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

.stButton > button:hover, .stLinkButton > a:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.1) !important;
}

.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
  border: none !important;
  color: #FFFFFF !important;
  box-shadow: 0 6px 18px rgba(37, 99, 235, 0.25) !important;
}

.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
  background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.35) !important;
}

/* Modern Tabs */
button[data-baseweb="tab"],
button[data-baseweb="tab"] p {
  min-height: 48px;
  font-weight: 700 !important;
  font-size: 0.94rem !important;
  border-radius: 10px 10px 0 0 !important;
  padding: 8px 16px !important;
  color: #64748B !important;
}

button[data-baseweb="tab"] p {
  min-height: auto;
  padding: 0 !important;
}

button[data-baseweb="tab"][aria-selected="true"],
button[data-baseweb="tab"][aria-selected="true"] p {
  color: #2563EB !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
  border-bottom: 3px solid #2563EB !important;
}

/* ==========================================================================
   CUSTOM STEPPER 3 BƯỚC TRỰC QUAN
   ========================================================================== */
.rw-stepper-box {
  background: #FFFFFF;
  border: 1px solid var(--rw-line);
  border-radius: 18px;
  padding: 20px 24px;
  margin: 16px 0 24px;
  box-shadow: var(--rw-shadow-sm);
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
  box-shadow: 0 0 0 5px rgba(16, 185, 129, 0.15);
}

.rw-step-node.active .rw-step-circle {
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  color: #FFFFFF;
  box-shadow: 0 0 0 6px rgba(37, 99, 235, 0.2);
  transform: scale(1.08);
}

.rw-step-node.pending .rw-step-circle {
  background: #F1F5F9;
  border: 2px solid #CBD5E1;
  color: #94A3B8;
}

.rw-step-label {
  margin-top: 10px;
  font-size: 0.85rem;
  font-weight: 700;
  color: #64748B;
  transition: color 0.2s ease;
}

.rw-step-node.active .rw-step-label {
  color: #2563EB;
}

.rw-step-node.completed .rw-step-label {
  color: #10B981;
}

.rw-step-line {
  flex: 1;
  height: 4px;
  background: #E2E8F0;
  margin: -24px 12px 0;
  position: relative;
  z-index: 1;
  border-radius: 2px;
}

.rw-step-line.completed-line {
  background: linear-gradient(90deg, #10B981 0%, #2563EB 100%);
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

.rw-queue-card {
  background: #FFFFFF;
  border: 1px solid var(--rw-line);
  border-radius: 16px;
  padding: 16px;
  box-shadow: var(--rw-shadow-sm);
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.rw-queue-card:hover {
  transform: translateY(-4px);
  border-color: #93C5FD;
  box-shadow: 0 12px 28px rgba(37, 99, 235, 0.1);
}

.rw-queue-card.selected {
  border: 2px solid #2563EB;
  background: #F8FAFF;
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.16);
}

/* Badges with Soft Glow */
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
  background: #FEF2F2;
  color: #DC2626;
  border: 1px solid #FECACA;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.15);
}

.rw-badge-warning {
  background: #FFFBEB;
  color: #D97706;
  border: 1px solid #FDE68A;
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.15);
}

.rw-badge-success {
  background: #ECFDF5;
  color: #059669;
  border: 1px solid #A7F3D0;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.15);
}

/* Defect Semantic Badges from Figma Design System */
.rw-badge-d40 {
  background: #FEF2F2;
  color: #DC2626;
  border: 1px solid #FECACA;
  font-weight: 700;
}

.rw-badge-d20 {
  background: #FFFBEB;
  color: #D97706;
  border: 1px solid #FDE68A;
  font-weight: 700;
}

.rw-badge-d10 {
  background: #FEFCE8;
  color: #CA8A04;
  border: 1px solid #FEF08A;
  font-weight: 700;
}

.rw-badge-d00 {
  background: #ECFDF5;
  color: #059669;
  border: 1px solid #A7F3D0;
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

/* Existing Hero & Layout preservation with Tech Coordinate Grid */
.rw-hero{position:relative;overflow:hidden;background:radial-gradient(circle at 86% 18%, rgba(56, 189, 248, 0.25), transparent 46%), radial-gradient(circle at 14% 90%, rgba(37, 99, 235, 0.35), transparent 45%), linear-gradient(122deg, #071224 0%, #0F2952 52%, #1D4ED8 100%);
 border:1px solid rgba(255,255,255,.15);border-radius:24px;min-height:310px;padding:clamp(24px,4vw,46px);box-shadow:0 22px 54px rgba(10,25,47,.22);color:white;margin-bottom:22px}
.rw-hero::before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.04) 1px, transparent 1px);background-size:32px 32px;pointer-events:none}
.rw-hero-grid{position:relative;z-index:1;display:grid;grid-template-columns:1.18fr .82fr;align-items:center;gap:32px}
.rw-kicker{display:inline-flex;align-items:center;gap:8px;font-size:.74rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
 background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.26);border-radius:999px;padding:6px 14px;margin-bottom:14px;color:#E0F2FE;backdrop-filter:blur(6px)}
.rw-kicker-dot{width:8px;height:8px;border-radius:50%;background:#10B981;box-shadow:0 0 0 4px rgba(16,185,129,.25);display:inline-block}
.rw-hero h1{font-family:var(--rw-font) !important;color:white !important;font-size:clamp(1.75rem,3.2vw,2.55rem) !important;font-weight:800 !important;line-height:1.22 !important;letter-spacing:-0.02em !important;margin:0 0 14px}
.rw-hero .rw-lead{color:#DBEAFE;font-size:clamp(.95rem,1.45vw,1.04rem);line-height:1.7;max-width:560px;margin:0}
.rw-hero-visual{position:relative;background:rgba(10, 25, 47, 0.55);border:1px solid rgba(255,255,255,.22);
 border-radius:20px;padding:20px;backdrop-filter:blur(14px);box-shadow:0 16px 36px rgba(0,0,0,.28)}
.rw-visual-head{display:flex;align-items:center;justify-content:space-between;font-size:.82rem;font-weight:700;color:white;margin-bottom:14px}
.rw-visual-dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:#10B981;margin-right:6px;box-shadow:0 0 0 4px rgba(16,185,129,.22)}
.rw-visual-road{height:108px;position:relative;border-radius:14px;background:linear-gradient(137deg,#1E293B,#334155);border:1px solid rgba(255,255,255,.12);overflow:hidden}
.rw-visual-road:after{content:"";position:absolute;left:24%;top:-35px;width:52%;height:190px;transform:rotate(23deg);background:#1E293B;border-left:4px solid #E2E8F0;border-right:4px solid #E2E8F0}
.rw-road-line{position:absolute;left:49%;top:-35px;width:4px;height:190px;transform:rotate(23deg);z-index:1;background:repeating-linear-gradient(to bottom,#FBBF24 0 15px,transparent 15px 31px)}
.rw-road-pin{position:absolute;z-index:2;left:53%;top:28px;background:rgba(239,68,68,.2);border:2px solid #EF4444;width:36px;height:28px;border-radius:6px;box-shadow:0 0 16px rgba(239,68,68,.45)}
.rw-road-pin::after{content:"D40";position:absolute;top:-16px;left:-2px;background:#EF4444;color:#fff;font-size:9px;font-weight:800;padding:1px 4px;border-radius:3px}
.rw-visual-flow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:14px}
.rw-visual-flow span{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.14);border-radius:9px;text-align:center;color:#F8FAFC;font-size:.72rem;padding:8px 4px;font-weight:700}

.rw-section{margin-top:34px;margin-bottom:16px}
.rw-section .rw-overline{display:block;color:#2563EB;font-weight:800;text-transform:uppercase;letter-spacing:.08em;font-size:.75rem;margin-bottom:6px}
.rw-section h2{font-size:clamp(1.35rem,2.3vw,1.85rem);margin:0 0 8px}
.rw-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.rw-card{border:1px solid var(--rw-line);border-radius:18px;background:#fff;padding:24px;box-shadow:var(--rw-shadow-sm);transition:all .2s ease}
.rw-card:hover{transform:translateY(-3px);box-shadow:var(--rw-shadow-md)}
.rw-card-icon{display:flex;align-items:center;justify-content:center;width:48px;height:48px;border-radius:14px;background:#EFF6FF;color:#2563EB;font-size:1.4rem;margin-bottom:16px}
.rw-card h3{font-size:1.08rem;margin:0 0 8px}
.rw-card p{font-size:.88rem;color:#64748B;margin:0}

/* 4-Class AI Recognition Showcase Grid */
.rw-defect-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:14px 0 8px}
.rw-defect-card{background:#FFFFFF;border:1px solid var(--rw-line);border-radius:16px;padding:18px;box-shadow:var(--rw-shadow-sm);transition:all .22s cubic-bezier(0.16,1,0.3,1);position:relative;overflow:hidden}
.rw-defect-card:hover{transform:translateY(-3px);box-shadow:var(--rw-shadow-md);border-color:#CBD5E1}
.rw-defect-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
.rw-defect-code{font-size:.78rem;font-weight:800;padding:4px 10px;border-radius:999px;letter-spacing:.03em}
.rw-defect-weight{font-size:.74rem;font-weight:700;color:#64748B;font-variant-numeric:tabular-nums}
.rw-defect-card h4{font-size:1rem !important;margin:0 0 6px !important;color:#0F172A !important}
.rw-defect-card p{font-size:.82rem;color:#64748B;margin:0;line-height:1.45}

/* Officer Queue Case Summary Banner */
.rw-case-banner{background:#FFFFFF;border:1px solid var(--rw-line);border-left:4px solid #2563EB;border-radius:14px;padding:14px 18px;margin:10px 0 16px;box-shadow:var(--rw-shadow-sm);display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px}
.rw-case-title{font-size:1.02rem;font-weight:700;color:#0F172A;margin:0}
.rw-case-meta{font-size:.82rem;color:#475569;margin-top:3px}

.rw-overview{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.rw-kpi{background:#FFFFFF;border:1px solid var(--rw-line);padding:22px;border-radius:18px;box-shadow:var(--rw-shadow-sm);transition:all .2s ease}
.rw-kpi:hover{transform:translateY(-2px);box-shadow:var(--rw-shadow-md)}
.rw-kpi small{display:block;color:#64748B;margin-bottom:8px;font-size:.82rem;font-weight:600}
.rw-kpi strong{display:block;color:#0F172A;font-size:clamp(1.5rem,2.5vw,2.1rem);line-height:1.2;font-weight:800}
.rw-kpi em{display:block;font-size:.76rem;font-style:normal;color:#94A3B8;margin-top:6px}

.rw-page-intro{position:relative;overflow:hidden;background:radial-gradient(circle at 86% 20%, rgba(56, 189, 248, 0.24), transparent 45%), linear-gradient(118deg,#071224 0%,#0F2952 52%,#1D4ED8 100%);padding:clamp(22px,3vw,32px) clamp(24px,3.5vw,36px);border:1px solid rgba(255,255,255,.16);border-radius:22px;margin-bottom:22px;box-shadow:0 16px 40px rgba(10,25,47,.18);color:#FFFFFF}
.rw-page-intro::before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px);background-size:28px 28px;pointer-events:none}
.rw-page-intro .rw-overline{position:relative;display:inline-block;font-size:.74rem;color:#E0F2FE;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.26);border-radius:999px;padding:5px 13px;letter-spacing:.08em;font-weight:700;text-transform:uppercase;margin-bottom:10px}
.rw-page-intro h1{position:relative;font-family:var(--rw-font) !important;color:#FFFFFF !important;font-size:clamp(1.5rem,2.7vw,2.15rem);font-weight:800 !important;letter-spacing:-0.02em !important;line-height:1.24 !important;margin:4px 0 8px}
.rw-page-intro p{position:relative;color:#DBEAFE !important;margin:0;font-size:.95rem;line-height:1.6;max-width:760px}

.rw-hint{background:#EFF6FF;border-left:4px solid #2563EB;padding:14px 18px;border-radius:0 12px 12px 0;font-size:.88rem;color:#1E40AF;margin-bottom:18px}
.rw-empty{background:#F8FAFC;padding:24px;border:2px dashed #CBD5E1;border-radius:16px;color:#475569;text-align:center}
.rw-preview-banner{background:linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);border:1px solid #3B82F6;color:#FFFFFF;padding:12px 20px;border-radius:14px;font-size:.93rem;font-weight:600;letter-spacing:.02em;margin:16px 0 12px;display:flex;align-items:center;gap:10px;box-shadow:0 4px 16px rgba(15, 23, 42, 0.15)}

/* CTA Page Links & Two-Column Panels (Home / Submit / Auth) */
[data-testid="stPageLink-NavLink"]{
  display:flex !important;align-items:center;justify-content:center;min-height:50px;padding:10px 18px !important;
  border-radius:14px !important;border:1px solid #BFDBFE !important;
  background:linear-gradient(180deg,#FFFFFF 0%,#EFF6FF 100%) !important;
  color:#1D4ED8 !important;font-weight:700 !important;box-shadow:var(--rw-shadow-sm);
  transition:all .2s cubic-bezier(0.16,1,0.3,1) !important;text-decoration:none !important;
}
[data-testid="stPageLink-NavLink"]:hover{
  transform:translateY(-2px);background:linear-gradient(135deg,#2563EB 0%,#1D4ED8 100%) !important;
  color:#FFFFFF !important;border-color:#1D4ED8 !important;box-shadow:0 8px 22px rgba(37,99,235,.28) !important;
}
[data-testid="stPageLink-NavLink"]:hover *{color:#FFFFFF !important;}

.rw-two-col{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:14px}
.rw-white-panel{background:#FFFFFF;border:1px solid var(--rw-line);border-radius:18px;padding:24px;box-shadow:var(--rw-shadow-sm);transition:all .2s ease}
.rw-white-panel:hover{transform:translateY(-2px);box-shadow:var(--rw-shadow-md);border-color:#CBD5E1}
.rw-panel-title{display:inline-block;font-size:.74rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#2563EB;background:#EFF6FF;padding:4px 10px;border-radius:999px;margin-bottom:10px}
.rw-white-panel h3{margin:4px 0 8px;font-size:1.12rem}
.rw-white-panel p{margin:0;color:#64748B;font-size:.9rem}
.rw-footnote{margin-top:22px;padding:14px 18px;border-radius:14px;background:#F1F5F9;border:1px solid #E2E8F0;color:#475569;font-size:.84rem;text-align:center}

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
    background: rgba(255, 255, 255, 0.96) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    border-top: 1px solid #E2E8F0 !important;
    padding: 6px 8px calc(6px + env(safe-area-inset-bottom)) 8px !important;
    box-shadow: 0 -6px 24px rgba(15, 23, 42, 0.08) !important;
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
    gap: 2px !important;
    min-height: 48px !important;
    padding: 5px 2px !important;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    border-radius: 10px !important;
    font-size: 0.72rem !important;
    color: #475569 !important;
  }
  .st-key-rw_mobile_dock [data-testid="stPageLink-NavLink"]:hover {
    transform: none !important;
    background: #EFF6FF !important;
    color: #2563EB !important;
    box-shadow: none !important;
  }
  .st-key-rw_mobile_dock [data-testid="stPageLink-NavLink"]:hover * {
    color: #2563EB !important;
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

def apply():
    st.markdown(CSS, unsafe_allow_html=True)
