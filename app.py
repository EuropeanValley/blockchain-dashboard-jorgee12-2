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
    --primary-glow: rgba(247, 147, 26, 0.5);
    --secondary: #00E5FF;
    --bg: #010204;
    --card-bg: rgba(8, 12, 20, 0.85);
    --border: rgba(255, 255, 255, 0.05);
}

#MainMenu, footer, header, .stDeployButton {display:none!important}

/* Cinematic Film Grain Overlay */
.main::before {
    content: "";
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image: url("https://www.transparenttextures.com/patterns/carbon-fibre.png");
    opacity: 0.03;
    pointer-events: none;
    z-index: 999;
}

/* Hypermodern Background with Perspective Grid */
.main {
    background-color: var(--bg) !important;
    background-image: 
        radial-gradient(circle at 50% 0%, rgba(247, 147, 26, 0.08) 0%, transparent 50%),
        linear-gradient(rgba(247, 147, 26, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(247, 147, 26, 0.02) 1px, transparent 1px) !important;
    background-size: 100% 100%, 60px 60px, 60px 60px !important;
    animation: grid-drift 60s linear infinite !important;
}

@keyframes grid-drift {
    0% { background-position: 0 0, 0 0, 0 0; }
    100% { background-position: 0 0, 60px 60px, 60px 60px; }
}

.block-container {
    padding: 3rem 5rem !important;
}

/* Floating Glass Containers */
.stContainer {
    background: var(--card-bg) !important;
    backdrop-filter: blur(25px) saturate(150%) !important;
    border: 1px solid var(--border) !important;
    border-radius: 28px !important;
    padding: 30px !important;
    box-shadow: 0 20px 50px rgba(0,0,0,0.6), inset 0 0 20px rgba(255,255,255,0.02) !important;
    margin-bottom: 2.5rem !important;
    animation: float 6s ease-in-out infinite;
}

@keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
    100% { transform: translateY(0px); }
}

/* Holographic Titles */
h1, h2, h3 {
    background: linear-gradient(135deg, #fff 0%, var(--primary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.03em !important;
}

/* Advanced KPI Cards */
[data-testid="metric-container"] {
    background: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 22px !important;
    padding: 25px !important;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
}

[data-testid="metric-container"]:hover {
    background: rgba(247, 147, 26, 0.05) !important;
    border-color: var(--primary) !important;
    box-shadow: 0 0 30px rgba(247, 147, 26, 0.2) !important;
    transform: scale(1.02) !important;
}

[data-testid="stMetricValue"] {
    font-size: 2.2rem !important;
    background: linear-gradient(to bottom, #fff, var(--primary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: none !important;
}

/* Buttons with Neon Pulse */
.stButton>button {
    background: transparent !important;
    border: 1px solid var(--primary) !important;
    color: var(--primary) !important;
    box-shadow: inset 0 0 10px rgba(247, 147, 26, 0.2) !important;
    border-radius: 14px !important;
    padding: 0.5rem 2rem !important;
}

.stButton>button:hover {
    box-shadow: 0 0 25px var(--primary-glow), inset 0 0 10px var(--primary-glow) !important;
    background: var(--primary) !important;
    color: white !important;
}

/* Hypermodern Section Labels */
.section-label {
    font-family: 'Space Grotesk', sans-serif;
    color: var(--primary);
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.3em;
    padding: 5px 15px;
    border-left: 3px solid var(--primary);
    background: linear-gradient(90deg, rgba(247, 147, 26, 0.1), transparent);
    margin-bottom: 2rem;
    display: block;
    box-shadow: -10px 0 20px rgba(247, 147, 26, 0.1);
}

h2, h3 {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* Scrollbar and Sidebar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }

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
@st.cache_data(ttl=300) # Longer cache for stability
def load_network_data():
    try:
        tip_hash = get_tip_hash()
        block = get_block(tip_hash)
        return tip_hash, block, False
    except Exception as e:
        # Fallback to mock data if rate limited
        st.warning("📡 API Offline/Rate Limited. Displaying cached/mock data for demonstration.")
        mock_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        mock_block = {
            'id': mock_hash, 'height': 840000, 'version': 2, 'timestamp': 1714000000,
            'tx_count': 3500, 'size': 1500000, 'weight': 3990000, 'difficulty': 80e12,
            'merkle_root': 'mock_merkle', 'nonce': 123456789
        }
        return mock_hash, mock_block, True

@st.cache_data(ttl=600)
def load_multi_blocks(n=50):
    try:
        from api.blockchain_client import get_recent_blocks
        return get_recent_blocks(n)
    except:
        # Generate some realistic mock block intervals for M4/M3
        import time
        now = int(time.time())
        mock_blocks = []
        for i in range(n):
            mock_blocks.append({
                'id': f"mock_{i}", 'height': 840000 - i, 'timestamp': now - (i * 600),
                'difficulty': 80e12, 'size': 1400000, 'weight': 3800000, 'nonce': 123456
            })
        return mock_blocks

# ── Sidebar Configuration ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ₿ Settings")
    auto_refresh = st.toggle("Auto-refresh 60s", value=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("⟳ Clear Cache"):
        st.cache_data.clear()
    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption(f"UTC: {datetime.datetime.now(datetime.UTC).strftime('%H:%M:%S')}")
    st.info("The dashboard updates automatically. Use the sidebar only for global settings.")

# ── Global Header ────────────────────────────────────────────────────────────
try:
    tip_hash, tip_block, is_mock = load_network_data()
    multi_blocks = load_multi_blocks(50)
except Exception as e:
    st.error(f"Critical Data Error: {e}")
    st.stop()

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

# ── Section 1: Network Core & Protocol ──────────────────────────────────────
st.markdown("## 🌐 Network Core & Protocol")
with st.container():
    col_m1, col_m2 = st.columns([1, 1], gap="large")
    with col_m1:
        m1_pow_monitor.render(multi_blocks)
    with col_m2:
        m2_block_header.render(tip_hash, tip_block)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Section 2: Intelligent Analysis & History ───────────────────────────────
st.markdown("## 🧠 Intelligent Analysis & History")
with st.container():
    col_m3, col_m4 = st.columns([1, 1], gap="large")
    with col_m3:
        m3_difficulty_history.render(multi_blocks)
    with col_m4:
        m4_ai_component.render(multi_blocks)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Section 3: Value Flow & Market ──────────────────────────────────────────
st.markdown("## 💸 Value Flow & Market")
with st.container():
    col_m5, col_m7 = st.columns([1, 1], gap="large")
    with col_m5:
        m5_tx_explorer.render(tip_hash)
    with col_m7:
        m7_mempool.render()

st.markdown("<hr>", unsafe_allow_html=True)

# ── Section 4: Advanced Cryptography ────────────────────────────────────────
st.markdown("## 🔐 Advanced Cryptography")
with st.container():
    col_m8, col_m9 = st.columns([1, 1], gap="large")
    with col_m8:
        m8_witness_analyzer.render(multi_blocks)
    with col_m9:
        m9_nonce_entropy.render(multi_blocks)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Section 5: Security Evaluation ──────────────────────────────────────────
st.markdown("## 🛡️ Security Evaluation")
with st.container():
    m6_security.render(tip_block)

# ── Auto-refresh logic ───────────────────────────────────────────────────────
if auto_refresh:
    import time
    time.sleep(60)
    st.rerun()
