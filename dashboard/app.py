import streamlit as st
from utils import sidebar, NAVY, PINK
st.set_page_config(page_title='SupeRR Selector | Pressure Performance', page_icon=None, layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
:root{--navy:#0B1F4B;--pink:#E5007D;--bg:#F3F5FA}
html,body,[class*="css"]{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--navy)}
.stApp{background:radial-gradient(ellipse at 92% 2%,rgba(229,0,125,.045),transparent 30%),var(--bg)}
.block-container{padding:1.45rem 2rem 3.2rem;max-width:1580px}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#fff 0%,#f8f9fc 100%);border-right:1px solid #e6eaf2}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3{font-size:1.02rem;letter-spacing:.01em}
.hero{position:relative;overflow:hidden;isolation:isolate;background:linear-gradient(118deg,#081638 0%,#0B1F4B 48%,#254e87 100%);color:white;border-radius:22px;padding:38px 42px;margin:4px 0 20px;box-shadow:0 16px 38px rgba(11,31,75,.18);animation:heroIn .7s cubic-bezier(.2,.8,.2,1) both}
.hero>*{position:relative;z-index:1}.hero:after{content:"";position:absolute;z-index:0;width:360px;height:360px;right:5%;top:-205px;border-radius:50%;background:radial-gradient(circle,rgba(229,0,125,.38) 0,rgba(229,0,125,.1) 40%,transparent 70%);animation:orbFloat 7s ease-in-out infinite alternate}
.hero:before{content:"";position:absolute;z-index:0;width:260px;height:260px;right:22%;bottom:-220px;border-radius:50%;border:1px solid rgba(255,255,255,.16);box-shadow:0 0 0 28px rgba(255,255,255,.025),0 0 0 58px rgba(255,255,255,.02)}
.hero-kicker{font-size:.72rem;text-transform:uppercase;letter-spacing:.2em;font-weight:750;color:#ffb7dc;margin-bottom:10px}
.hero h1{color:white;margin:0;font-size:clamp(2rem,4vw,3rem);letter-spacing:-.035em;line-height:1.07}.hero p{color:#e4eaf6;margin:12px 0 0;font-size:1.03rem;max-width:690px;line-height:1.6}
.pipeline{display:flex;gap:12px;margin:14px 0 22px}.step{position:relative;overflow:hidden;background:rgba(255,255,255,.94);border:1px solid #e5eaf3;border-radius:14px;padding:15px 18px;flex:1;font-weight:650;box-shadow:0 4px 14px rgba(11,31,75,.035);transition:transform .22s ease,box-shadow .22s ease,border-color .22s ease;animation:fadeUp .55s ease both}.step:nth-child(2){animation-delay:.08s}.step:nth-child(3){animation-delay:.16s}.step:hover{transform:translateY(-3px);box-shadow:0 10px 22px rgba(11,31,75,.09);border-color:rgba(229,0,125,.35)}.step b{display:inline-grid;place-items:center;width:27px;height:27px;border-radius:9px;color:white;background:var(--pink);margin-right:9px;font-size:.78rem}
.metric-card{position:relative;overflow:hidden;background:linear-gradient(145deg,#fff 0%,#fbfcff 100%);border:1px solid #e7ebf3;border-radius:16px;padding:17px 18px;box-shadow:0 5px 18px rgba(11,31,75,.055);min-height:108px;transition:transform .22s ease,box-shadow .22s ease;animation:fadeUp .55s ease both}.metric-card:after{content:"";position:absolute;left:0;top:0;width:3px;height:100%;background:linear-gradient(var(--pink),#ff8ec6)}.metric-card:hover{transform:translateY(-4px);box-shadow:0 13px 27px rgba(11,31,75,.11)}
.metric-label{font-size:.76rem;color:#697895;font-weight:700;letter-spacing:.045em;text-transform:uppercase}.metric-value{font-size:1.8rem;font-weight:800;letter-spacing:-.04em;color:#0B1F4B;margin-top:7px;line-height:1}.metric-sub{font-size:.72rem;color:#8791a6;margin-top:8px}
.foot{margin-top:30px;padding:14px 2px 0;border-top:1px solid #dfe5f0;color:#6d7890;font-size:.76rem}
.note{background:linear-gradient(110deg,#fff,#fff8fc);border:1px solid #f0d9e7;border-left:4px solid #E5007D;border-radius:12px;padding:15px 18px;color:#354566;box-shadow:0 4px 14px rgba(11,31,75,.035)}
.st-key-top_navigation{padding:8px 10px;margin:0 0 20px;background:rgba(255,255,255,.92);border:1px solid #e3e8f2;border-radius:14px;box-shadow:0 5px 18px rgba(11,31,75,.055);position:sticky;top:8px;z-index:999}
.st-key-top_navigation [data-testid="stPageLink"] a{display:flex;justify-content:center;align-items:center;min-height:38px;padding:7px 8px;border-radius:9px;color:#31466e;font-size:.82rem;font-weight:700;text-decoration:none;white-space:nowrap;transition:background .18s ease,color .18s ease,transform .18s ease}
.st-key-top_navigation [data-testid="stPageLink"] a:hover{background:#fce8f3;color:#b60064;transform:translateY(-1px)}
.st-key-top_navigation [data-testid="stPageLink"] a[aria-current="page"]{background:#0B1F4B;color:white}
@media(max-width:1050px){.st-key-top_navigation [data-testid="stPageLink"] a{font-size:.72rem;padding-inline:4px}.st-key-top_navigation{padding:6px 4px}}
@media(max-width:760px){.st-key-top_navigation{position:static;overflow-x:auto}.st-key-top_navigation [data-testid="stPageLink"] a{white-space:normal;line-height:1.1}}
[data-testid="stMetric"]{background:#fff;padding:14px;border:1px solid #e7ebf3;border-radius:14px;box-shadow:0 4px 14px rgba(11,31,75,.045)}
h1,h2,h3{color:#0B1F4B;letter-spacing:-.02em}h2{margin-top:.5rem}h3{font-weight:750}
div[data-testid="stVerticalBlockBorderWrapper"]{border:1px solid #e5eaf3!important;border-radius:14px!important;background:rgba(255,255,255,.93);box-shadow:0 3px 12px rgba(11,31,75,.035);transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease;animation:fadeUp .45s ease both}
div[data-testid="stVerticalBlockBorderWrapper"]:hover{transform:translateY(-2px);box-shadow:0 9px 22px rgba(11,31,75,.09);border-color:rgba(229,0,125,.28)!important}
.stButton>button{border:1px solid #e3e8f2;border-radius:10px;background:#fff;color:var(--navy);font-weight:700;transition:all .18s ease}
.stButton>button:hover{border-color:var(--pink);color:var(--pink);box-shadow:0 5px 14px rgba(229,0,125,.12);transform:translateY(-1px)}
button[role="tab"]{font-weight:700}
[data-testid="stExpander"]{background:white;border:1px solid #e7ebf3;border-radius:12px;overflow:hidden}
@keyframes heroIn{from{opacity:0;transform:translateY(12px) scale(.99)}to{opacity:1;transform:translateY(0) scale(1)}}
@keyframes fadeUp{from{opacity:0;transform:translateY(9px)}to{opacity:1;transform:translateY(0)}}
@keyframes orbFloat{from{transform:translate3d(0,0,0) scale(.92)}to{transform:translate3d(-18px,22px,0) scale(1.08)}}
@media(max-width:900px){.block-container{padding:1rem 1rem 2rem}.hero{padding:28px 25px}.pipeline{gap:8px}.step{padding:12px 10px;font-size:.87rem}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation-duration:.01ms!important;animation-iteration-count:1!important;scroll-behavior:auto!important;transition-duration:.01ms!important}}
</style>''',unsafe_allow_html=True)
filters=sidebar()
pages=[st.Page('pages/01_Overview.py',title='Overview',default=True),st.Page('pages/02_What_is_Pressure.py',title='Pressure'),st.Page('pages/03_Match_Explorer.py',title='Matches'),st.Page('pages/04_Batter_Deep_Dive.py',title='Batters'),st.Page('pages/05_Bowler_Deep_Dive.py',title='Bowlers'),st.Page('pages/06_Final_Top_10.py',title='Final 10'),st.Page('pages/07_Reliability.py',title='Reliability'),st.Page('pages/08_Methodology.py',title='Methodology')]
nav=st.navigation(pages,position='hidden')
st.session_state['global_filters']=filters
with st.container(key='top_navigation'):
    nav_cols=st.columns(len(pages),gap='small')
    for col,page in zip(nav_cols,pages):
        with col:
            st.page_link(page,label=page.title,use_container_width=True)
nav.run()
