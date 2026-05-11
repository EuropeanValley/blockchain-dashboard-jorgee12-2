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
    m7_mempool,
    m8_witness_analyzer,
    m9_nonce_entropy,
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
    --neon-orange: #FFAB40;
    --neon-blue: #00E5FF;
    --secondary: #1565C0;
    --bg: #020406;
    --card-bg: rgba(10, 15, 25, 0.7);
    --border: rgba(255, 255, 255, 0.08);
}

#MainMenu, footer, header, .stDeployButton {display:none!important}

/* Global Typography */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    color: #E6EDF3 !important;
}

h1, h2, h3, .section-label {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
}

/* Moving Cyber-Grid Background */
.main {
    background-color: var(--bg) !important;
    background-image: 
        linear-gradient(rgba(247, 147, 26, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(247, 147, 26, 0.03) 1px, transparent 1px) !important;
    background-size: 40px 40px !important;
    animation: grid-move 20s linear infinite !important;
}

@keyframes grid-move {
    0% { background-position: 0 0; }
    100% { background-position: 40px 40px; }
}

.block-container {
    padding: 2rem 4rem !important;
}

/* Custom Metric Cards with Animated Border */
[data-testid="metric-container"] {
    background: var(--card-bg) !important;
    backdrop-filter: blur(15px) !important;
    border: 1px solid var(--border) !important;
    border-radius: 20px !important;
    padding: 24px !important;
    box-shadow: 0 10px 40px rgba(0,0,0,0.5) !important;
    position: relative;
    overflow: hidden;
}

[data-testid="metric-container"]::before {
    content: "";
    position: absolute;
    top: 0; left: -100%;
    width: 100%; height: 2px;
    background: linear-gradient(90deg, transparent, var(--primary), transparent);
    animation: border-trace 4s linear infinite;
}

@keyframes border-trace {
    0% { left: -100%; }
    100% { left: 100%; }
}

[data-testid="stMetricValue"] {
    color: var(--primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 2rem !important;
    text-shadow: 0 0 25px rgba(247, 147, 26, 0.4);
}

/* Section labels with Neon Underline */
.section-label {
    color: var(--primary);
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    margin-bottom: 1.5rem;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(247,147,26,0.2);
    display: inline-block;
}

/* Styled Scrollbar */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { 
    background: rgba(247, 147, 26, 0.2); 
    border-radius: 10px; 
}
::-webkit-scrollbar-thumb:hover { background: var(--primary); }

/* Sidebar Premium */
[data-testid="stSidebar"] {
    background-color: #030508 !important;
    border-right: 1px solid var(--border);
}

/* Glass Containers for Sections */
.stContainer {
    background: rgba(255, 255, 255, 0.02) !important;
    border-radius: 24px !important;
    padding: 25px !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    margin-bottom: 2rem !important;
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

@st.cache_data(ttl=60)
def load_multi_blocks(n=50):
    from api.blockchain_client import get_recent_blocks
    return get_recent_blocks(n)

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
multi_blocks = load_multi_blocks(50)

# ── Live Ticker ─────────────────────────────────────────────────────────────
st.markdown("""
<div style="background: rgba(247,147,26,0.05); border: 1px solid rgba(247,147,26,0.1); border-radius: 8px; padding: 10px 20px; margin-bottom: 2rem; display: flex; align-items: center; overflow: hidden;">
    <div style="white-space: nowrap; animation: marquee 30s linear infinite; display: flex; gap: 50px; font-size: 0.85rem; font-weight: 500; color: #8B949E;">
        <span>🔥 <span style="color:var(--primary)">NETWORK STATUS:</span> HEALTHY</span>
        <span>📊 <span style="color:var(--primary)">DIFFICULTY:</span> {diff:.2e}</span>
        <span>⏱ <span style="color:var(--primary)">AVG BLOCK TIME:</span> 10.02 MIN</span>
        <span>⛓ <span style="color:var(--primary)">MEMPOOL:</span> ACTIVE</span>
        <span>🚀 <span style="color:var(--primary)">HASH RATE:</span> {hr:.2f} EH/s</span>
        <span>🔥 <span style="color:var(--primary)">NETWORK STATUS:</span> HEALTHY</span>
        <span>📊 <span style="color:var(--primary)">DIFFICULTY:</span> {diff:.2e}</span>
    </div>
</div>
<style>
@keyframes marquee {{
    0% {{ transform: translateX(0); }}
    100% {{ transform: translateX(-50%); }}
}}
</style>
""".format(diff=tip_block['difficulty'], hr=tip_block['difficulty'] * (2**32) / 600 / 1e18), unsafe_allow_html=True)

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
with st.container():
    col_m1, col_m2 = st.columns([1, 1], gap="large")
    with col_m1:
        m1_pow_monitor.render()
    with col_m2:
        m2_block_header.render()

st.markdown("<hr>", unsafe_allow_html=True)

# ── Section 2: AI & History ─────────────────────────────────────────────────
with st.container():
    col_m3, col_m4 = st.columns([1, 1], gap="large")
    with col_m3:
        m3_difficulty_history.render()
    with col_m4:
        m4_ai_component.render()

st.markdown("<hr>", unsafe_allow_html=True)

# ── Section 3: Transactions & Mempool ───────────────────────────────────────
with st.container():
    col_m5, col_m7 = st.columns([1, 1], gap="large")
    with col_m5:
        m5_tx_explorer.render(tip_hash)
    with col_m7:
        m7_mempool.render()

st.markdown("<hr>", unsafe_allow_html=True)

# ── Section 4: Cryptography Deep Dive (M8 & M9) ──────────────────────────────
with st.container():
    col_m8, col_m9 = st.columns([1, 1], gap="large")
    with col_m8:
        m8_witness_analyzer.render(multi_blocks)
    with col_m9:
        m9_nonce_entropy.render(multi_blocks)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Section 5: Security Score ───────────────────────────────────────────────
with st.container():
    m6_security.render()

# ── Auto-refresh logic ───────────────────────────────────────────────────────
if auto_refresh:
    import time
    time.sleep(60)
    st.rerun()
