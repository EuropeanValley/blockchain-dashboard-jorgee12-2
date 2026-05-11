"""CryptoChain Analyzer Dashboard — modular entry point.

Run with:  streamlit run app.py
"""

import datetime
import streamlit as st

from api.blockchain_client import get_tip_hash, get_block, get_block_header_hex
from modules import (
    m1_pow_monitor,
    m2_block_header,
    m3_difficulty_history,
    m4_ai_component,
    m5_tx_explorer,
    m6_security,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CryptoChain Analyzer",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS (Shared across modules) ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Space+Grotesk:wght@300;500;700&display=swap');

:root {
    --primary: #F7931A;
    --secondary: #1565C0;
    --bg: #030508;
    --card-bg: rgba(13, 17, 23, 0.7);
    --border: rgba(255, 255, 255, 0.1);
}

#MainMenu, footer, header, .stDeployButton {display:none!important}
.block-container {padding: 1.5rem 3rem !important; background-color: var(--bg)}

/* Global Typography */
html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif !important;
    color: #E6EDF3 !important;
}

h1, h2, h3, .section-label {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

/* Glassmorphism Containers */
div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column"] > div {
    /* background: var(--card-bg);
    backdrop-filter: blur(12px);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1rem;
    margin-bottom: 1rem; */
}

/* Custom KPI Cards */
[data-testid="metric-container"] {
    background: linear-gradient(145deg, rgba(20, 26, 35, 0.8), rgba(10, 14, 20, 0.9)) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4) !important;
    transition: transform 0.3s ease, border-color 0.3s ease !important;
}

[data-testid="metric-container"]:hover {
    transform: translateY(-5px);
    border-color: var(--primary) !important;
}

[data-testid="stMetricValue"] {
    color: var(--primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    text-shadow: 0 0 20px rgba(247, 147, 26, 0.3);
}

[data-testid="stMetricLabel"] {
    color: #8B949E !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* Animated Background */
.main {
    background: radial-gradient(circle at 50% -20%, #1a237e 0%, #030508 60%) !important;
}

/* Section labels */
.section-label {
    color: var(--primary);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 1rem;
    border-left: 3px solid var(--primary);
    padding-left: 10px;
}

/* Buttons */
.stButton>button {
    background: rgba(247, 147, 26, 0.1) !important;
    border: 1px solid var(--primary) !important;
    color: var(--primary) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}
.stButton>button:hover {
    background: var(--primary) !important;
    color: white !important;
    box-shadow: 0 0 20px rgba(247, 147, 26, 0.4) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #05070A !important;
    border-right: 1px solid var(--border);
}

hr {
    border: 0;
    height: 1px;
    background: linear-gradient(to right, transparent, var(--border), transparent);
    margin: 2rem 0;
}
</style>
""", unsafe_allow_html=True)

# ── Shared Data Loader (Global Tip) ──────────────────────────────────────────
@st.cache_data(ttl=30)
def load_tip():
    tip_hash = get_tip_hash()
    block = get_block(tip_hash)
    return tip_hash, block

# ── Sidebar Configuration ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ₿ Settings")
    auto_refresh = st.toggle("Auto-refresh 60s", value=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("⟳ Clear Cache"):
        st.cache_data.clear()
    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption(f"UTC: {datetime.datetime.utcnow().strftime('%H:%M:%S')}")
    st.info("The dashboard updates automatically. Use the sidebar only for global settings.")

# ── Global Header ────────────────────────────────────────────────────────────
tip_hash, tip_block = load_tip()

st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 2rem;">
    <div style="display: flex; align-items: center; gap: 20px;">
        <div style="background: var(--primary); padding: 12px; border-radius: 14px; box-shadow: 0 0 30px rgba(247,147,26,0.4);">
            <img src="https://cryptologos.cc/logos/bitcoin-btc-logo.png" width="35" style="filter: brightness(0) invert(1);">
        </div>
        <div>
            <h1 style="margin:0; font-size: 2.2rem;">CryptoChain <span style="color:var(--primary)">Analyzer</span></h1>
            <p style="margin:0; color: #8B949E; font-size: 0.9rem;">Intelligence layer for the Bitcoin network · Protocol Analysis</p>
        </div>
    </div>
    <div style="text-align: right;">
        <div style="display: flex; align-items: center; gap: 8px; justify-content: flex-end;">
            <div style="width: 10px; height: 10px; background: #66BB6A; border-radius: 50%; box-shadow: 0 0 10px #66BB6A; animation: pulse 2s infinite;"></div>
            <span style="font-weight: 700; font-size: 0.8rem; letter-spacing: 0.1em; color: #66BB6A;">LIVE MONITORING</span>
        </div>
        <p style="margin:0; color: #8B949E; font-size: 0.75rem; margin-top: 4px;">BLOCK HEIGHT: <b>{height}</b></p>
    </div>
</div>

<style>
@keyframes pulse {{
    0% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.5; transform: scale(0.8); }}
    100% {{ opacity: 1; transform: scale(1); }}
}}
</style>
""".format(height=f"{tip_block['height']:,}"), unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Section 1: Network & PoW Status ─────────────────────────────────────────
col_m1, col_m2 = st.columns([1, 1], gap="large")

with col_m1:
    m1_pow_monitor.render()

with col_m2:
    m2_block_header.render()

st.markdown("<hr>", unsafe_allow_html=True)

# ── Section 2: AI & History ─────────────────────────────────────────────────
col_m3, col_m4 = st.columns([1, 1], gap="large")

with col_m3:
    m3_difficulty_history.render()

with col_m4:
    m4_ai_component.render()

st.markdown("<hr>", unsafe_allow_html=True)

# ── Section 3: Transactions & Security ──────────────────────────────────────
col_m5, col_m6 = st.columns([1, 1], gap="large")

with col_m5:
    m5_tx_explorer.render(tip_hash)

with col_m6:
    m6_security.render()

# ── Auto-refresh logic ───────────────────────────────────────────────────────
if auto_refresh:
    import time
    time.sleep(60)
    st.rerun()
