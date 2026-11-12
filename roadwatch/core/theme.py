"""RoadWatch AI Pro | Design system v4: nền trắng, xanh navy/royal, typography 8px scale.
Các lớp HTML được render từ chuỗi cố định; dữ liệu người dùng luôn cần escape.
"""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
:root {
  color-scheme: light;
  --rw-navy:#0B1F42;--rw-ink:#14243B;--rw-sub:#53637B;
  --rw-blue:#2367E8;--rw-blue-dark:#1554CC;--rw-sky:#EAF3FF;
  --rw-line:#E1E9F3;--rw-bg:#FFFFFF;--rw-soft:#F7FAFF;
  --rw-shadow:0 14px 38px rgba(12,45,94,.065);
  --rw-radius:18px;
}
html,body,.stApp,[data-testid="stAppViewContainer"],
p, h1, h2, h3, h4, h5, h6, label, input, textarea, select, button,
.stMarkdown, [data-testid="stText"] {
  font-family:'Be Vietnam Pro','Segoe UI',system-ui,sans-serif;
}

/* Bảo vệ tuyệt đối Material Symbols và icon của Streamlit không bị đè font */
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
  word-wrap: normal !important;
  direction: ltr !important;
  -webkit-font-smoothing: antialiased !important;
}

/* Định dạng expander chuẩn để mũi tên và tiêu đề không dính vào nhau */
[data-testid="stExpander"] details summary {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  cursor: pointer !important;
}
[data-testid="stExpander"] details summary p {
  margin: 0 !important;
  display: inline-block !important;
}
.stApp{background:var(--rw-bg);color:var(--rw-ink);font-size:15px;line-height:1.65}
[data-testid="stHeader"]{background:rgba(255,255,255,.92)}
.main .block-container,.block-container{max-width:1180px;padding-top:2.6rem;padding-bottom:4rem}
[data-testid="stVerticalBlock"]{gap:.85rem}
h1,h2,h3,h4{font-weight:800;color:var(--rw-navy);letter-spacing:-.035em;line-height:1.25}
h1{font-size:clamp(1.9rem,4.2vw,2.8rem)}h2{font-size:clamp(1.45rem,2.6vw,2rem)}h3{font-size:1.14rem}
p{line-height:1.75;color:var(--rw-ink)}
[data-testid="stCaptionContainer"],.stCaption,small{color:var(--rw-sub)!important;font-size:.83rem!important;line-height:1.65}
:focus-visible{outline:3px solid #5EB2FF!important;outline-offset:3px!important}
/* Sidebar: nhận diện thương hiệu, phân nhóm bằng native navigation */
section[data-testid="stSidebar"]{background:#F9FBFF;border-right:1px solid var(--rw-line)}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"]{padding-top:.6rem}
[data-testid="stSidebarNav"] a{display:flex!important;align-items:center!important;border-radius:12px;min-height:42px;margin:2px 5px;padding:6px 12px;gap:10px}
[data-testid="stSidebarNav"] a:hover{background:#EBF3FF}
[data-testid="stSidebarNav"] a[aria-current="page"]{background:#DDEBFF;color:#144EA9;font-weight:750}
[data-testid="stSidebarNav"] a span{display:inline-flex!important;align-items:center!important;line-height:1!important}
[data-testid="stSidebarNav"] a span:first-child{font-size:1.15rem!important;line-height:1!important;margin-top:-2px!important}
[data-testid="stNavSectionHeader"]{color:#75859A;font-size:.75rem;font-weight:750;letter-spacing:.08em;text-transform:uppercase}
.rw-sidebar-brand{border:1px solid #DFEAF8;border-radius:16px;background:#fff;padding:15px;margin:3px 0 16px}
.rw-logo{display:flex;align-items:center;gap:10px;color:#133B7A;font-size:1rem;font-weight:800;letter-spacing:-.03em}
.rw-logo-mark{width:35px;height:35px;border-radius:11px;background:#165BD5;color:white;display:inline-flex;align-items:center;justify-content:center;box-shadow:0 7px 17px rgba(22,91,213,.22)}
.rw-sidebar-sub{color:#7788A1;font-size:.74rem;margin:4px 0 0 45px}
.rw-sidebar-info{font-size:.77rem;color:var(--rw-sub);padding:9px 11px;border-radius:11px;background:#EEF5FF}
/* Inputs, buttons and cards */
[data-testid="stForm"],[data-testid="stMetric"],[data-testid="stExpander"]{border:1px solid var(--rw-line)!important;border-radius:16px!important;background:#fff;box-shadow:0 4px 18px rgba(18,54,103,.032)}
[data-testid="stForm"]{padding:1.4rem}
[data-testid="stMetric"]{padding:1.15rem}
[data-testid="stMetricLabel"]{color:var(--rw-sub);font-size:.87rem}
[data-testid="stMetricValue"]{font-weight:800;color:var(--rw-navy)}
[data-testid="stDataFrame"]{border:1px solid var(--rw-line);border-radius:12px;overflow:hidden}
[data-testid="stAlert"]{border-radius:12px}
[data-testid="stWidgetLabel"] p, label{font-weight:650;font-size:.9rem;color:var(--rw-ink)}
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"]>div{border-radius:11px!important;min-height:45px}
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button,
.stLinkButton>a{min-height:46px;border-radius:12px!important;font-weight:700;transition:transform .16s ease,box-shadow .16s ease}
.stButton>button:hover,.stLinkButton>a:hover{transform:translateY(-1px)}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{background:var(--rw-blue);border-color:var(--rw-blue);color:white}
.stButton>button[kind="primary"]:hover,.stFormSubmitButton>button[kind="primary"]:hover{background:var(--rw-blue-dark)}
[data-testid="stFileUploaderDropzone"]{background:#F7FAFF;border:2px dashed #B7D0F2;border-radius:14px;padding:1.1rem}
[data-testid="stCameraInput"]{border-radius:14px;overflow:hidden}
button[data-baseweb="tab"]{min-height:48px;font-weight:700}
iframe[title*="folium"], iframe[title*="streamlit_folium"]{border-radius:16px}
/* CTA page_link for hero: acts like genuine keyboard-accessible navigation */
[data-testid="stPageLink"] a{display:flex;justify-content:center;align-items:center;text-decoration:none;
  min-height:53px;border-radius:12px;border:1px solid #C7D9F5;background:white;transition:.15s ease}
[data-testid="stPageLink"] a p,[data-testid="stPageLink"] a span{color:#1C4F9B;font-size:.95rem;font-weight:750}
[data-testid="stPageLink"] a:hover{background:#E7F1FF;border-color:#7BAAED;transform:translateY(-1px)}
/* Primary action above the fold: tương phản mạnh; nút bản đồ là secondary */
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"]) > [data-testid="column"]:first-child [data-testid="stPageLink"] a {
  background:var(--rw-blue);border-color:var(--rw-blue);box-shadow:0 8px 22px rgba(27,93,204,.16);
}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"]) > [data-testid="column"]:first-child [data-testid="stPageLink"] a p,
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"]) > [data-testid="column"]:first-child [data-testid="stPageLink"] a span{color:white!important}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"]) > [data-testid="column"]:first-child [data-testid="stPageLink"] a:hover{background:var(--rw-blue-dark)}
/* Hero: SEO semantic H1, một thông điệp lớn, thị giác bản đồ / quy trình */
.rw-hero{position:relative;overflow:hidden;background:linear-gradient(118deg,#0C2656,#1557BC 62%,#1D74EB);
 border-radius:25px;min-height:335px;padding:clamp(24px,4.5vw,52px);box-shadow:0 23px 55px rgba(18,84,173,.18);color:white;margin-bottom:22px}
.rw-hero:before{content:"";position:absolute;width:440px;height:440px;right:-180px;top:-220px;
 border:1px solid rgba(255,255,255,.21);border-radius:50%;box-shadow:0 0 0 55px rgba(255,255,255,.04),0 0 0 110px rgba(255,255,255,.03)}
.rw-hero-grid{position:relative;display:grid;grid-template-columns:1.14fr .86fr;align-items:center;gap:32px}
.rw-kicker{display:inline-block;font-size:.76rem;font-weight:750;letter-spacing:.075em;text-transform:uppercase;
 background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.29);border-radius:999px;padding:6px 13px;margin-bottom:17px;color:#E6F1FF}
.rw-hero h1{color:white;font-size:clamp(2rem,4.3vw,3.35rem);line-height:1.14;letter-spacing:-.05em;margin:0 0 18px}
.rw-hero .rw-lead{color:#DFECFF;font-size:clamp(.95rem,1.5vw,1.08rem);line-height:1.75;max-width:550px;margin:0}
.rw-hero-visual{position:relative;background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.22);
 border-radius:20px;padding:22px;backdrop-filter:blur(8px);box-shadow:0 14px 34px rgba(3,22,61,.15)}
.rw-visual-head{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:.83rem;font-weight:700;color:white;margin-bottom:16px}
.rw-visual-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#6BE1B3;margin-right:6px;box-shadow:0 0 0 4px rgba(107,225,179,.15)}
.rw-visual-road{height:100px;position:relative;border-radius:14px;background:linear-gradient(137deg,#DCEBFF,#B7D5FA);overflow:hidden}
.rw-visual-road:after{content:"";position:absolute;left:24%;top:-35px;width:52%;height:180px;transform:rotate(23deg);background:#5374A2;border-left:6px solid #F3F7FD;border-right:6px solid #F3F7FD}
.rw-road-line{position:absolute;left:49%;top:-35px;width:4px;height:180px;transform:rotate(23deg);z-index:1;
 background:repeating-linear-gradient(to bottom,#F6D66D 0 15px,transparent 15px 31px)}
.rw-road-pin{position:absolute;z-index:2;left:55%;top:30px;background:#fff;border:4px solid #2563EB;
 width:25px;height:25px;border-radius:50%;box-shadow:0 3px 18px rgba(0,0,0,.2)}
.rw-visual-flow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:14px}
.rw-visual-flow span{background:rgba(255,255,255,.14);border-radius:9px;text-align:center;color:#F4F9FF;font-size:.68rem;padding:8px 5px;font-weight:650}
.rw-cta-label{font-size:.78rem;font-weight:700;color:#6380A5;margin:12px 0 -2px}
.rw-section{margin-top:42px;margin-bottom:17px}
.rw-section .rw-overline{display:block;color:#2D6BE4;font-weight:800;text-transform:uppercase;letter-spacing:.08em;font-size:.73rem;margin-bottom:6px}
.rw-section h2{font-size:clamp(1.35rem,2.4vw,1.85rem);margin:0 0 8px}
.rw-section p{margin:0;color:#697991;max-width:75ch}
.rw-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}
.rw-card{border:1px solid var(--rw-line);border-radius:18px;background:#fff;padding:22px;
 box-shadow:0 6px 22px rgba(29,72,120,.035)}
.rw-card-icon{display:flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:13px;
 background:#EAF3FF;color:#1558C8;font-size:1.3rem;margin-bottom:14px}
.rw-card h3{font-size:1.05rem;margin:0 0 7px}
.rw-card p{font-size:.87rem;color:#64758D;margin:0}
.rw-overview{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px}
.rw-kpi{background:#F8FBFF;border:1px solid #E2EBF7;padding:20px;border-radius:16px}
.rw-kpi small{display:block;color:#637591;margin-bottom:8px;font-size:.78rem}
.rw-kpi strong{display:block;color:#0E3E89;font-size:clamp(1.45rem,2.4vw,2.05rem);line-height:1.3}
.rw-kpi em{display:block;font-size:.74rem;font-style:normal;color:#8A99AC;margin-top:4px}
.rw-two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.rw-white-panel{background:#fff;border:1px solid var(--rw-line);border-radius:18px;padding:22px}
.rw-panel-title{color:#134B9D;font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;font-weight:800}
.rw-white-panel h3{margin:8px 0 10px}
.rw-white-panel p,.rw-white-panel li{color:var(--rw-sub);font-size:.88rem}
.rw-white-panel ul{padding-left:20px;margin-bottom:0}
.rw-footnote{color:#708198;font-size:.78rem;border-top:1px solid #E6EDF6;margin-top:36px;padding-top:19px}
/* Page intros + workflow */
.rw-page-intro{background:linear-gradient(110deg,#F2F7FF,#FFFFFF);padding:24px 27px;border:1px solid #E2ECF8;
 border-radius:18px;margin-bottom:18px}
.rw-page-intro .rw-overline{font-size:.71rem;color:#276BE3;letter-spacing:.1em;font-weight:800;text-transform:uppercase}
.rw-page-intro h1{font-size:clamp(1.55rem,3.1vw,2.15rem);margin:7px 0}
.rw-page-intro p{color:#667993;margin:0;font-size:.91rem}
.rw-progress{display:flex;gap:9px;flex-wrap:wrap;margin:12px 0 16px}
.rw-progress span{border:1px solid #D9E7FA;border-radius:999px;padding:7px 12px;font-size:.77rem;
 color:#4F6D96;background:white;font-weight:700}
.rw-progress span.active{background:#E6F1FF;color:#164A97;border-color:#AFCBFA}
.rw-hint{background:#F1F7FF;border-left:4px solid #2775EB;padding:13px 16px;border-radius:0 12px 12px 0;
 font-size:.87rem;color:#2F557F}
.rw-empty{background:#F6FAFF;padding:22px;border:1px dashed #AFCBEF;border-radius:16px;color:#436A99}
.rw-badge{display:inline-block;padding:4px 10px;border-radius:999px;font-size:.78rem;font-weight:750}
.rw-high{background:#FDE8E8;color:#A71D2A}.rw-mid{background:#FFF0D2;color:#925A08}.rw-low{background:#E7F8ED;color:#11763C}
@media(max-width:950px){.rw-hero-grid{grid-template-columns:1fr}.rw-hero-visual{max-width:570px}.rw-overview{grid-template-columns:repeat(2,1fr)}}
@media(max-width:740px){
 .block-container{padding:1.15rem 1rem 3rem}.rw-hero{padding:23px;border-radius:18px;min-height:auto}
 .rw-hero h1{font-size:2.06rem}.rw-hero-visual{padding:15px}.rw-cards,.rw-two-col{grid-template-columns:1fr}
 .rw-overview{grid-template-columns:repeat(2,minmax(0,1fr))}.rw-kpi{padding:14px}
 .rw-card{padding:18px}.rw-page-intro{padding:19px 17px}
 [data-testid="stHorizontalBlock"]{flex-wrap:wrap}
 [data-testid="column"]{min-width:0!important}
}
@media(max-width:420px){.rw-overview{gap:9px}.rw-kpi strong{font-size:1.55rem}.rw-visual-flow span{font-size:.6rem}}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>
"""

def apply():
    st.markdown(CSS, unsafe_allow_html=True)
