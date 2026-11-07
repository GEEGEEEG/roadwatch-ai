"""Giao diện RoadWatch: thang chữ, khoảng cách bội số 8px, tương phản đạt chuẩn, một điểm nhấn mỗi trang."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&display=swap');
:root{
  --ink:#0F172A; --muted:#475569; --line:#E2E8F0; --soft:#F1F5F9; --field:#64748B;
  --brand:#2563EB; --brand-ink:#1D4ED8; --paint:#F5B700;
  --s1:8px; --s2:16px; --s3:24px; --s4:32px; --s5:48px;
  --t-sm:.875rem; --t-base:1rem; --t-lg:1.125rem; --t-h3:1.25rem; --t-h2:1.75rem;
  --t-h1:clamp(2rem,4.6vw,3rem);
}
html, body, [class*="css"], .stApp { font-family:'Be Vietnam Pro', system-ui, -apple-system, 'Segoe UI', sans-serif; color:var(--ink); }
.stApp { background:#F8FAFC; font-size:var(--t-base); line-height:1.65; }
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:1120px; padding-top:var(--s5); padding-bottom:var(--s5); }
[data-testid="stVerticalBlock"] { gap:var(--s2); }

/* Chữ: 14 / 16 / 18 / 20 / 28 / 32–48 */
h1,h2,h3,h4 { color:var(--ink); line-height:1.2; letter-spacing:-.02em; font-weight:700; }
h1 { font-size:var(--t-h1); } h2 { font-size:var(--t-h2); } h3 { font-size:var(--t-h3); font-weight:600; }
[data-testid="stCaptionContainer"], .stCaption, small { font-size:var(--t-sm) !important; color:var(--muted) !important; line-height:1.6; }
label, [data-testid="stWidgetLabel"] p { font-weight:600; font-size:var(--t-sm); color:var(--ink); }
:focus-visible { outline:3px solid var(--paint) !important; outline-offset:2px; }

/* Sidebar */
section[data-testid="stSidebar"] { background:#fff; border-right:1px solid var(--line); }
[data-testid="stSidebarHeader"]::before { content:"🛣️  RoadWatch AI"; font-weight:700; font-size:var(--t-lg); margin-left:var(--s1); flex:1; }
[data-testid="stNavSectionHeader"] { font-size:var(--t-sm); letter-spacing:0; color:var(--muted); font-weight:600; }
[data-testid="stSidebarNav"] a { border-radius:8px; margin:2px 6px; min-height:40px; }
[data-testid="stSidebarNav"] a[aria-current="page"] { background:#EFF6FF; color:var(--brand-ink); font-weight:600; }
section[data-testid="stSidebar"] [data-testid="stAlert"] { padding:var(--s1) var(--s2); font-size:var(--t-sm); }

/* Khung phẳng: kẻ viền mảnh, không đổ bóng (bóng chỉ dành cho banner) */
[data-testid="stMetric"], [data-testid="stForm"], [data-testid="stExpander"] { background:#fff; border:1px solid var(--line) !important; border-radius:12px; box-shadow:none; }
[data-testid="stMetric"] { padding:var(--s2); }
[data-testid="stMetricLabel"] { color:var(--muted); font-weight:500; font-size:var(--t-sm); }
[data-testid="stMetricValue"] { font-weight:700; }
[data-testid="stForm"] { padding:var(--s3); }
[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:8px; overflow:hidden; }
[data-testid="stAlert"] { border-radius:8px; }
button[data-baseweb="tab"] { min-height:48px; font-weight:600; padding:0 var(--s2); }
iframe[title*="folium"], iframe[title*="streamlit_folium"] { border-radius:12px; }

/* Ô nhập và nút: cao tối thiểu 48px, viền đủ đậm để thấy ranh giới */
[data-baseweb="input"], [data-baseweb="select"] > div { min-height:48px; }
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div { border:1.5px solid var(--field) !important; border-radius:8px !important; background:#fff; }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within { border-color:var(--ink) !important; }
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button { border-radius:8px; font-weight:600; min-height:48px; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { background:var(--brand); border-color:var(--brand); }
[data-testid="stFileUploaderDropzone"] { background:#fff; border:2px dashed var(--field); border-radius:12px; min-height:96px; }
[data-testid="stFileUploaderDropzone"]:hover { border-color:var(--brand); }
[data-testid="stCameraInput"] > div { border-radius:12px; overflow:hidden; }

/* Liên kết trang -> nút. Nút chính đặc, nút phụ viền */
[data-testid="stPageLink"] a, a[data-testid="stPageLink-NavLink"] { justify-content:center; min-height:48px; padding:0 var(--s3); border-radius:8px; font-weight:600; background:var(--brand); }
[data-testid="stPageLink"] a:hover { filter:brightness(1.08); }
[data-testid="stPageLink"] a p, [data-testid="stPageLink"] a span { color:#fff !important; font-weight:600; }
[data-testid="stColumn"]:nth-child(2) [data-testid="stPageLink"] a { background:transparent; border:1.5px solid var(--ink); }
[data-testid="stColumn"]:nth-child(2) [data-testid="stPageLink"] a p, [data-testid="stColumn"]:nth-child(2) [data-testid="stPageLink"] a span { color:var(--ink) !important; }

/* Trang chủ: banner là điểm nhấn duy nhất */
.rw-hero { color:#fff; border-radius:16px; padding:clamp(32px,5vw,48px); margin-bottom:var(--s3); box-shadow:0 20px 40px -24px rgba(29,78,216,.55);
  background:linear-gradient(135deg,#1E3A8A 0%,#1D4ED8 60%,#2563EB 100%); }
.rw-hero h1 { color:#fff; margin:0 0 var(--s2); }
.rw-hero p { color:#DBEAFE; margin:0; font-size:var(--t-lg); max-width:60ch; }
.rw-pill { display:inline-block; background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.35); padding:4px 12px; border-radius:999px; font-size:var(--t-sm); font-weight:600; margin-bottom:var(--s2); }
.rw-chips { display:flex; flex-wrap:wrap; gap:var(--s1); margin-top:var(--s3); }
.rw-chips span { background:rgba(255,255,255,.14); padding:4px 12px; border-radius:999px; font-size:var(--t-sm); }
.rw-steps { display:grid; grid-template-columns:repeat(3,1fr); gap:var(--s3); margin:var(--s3) 0; }
.rw-step { background:#fff; border:1px solid var(--line); border-top:4px solid var(--brand); border-radius:12px; padding:var(--s3); }
.rw-step b { display:block; margin:var(--s1) 0 4px; font-size:var(--t-lg); }
.rw-step span { color:var(--muted); font-size:var(--t-base); }
.rw-ico { font-size:1.5rem; display:block; }
.rw-num { display:inline-flex; width:28px; height:28px; border-radius:50%; background:#DBEAFE; color:var(--brand-ink); font-weight:700; align-items:center; justify-content:center; }
.rw-stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:var(--s2); margin:var(--s1) 0 var(--s3); }
.rw-stat { background:#fff; border:1px solid var(--line); border-top:4px solid var(--c); border-radius:12px; padding:var(--s2); }
.rw-stat small { display:block; color:var(--muted); font-weight:500; }
.rw-stat strong { font-size:2rem; font-weight:700; line-height:1.2; }
.rw-empty { background:#EFF6FF; border:1px dashed #93C5FD; color:#1E3A8A; border-radius:8px; padding:var(--s2); margin-bottom:var(--s2); }
.rw-badge { display:inline-block; padding:2px 10px; border-radius:999px; font-size:var(--t-sm); font-weight:600; }
.rw-high { background:#FEE2E2; color:#B91C1C; } .rw-mid { background:#FEF3C7; color:#92400E; } .rw-low { background:#DCFCE7; color:#166534; }

@media (max-width:900px){ .rw-stats{ grid-template-columns:repeat(2,1fr); } }
@media (max-width:720px){ .block-container{ padding:var(--s2) var(--s2) var(--s5); } .rw-steps{ grid-template-columns:1fr; } }
@media (prefers-reduced-motion:reduce){ *{ transition:none !important; } }
</style>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
