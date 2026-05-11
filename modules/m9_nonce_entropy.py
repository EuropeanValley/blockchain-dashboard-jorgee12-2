"""M9 - Nonce Entropy & ASIC Fingerprinting."""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from api.blockchain_client import get_block_header_hex

def _extract_nonce(header_hex: str) -> int:
    import struct
    raw = bytes.fromhex(header_hex)
    return struct.unpack_from("<I", raw, 76)[0]

def render(blocks: list) -> None:
    st.markdown('<p class="section-label">Nonce Entropy & ASIC Analysis — M9</p>',
                unsafe_allow_html=True)

    if not blocks:
        st.warning("Data required.")
        return

    # To get real nonces, we might need to fetch raw headers for each block
    # But since that's slow, we'll use a subset or cached data if available.
    # For now, let's assume we can fetch at least 20 raw nonces for the demo.
    
    with st.spinner("Analyzing nonce distribution..."):
        nonces = []
        # In a real app, we'd fetch these. For the dashboard feel, we use 50 blocks.
        # Let's use the 'nonce' field if it exists in the block dict (it might not in Blockstream API)
        # Blockstream block dict has 'id', 'height', 'version', 'timestamp', 'tx_count', 'size', 'weight', 'merkle_root', 'previousblockhash', 'mediantime', 'nonce', 'bits', 'difficulty'
        for b in blocks[:50]:
            if 'nonce' in b:
                nonces.append(b['nonce'])
    
    if not nonces:
        st.info("Nonce data not directly provided by API. Fetching subset from raw headers...")
        # Fallback: fetch a few raw headers
        for b in blocks[:10]:
            try:
                hdr = get_block_header_hex(b['id'])
                nonces.append(_extract_nonce(hdr))
            except: continue

    if not nonces:
        st.error("Could not fetch nonce data.")
        return

    # Statistics
    nonce_arr = np.array(nonces)
    entropy = -np.sum((nonce_arr/2**32) * np.log2(nonce_arr/2**32 + 1e-12)) / len(nonces) # Simplified normalized entropy
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Sample Size", len(nonces))
    c2.metric("Max Nonce", f"{nonce_arr.max():,}")
    c3.metric("Min Nonce", f"{nonce_arr.min():,}")

    st.markdown("<hr>", unsafe_allow_html=True)

    # Visualization: Scatter of nonces
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(nonces))), y=nonces,
        mode='markers',
        marker=dict(
            size=10,
            color=nonces,
            colorscale='Viridis',
            showscale=True,
            line=dict(width=1, color='rgba(255,255,255,0.1)')
        ),
        name='Nonce Value'
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk, sans-serif", size=11, color="#8B949E"),
        height=350,
        xaxis_title="Block Index",
        yaxis_title="Nonce Value (32-bit)",
        title=dict(text="Nonce Distribution (0 to 2^32)", font=dict(size=12))
    )
    st.plotly_chart(fig, width='stretch')

    st.caption("A perfectly uniform distribution suggests high entropy. Patterns (clusters) can reveal specific ASIC manufacturer strategies or software-defined nonce ranges.")
