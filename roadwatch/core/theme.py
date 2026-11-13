"""RoadWatch AI - Modern Dashboard & Glassmorphism Design System v4.5."""
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
  --rw-border-glass: rgba(226, 232, 240, 0.85);
  --rw-bg: #F8FAFC;
  --rw-card-bg: #FFFFFF;
  --rw-shadow-sm: 0 2px 8px rgba(15, 23, 42, 0.04);
  --rw-shadow-md: 0 8px 24px rgba(15, 23, 42, 0.06);
  --rw-shadow-lg: 0 16px 40px rgba(15, 23, 42, 0.08);
  --rw-radius: 16px;
}

html, body, .stApp, [data-testid="stAppViewContainer"],
p, h1, h2, h3, h4, h5, h6, label, input, textarea, select, button,
.stMarkdown, [data-testid="stText"] {
  font-family: 'Plus Jakarta Sans', 'Be Vietnam Pro', 'Segoe UI', system-ui, sans-serif;
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

/* Main app container */
.stApp {
  background: var(--rw-bg);
  color: var(--rw-ink);
  font-size: 15px;
  line-height: 1.65;
}

[data-testid="stHeader"] {
  background: rgba(248, 250, 252, 0.82) !important;
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(226, 232, 240, 0.7);
}

.main .block-container, .block-container {
  max-width: 1200px;
  padding-top: 2.2rem;
  padding-bottom: 4rem;
}

/* Typography */
h1, h2, h3, h4 {
  font-weight: 800;
  color: var(--rw-navy);
  letter-spacing: -0.03em;
  line-height: 1.25;
}

h1 { font-size: clamp(1.85rem, 3.8vw, 2.6rem); }
h2 { font-size: clamp(1.4rem, 2.4vw, 1.95rem); }
h3 { font-size: 1.15rem; }

/* Modern Sidebar */
section[data-testid="stSidebar"] {
  background: #FFFFFF !important;
  border-right: 1px solid var(--rw-line);
  box-shadow: 2px 0 16px rgba(15, 23, 42, 0.02);
}

[data-testid="stSidebarNav"] a {
  display: flex !important;
  align-items: center !important;
  border-radius: 12px !important;
  min-height: 42px;
  margin: 2px 8px;
  padding: 8px 12px;
  gap: 12px;
  font-weight: 600;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

[data-testid="stSidebarNav"] a:hover {
  background: #EFF6FF !important;
  color: var(--rw-blue) !important;
  transform: translateX(3px);
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
  color: #FFFFFF !important;
  font-weight: 700;
  box-shadow: 0 6px 18px rgba(37, 99, 235, 0.28);
}

[data-testid="stSidebarNav"] a span {
  display: inline-flex !important;
  align-items: center !important;
  line-height: 1 !important;
}

[data-testid="stSidebarNav"] a span:first-child {
  font-size: 1.25rem !important;
  line-height: 1 !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  margin-top: 0 !important;
}

[data-testid="stSidebarNav"] a span:last-child {
  display: inline-flex !important;
  align-items: center !important;
  line-height: 1.3 !important;
}

[data-testid="stSidebarNav"] a[aria-current="page"] span {
  color: #FFFFFF !important;
}

[data-testid="stNavSectionHeader"] {
  color: #64748B !important;
  font-size: 0.76rem !important;
  font-weight: 800 !important;
  letter-spacing: 0.08em !important;
  text-transform: uppercase !important;
  padding: 10px 14px 4px !important;
}

.rw-sidebar-brand {
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 16px;
  background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
  padding: 16px;
  margin: 4px 6px 18px;
  box-shadow: var(--rw-shadow-sm);
}

.rw-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #0F172A;
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.rw-logo-mark {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 0.95rem;
  box-shadow: 0 6px 14px rgba(37, 99, 235, 0.3);
}

.rw-sidebar-sub {
  color: #64748B;
  font-size: 0.78rem;
  margin: 6px 0 0 50px;
}

.rw-sidebar-info {
  font-size: 0.8rem;
  color: var(--rw-sub);
  padding: 10px 14px;
  border-radius: 12px;
  background: #F1F5F9;
  margin: 4px 6px;
  border: 1px solid #E2E8F0;
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
  border-radius: var(--rw-radius) !important;
  background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%) !important;
  padding: 1.25rem !important;
  box-shadow: var(--rw-shadow-sm) !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

[data-testid="stMetric"]:hover {
  transform: translateY(-2px);
  box-shadow: var(--rw-shadow-md) !important;
  border-color: #CBD5E1 !important;
}

[data-testid="stMetricLabel"] {
  color: #64748B !important;
  font-size: 0.85rem !important;
  font-weight: 600 !important;
}

[data-testid="stMetricValue"] {
  font-weight: 800 !important;
  color: var(--rw-navy) !important;
  letter-spacing: -0.02em;
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
button[data-baseweb="tab"] {
  min-height: 50px;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  border-radius: 10px 10px 0 0 !important;
  padding: 10px 20px !important;
  color: #64748B !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
  color: #2563EB !important;
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
  max-width: 720px;
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

/* Micro-animations */
@keyframes pulseGlow {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.05); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.8; }
}

.rw-pulse {
  animation: pulseGlow 2s infinite ease-in-out;
}

/* Existing Hero & Layout preservation */
.rw-hero{position:relative;overflow:hidden;background:linear-gradient(118deg,#0A192F 0%,#133B7A 50%,#1D64D8 100%);
 border-radius:24px;min-height:330px;padding:clamp(24px,4.5vw,50px);box-shadow:0 20px 50px rgba(13,39,80,.2);color:white;margin-bottom:22px}
.rw-hero-grid{position:relative;display:grid;grid-template-columns:1.15fr .85fr;align-items:center;gap:32px}
.rw-kicker{display:inline-block;font-size:.76rem;font-weight:750;letter-spacing:.075em;text-transform:uppercase;
 background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.3);border-radius:999px;padding:6px 14px;margin-bottom:16px;color:#E6F1FF}
.rw-hero h1{color:white;font-size:clamp(2rem,4.2vw,3.2rem);line-height:1.15;letter-spacing:-.04em;margin:0 0 16px}
.rw-hero .rw-lead{color:#E2E8F0;font-size:clamp(.95rem,1.5vw,1.06rem);line-height:1.75;max-width:560px;margin:0}
.rw-hero-visual{position:relative;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.22);
 border-radius:20px;padding:22px;backdrop-filter:blur(10px);box-shadow:0 14px 34px rgba(0,0,0,.2)}
.rw-visual-head{display:flex;align-items:center;justify-content:space-between;font-size:.84rem;font-weight:700;color:white;margin-bottom:16px}
.rw-visual-dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:#10B981;margin-right:6px;box-shadow:0 0 0 4px rgba(16,185,129,.2)}
.rw-visual-road{height:100px;position:relative;border-radius:14px;background:linear-gradient(137deg,#CBD5E1,#94A3B8);overflow:hidden}
.rw-visual-road:after{content:"";position:absolute;left:24%;top:-35px;width:52%;height:180px;transform:rotate(23deg);background:#334155;border-left:5px solid #F8FAFC;border-right:5px solid #F8FAFC}
.rw-road-line{position:absolute;left:49%;top:-35px;width:4px;height:180px;transform:rotate(23deg);z-index:1;background:repeating-linear-gradient(to bottom,#FCD34D 0 15px,transparent 15px 31px)}
.rw-road-pin{position:absolute;z-index:2;left:55%;top:30px;background:#fff;border:4px solid #2563EB;width:26px;height:26px;border-radius:50%;box-shadow:0 4px 18px rgba(0,0,0,.25)}
.rw-visual-flow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:14px}
.rw-visual-flow span{background:rgba(255,255,255,.14);border-radius:9px;text-align:center;color:#F8FAFC;font-size:.7rem;padding:8px 4px;font-weight:700}

.rw-section{margin-top:40px;margin-bottom:18px}
.rw-section .rw-overline{display:block;color:#2563EB;font-weight:800;text-transform:uppercase;letter-spacing:.08em;font-size:.75rem;margin-bottom:6px}
.rw-section h2{font-size:clamp(1.35rem,2.3vw,1.85rem);margin:0 0 8px}
.rw-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.rw-card{border:1px solid var(--rw-line);border-radius:18px;background:#fff;padding:24px;box-shadow:var(--rw-shadow-sm);transition:all .2s ease}
.rw-card:hover{transform:translateY(-3px);box-shadow:var(--rw-shadow-md)}
.rw-card-icon{display:flex;align-items:center;justify-content:center;width:48px;height:48px;border-radius:14px;background:#EFF6FF;color:#2563EB;font-size:1.4rem;margin-bottom:16px}
.rw-card h3{font-size:1.08rem;margin:0 0 8px}
.rw-card p{font-size:.88rem;color:#64748B;margin:0}

.rw-overview{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.rw-kpi{background:#FFFFFF;border:1px solid var(--rw-line);padding:22px;border-radius:18px;box-shadow:var(--rw-shadow-sm);transition:all .2s ease}
.rw-kpi:hover{transform:translateY(-2px);box-shadow:var(--rw-shadow-md)}
.rw-kpi small{display:block;color:#64748B;margin-bottom:8px;font-size:.82rem;font-weight:600}
.rw-kpi strong{display:block;color:#0F172A;font-size:clamp(1.5rem,2.5vw,2.1rem);line-height:1.2;font-weight:800}
.rw-kpi em{display:block;font-size:.76rem;font-style:normal;color:#94A3B8;margin-top:6px}

.rw-page-intro{background:linear-gradient(135deg,#FFFFFF 0%,#F1F5F9 100%);padding:24px 28px;border:1px solid var(--rw-line);border-radius:18px;margin-bottom:20px;box-shadow:var(--rw-shadow-sm)}
.rw-page-intro .rw-overline{font-size:.72rem;color:#2563EB;letter-spacing:.1em;font-weight:800;text-transform:uppercase}
.rw-page-intro h1{font-size:clamp(1.5rem,3vw,2.1rem);margin:6px 0}
.rw-page-intro p{color:#64748B;margin:0;font-size:.92rem}

.rw-hint{background:#EFF6FF;border-left:4px solid #2563EB;padding:14px 18px;border-radius:0 12px 12px 0;font-size:.88rem;color:#1E40AF;margin-bottom:18px}
.rw-empty{background:#F8FAFC;padding:24px;border:2px dashed #CBD5E1;border-radius:16px;color:#475569;text-align:center}
.rw-preview-banner{background:linear-gradient(135deg,#1E40AF,#3B82F6);color:#fff;padding:10px 20px;border-radius:12px;font-size:.93rem;font-weight:600;letter-spacing:.03em;margin:16px 0 10px;display:flex;align-items:center;gap:8px}

@media(max-width:950px){.rw-hero-grid{grid-template-columns:1fr}.rw-overview{grid-template-columns:repeat(2,1fr)}}
@media(max-width:740px){
  .block-container{padding:1.2rem 1rem 3rem}
  .rw-hero{padding:24px;border-radius:18px}
  .rw-cards{grid-template-columns:1fr}
  .rw-overview{grid-template-columns:repeat(2,1fr)}
  .rw-stepper{flex-direction:column;gap:12px}
  .rw-step-line{display:none}
}
</style>
"""

def apply():
    st.markdown(CSS, unsafe_allow_html=True)
