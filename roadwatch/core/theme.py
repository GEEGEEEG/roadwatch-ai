"""Giao diện sáng, sạch, dùng tốt ngoài trời: một màu nhấn, thẻ bo góc, bóng nhẹ."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif; }
.block-container { max-width: 1180px; padding-top: 3.4rem; padding-bottom: 3rem; }
h1, h2, h3 { font-weight: 700; letter-spacing: -0.02em; color: #0F172A; }
h1 { font-size: 2rem; } h2 { font-size: 1.5rem; }
[data-testid="stCaptionContainer"], .stCaption { color: #475569; }

/* Sidebar */
section[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E2E8F0; }
[data-testid="stSidebarNav"] a { border-radius: 10px; margin: 1px 6px; }
[data-testid="stSidebarNav"] a[aria-current="page"] { background: #EFF6FF; color: #1D4ED8; font-weight: 600; }

/* Thẻ số liệu */
[data-testid="stMetric"] { background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px;
  padding: 14px 16px; box-shadow: 0 1px 2px rgba(15,23,42,.05); }
[data-testid="stMetricLabel"] { color: #475569; font-weight: 500; }
[data-testid="stMetricValue"] { font-weight: 700; }

/* Form, khung mở rộng, tab */
[data-testid="stForm"], [data-testid="stExpander"] { background: #FFF; border: 1px solid #E2E8F0 !important;
  border-radius: 16px; box-shadow: 0 1px 2px rgba(15,23,42,.04); }
[data-testid="stForm"] { padding: 1.2rem; }
button[data-baseweb="tab"] { font-weight: 600; padding: 10px 16px; }

/* Khung tải ảnh */
[data-testid="stFileUploaderDropzone"] { background: #EFF6FF; border: 2px dashed #93C5FD; border-radius: 16px; }
[data-testid="stFileUploaderDropzone"]:hover { border-color: #2563EB; }
[data-testid="stCameraInput"] > div { border-radius: 16px; overflow: hidden; }

/* Nút và ô nhập */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
  border-radius: 10px; font-weight: 600; min-height: 2.75rem; }
.stFormSubmitButton > button[kind="primary"], .stButton > button[kind="primary"] { box-shadow: 0 2px 6px rgba(37,99,235,.25); }
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div { border-radius: 10px !important; }
[data-testid="stAlert"] { border-radius: 12px; }
[data-testid="stDataFrame"] { border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden; }
iframe[title*="folium"], iframe[title*="streamlit_folium"] { border-radius: 14px; }

/* Hero và thẻ bước (trang chủ) */
.rw-hero { background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 55%, #38BDF8 100%); color: #fff;
  border-radius: 20px; padding: 2.2rem 2rem; margin-bottom: 1.2rem; }
.rw-hero h1 { color: #fff; margin: 0 0 .4rem; font-size: 2.1rem; }
.rw-hero p { color: #E0F2FE; margin: 0; font-size: 1.05rem; max-width: 640px; }
.rw-steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin: 1rem 0 1.4rem; }
.rw-step { background: #FFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 1.1rem 1.2rem; }
.rw-step b { display: block; margin: .35rem 0 .15rem; color: #0F172A; }
.rw-step span { color: #475569; font-size: .93rem; }
.rw-num { display: inline-flex; width: 28px; height: 28px; border-radius: 50%; background: #DBEAFE;
  color: #1D4ED8; font-weight: 700; align-items: center; justify-content: center; }
.rw-badge { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: .8rem; font-weight: 600; }
.rw-high { background: #FEE2E2; color: #B91C1C; } .rw-mid { background: #FEF3C7; color: #B45309; }
.rw-low { background: #DCFCE7; color: #15803D; }

@media (max-width: 720px) {
  .block-container { padding: 1rem .9rem 2.5rem; }
  .rw-steps { grid-template-columns: 1fr; }
  .rw-hero { padding: 1.5rem 1.2rem; } .rw-hero h1 { font-size: 1.6rem; }
}

/* ===== Nâng cấp v2 ===== */
.stApp { background: radial-gradient(1200px 400px at 85% -10%, #E0F2FE 0%, rgba(248,250,252,0) 60%), #F8FAFC; }
[data-testid="stHeader"] { background: transparent; }
/* Thương hiệu trong sidebar */
[data-testid="stSidebarHeader"]::before { content: "🛣️  RoadWatch AI"; font-weight: 700; font-size: 1.1rem;
  color: #0F172A; letter-spacing: -0.01em; margin-left: 8px; flex: 1; }
[data-testid="stNavSectionHeader"] { text-transform: uppercase; font-size: .7rem; letter-spacing: .09em; color: #64748B; font-weight: 600; }
section[data-testid="stSidebar"] [data-testid="stAlert"] { padding: .45rem .8rem; font-size: .9rem; }
/* Liên kết trang -> nút CTA */
[data-testid="stPageLink"] a, a[data-testid="stPageLink-NavLink"] { justify-content: center; padding: .85rem 1rem;
  border-radius: 12px; font-weight: 600; background: #2563EB; color: #fff; box-shadow: 0 4px 12px rgba(37,99,235,.28);
  transition: transform .12s ease, box-shadow .12s ease; }
[data-testid="stPageLink"] a:hover { transform: translateY(-1px); box-shadow: 0 8px 18px rgba(37,99,235,.32); }
[data-testid="stPageLink"] a p, [data-testid="stPageLink"] a span { color: #fff !important; font-weight: 600; }
[data-testid="stColumn"]:nth-child(2) [data-testid="stPageLink"] a { background: #fff; border: 1px solid #BFDBFE; box-shadow: none; }
[data-testid="stColumn"]:nth-child(2) [data-testid="stPageLink"] a p, [data-testid="stColumn"]:nth-child(2) [data-testid="stPageLink"] a span { color: #1D4ED8 !important; }
/* Hero v2 */
.rw-hero { position: relative; overflow: hidden; padding: 2.6rem 2.2rem; box-shadow: 0 18px 40px rgba(37,99,235,.22);
  background: radial-gradient(500px 220px at 90% 0%, rgba(255,255,255,.22), rgba(255,255,255,0) 70%),
              linear-gradient(135deg, #1E40AF 0%, #2563EB 55%, #38BDF8 100%); }
.rw-pill { display: inline-block; background: rgba(255,255,255,.18); border: 1px solid rgba(255,255,255,.35);
  padding: 3px 12px; border-radius: 999px; font-size: .8rem; font-weight: 600; margin-bottom: .9rem; }
.rw-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 1.1rem; }
.rw-chips span { background: rgba(255,255,255,.16); padding: 4px 12px; border-radius: 999px; font-size: .85rem; }
/* Thẻ bước */
.rw-step { transition: transform .15s ease, box-shadow .15s ease; box-shadow: 0 1px 2px rgba(15,23,42,.04); }
.rw-step:hover { transform: translateY(-3px); box-shadow: 0 10px 24px rgba(15,23,42,.08); }
.rw-ico { font-size: 1.6rem; display: block; margin-bottom: .2rem; }
/* Thẻ trạng thái */
.rw-stats { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin: .6rem 0 1.2rem; }
.rw-stat { background: #fff; border: 1px solid #E2E8F0; border-radius: 16px; padding: 1rem 1.1rem;
  border-top: 4px solid var(--c); box-shadow: 0 1px 2px rgba(15,23,42,.04); }
.rw-stat small { color: #475569; font-weight: 500; display: block; }
.rw-stat strong { font-size: 2rem; font-weight: 700; color: #0F172A; line-height: 1.2; }
.rw-empty { background: #EFF6FF; border: 1px dashed #93C5FD; color: #1E3A8A; border-radius: 14px;
  padding: .9rem 1.1rem; margin-bottom: 1rem; }
@media (max-width: 900px) { .rw-stats { grid-template-columns: repeat(2, 1fr); } }
</style>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
