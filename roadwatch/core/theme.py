"""Giao diện sáng, sạch, dùng tốt ngoài trời: một màu nhấn, thẻ bo góc, bóng nhẹ."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif; }
.block-container { max-width: 1080px; padding-top: 2.2rem; padding-bottom: 3rem; }
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
</style>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
