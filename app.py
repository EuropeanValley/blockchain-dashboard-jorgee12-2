"""CryptoChain Analyzer Dashboard — entry point.

Run with:  streamlit run app.py
"""

import time
import datetime

import streamlit as st

st.set_page_config(
    page_title="CryptoChain Analyzer",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Hide default Streamlit chrome */
#MainMenu        { visibility: hidden; }
footer           { visibility: hidden; }
header           { visibility: hidden; }
.block-container { padding-top: 1rem; padding-bottom: 1rem; }

/* KPI metric cards */
[data-testid="metric-container"] {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 10px;
    padding: 18px 20px 14px 20px;
}
[data-testid="stMetricValue"] {
    color: #F7931A;
    font-size: 1.55rem !important;
    font-weight: 700;
}
[data-testid="stMetricLabel"] {
    color: #8B949E;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #161B22;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    border-bottom: none;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px;
    color: #8B949E;
    font-weight: 500;
    padding: 8px 18px;
}
.stTabs [aria-selected="true"] {
    background: #F7931A !important;
    color: #0D1117 !important;
    font-weight: 700;
}
.stTabs [data-baseweb="tab-highlight"] { display: none; }
.stTabs [data-baseweb="tab-border"]    { display: none; }

/* Section headers */
h2 { color: #E6EDF3; font-size: 1.05rem !important; font-weight: 600;
     margin-top: 1.4rem !important; margin-bottom: 0.5rem !important; }
h3 { color: #E6EDF3; font-size: 0.95rem !important; font-weight: 500;
     margin-top: 1rem !important; }

/* Divider */
hr { border-color: #21262D; margin: 0.8rem 0; }

/* Expanders */
.streamlit-expanderHeader {
    background: #161B22 !important;
    border: 1px solid #30363D !important;
    border-radius: 8px !important;
    color: #8B949E !important;
    font-size: 0.82rem !important;
}
.streamlit-expanderContent {
    background: #161B22 !important;
    border: 1px solid #30363D !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* Code blocks */
code, .stCode { background: #0D1117 !important; border: 1px solid #30363D; }

/* Info / success / warning boxes */
.stAlert { border-radius: 8px; border-left-width: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Imports after page config ────────────────────────────────────────────────
from modules.m1_pow_monitor      import render as render_m1
from modules.m2_block_header     import render as render_m2
from modules.m3_difficulty_history import render as render_m3
from modules.m4_ai_component     import render as render_m4

# ── Header bar ───────────────────────────────────────────────────────────────
left, right = st.columns([6, 2])
with left:
    st.markdown("## ₿ &nbsp; CryptoChain Analyzer")
    st.caption("Real-time Bitcoin cryptographic metrics &nbsp;·&nbsp; Universidad Alfonso X el Sabio")
with right:
    st.markdown("<div style='text-align:right; padding-top:12px'>", unsafe_allow_html=True)
    now = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")
    auto = st.toggle("Auto-refresh 60s", value=False, key="auto_refresh")
    st.caption(f"Last update: {now}")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "⛏  PoW Monitor",
    "🔍  Block Header",
    "📈  Difficulty History",
    "🤖  AI Anomaly Detector",
])

with tab1:  render_m1()
with tab2:  render_m2()
with tab3:  render_m3()
with tab4:  render_m4()

if auto:
    time.sleep(60)
    st.rerun()
