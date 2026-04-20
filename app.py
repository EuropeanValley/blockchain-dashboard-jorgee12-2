"""CryptoChain Analyzer Dashboard — entry point.

Run with:  streamlit run app.py
"""

import time

import streamlit as st

from modules.m1_pow_monitor import render as render_m1
from modules.m2_block_header import render as render_m2
from modules.m3_difficulty_history import render as render_m3
from modules.m4_ai_component import render as render_m4

st.set_page_config(
    page_title="CryptoChain Analyzer",
    page_icon="₿",
    layout="wide",
)

st.title("₿ CryptoChain Analyzer Dashboard")
st.caption(
    "Real-time Bitcoin cryptographic metrics — "
    "Cryptography project · Universidad Alfonso X el Sabio"
)

# Sidebar — auto-refresh toggle
with st.sidebar:
    st.header("Settings")
    auto_refresh = st.checkbox("Auto-refresh every 60 s", value=False)
    if auto_refresh:
        st.info("Dashboard will reload automatically every 60 seconds.")
    st.markdown("---")
    st.markdown(
        "**APIs used**\n"
        "- [Blockstream](https://blockstream.info/api) (blocks, headers)\n"
        "- [Blockchain.info](https://blockchain.info) (difficulty history)"
    )

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "M1 — PoW Monitor",
    "M2 — Block Header",
    "M3 — Difficulty History",
    "M4 — AI Anomaly Detector",
])

with tab1:
    render_m1()
with tab2:
    render_m2()
with tab3:
    render_m3()
with tab4:
    render_m4()

# Auto-refresh: sleep then rerun the entire app
if auto_refresh:
    time.sleep(60)
    st.rerun()
