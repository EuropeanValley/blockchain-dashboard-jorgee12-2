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

# ── Sidebar Navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ₿ CryptoChain")
    st.caption("v1.0 — Academic Project")
    st.markdown("<hr>", unsafe_allow_html=True)
    
    page = st.radio(
        "Navigation",
        [
            "Overview Dashboard",
            "PoW Monitor (M1)",
            "Block Header (M2)",
            "Diff. History (M3)",
            "AI Anomaly (M4)",
            "Tx Explorer (M5)",
            "Security Score (M6)",
        ]
    )
    
    st.markdown("<hr>", unsafe_allow_html=True)
    auto_refresh = st.toggle("Auto-refresh 60s", value=False)
    if st.button("⟳ Clear Cache"):
        st.cache_data.clear()
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption(f"UTC: {datetime.datetime.utcnow().strftime('%H:%M:%S')}")

# ── Global Header ────────────────────────────────────────────────────────────
tip_hash, tip_block = load_tip()

# ── Page Routing ─────────────────────────────────────────────────────────────
if page == "Overview Dashboard":
    st.markdown("### 📊 Project Overview")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Block Height", f"{tip_block['height']:,}")
    k2.metric("Difficulty", f"{tip_block['difficulty']:.2e}")
    k3.metric("Transactions", f"{tip_block.get('tx_count', 0):,}")
    k4.metric("Last Seen", datetime.datetime.utcfromtimestamp(tip_block['timestamp']).strftime("%H:%M UTC"))
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Show small snippets of M1 and M2 in overview
    c1, c2 = st.columns(2)
    with c1:
        st.info("💡 **M1 & M2** are focused on the current Proof of Work state and block structure.")
    with c2:
        st.info("🧠 **M4** implements an AI Anomaly Detector using an Exponential distribution baseline.")
    
    st.markdown("#### Latest Block Tx Network")
    m5_tx_explorer.render(tip_hash)

elif page == "PoW Monitor (M1)":
    m1_pow_monitor.render()

elif page == "Block Header (M2)":
    m2_block_header.render()

elif page == "Diff. History (M3)":
    m3_difficulty_history.render()

elif page == "AI Anomaly (M4)":
    m4_ai_component.render()

elif page == "Tx Explorer (M5)":
    m5_tx_explorer.render(tip_hash)

elif page == "Security Score (M6)":
    m6_security.render()

# ── Auto-refresh logic ───────────────────────────────────────────────────────
if auto_refresh:
    import time
    time.sleep(60)
    st.rerun()
