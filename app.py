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
#MainMenu,footer,header,.stDeployButton{display:none!important}
.block-container{padding:0.8rem 2rem 1rem 2rem}

/* KPI cards */
[data-testid="metric-container"]{
  background:#0D1117;border:1px solid #21262D;
  border-radius:10px;padding:16px 18px 12px;
}
[data-testid="stMetricValue"]{
  color:#F7931A;font-size:1.45rem!important;font-weight:700;
}
[data-testid="stMetricLabel"]{
  color:#6E7681;font-size:.72rem!important;
  text-transform:uppercase;letter-spacing:.06em;
}

/* Section dividers */
hr{border:none;border-top:1px solid #21262D;margin:.6rem 0}

/* Expanders */
.streamlit-expanderHeader{
  background:#0D1117!important;border:1px solid #21262D!important;
  border-radius:8px!important;color:#6E7681!important;font-size:.82rem!important;
}
.streamlit-expanderContent{
  background:#0D1117!important;border:1px solid #21262D!important;
  border-top:none!important;border-radius:0 0 8px 8px!important;
}

/* Code */
code,.stCode{background:#070B0F!important;border:1px solid #21262D;
  font-size:.78rem!important;}

/* Alert boxes */
.stAlert{border-radius:8px;border-left-width:3px}

/* Section labels */
.section-label{
  color:#6E7681;font-size:.7rem;text-transform:uppercase;
  letter-spacing:.1em;margin-bottom:.2rem;
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

st.markdown("### ₿ &nbsp;CryptoChain Analyzer Dashboard")
st.caption(f"Real-time monitoring of the Bitcoin network · Block #{tip_block['height']:,}")
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
