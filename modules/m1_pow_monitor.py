"""M1 - Proof of Work Monitor.

Shows live Bitcoin mining state: difficulty, hash rate, leading-zero threshold,
and the inter-block time distribution.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from api.blockchain_client import get_recent_blocks


# ---------------------------------------------------------------------------
# Cryptographic helpers
# ---------------------------------------------------------------------------

def bits_to_target(bits: int) -> int:
    """Decode compact 'bits' field to the 256-bit target integer.

    Format: first byte = exponent, remaining 3 bytes = coefficient.
    target = coefficient * 2^(8*(exponent - 3))
    """
    exp = (bits >> 24) & 0xFF
    coeff = bits & 0x007FFFFF
    return coeff * (2 ** (8 * (exp - 3)))


def count_leading_zero_bits(hash_hex: str) -> int:
    """Count leading zero bits in a 256-bit hash (given as hex string)."""
    n = int(hash_hex, 16)
    if n == 0:
        return 256
    return 256 - n.bit_length()


# ---------------------------------------------------------------------------
# Cached data fetch
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def _fetch_blocks(n: int) -> list[dict]:
    return get_recent_blocks(n)


# ---------------------------------------------------------------------------
# Streamlit render
# ---------------------------------------------------------------------------

def render() -> None:
    st.header("M1 — Proof of Work Monitor")
    st.caption("Live data about the current state of Bitcoin mining.")

    col_slider, col_btn = st.columns([5, 1])
    with col_slider:
        n_blocks = st.slider("Blocks to analyse", 20, 150, 50, key="m1_n")
    with col_btn:
        st.write("")
        if st.button("Refresh", key="m1_refresh"):
            st.cache_data.clear()

    with st.spinner("Fetching recent blocks from Blockstream…"):
        try:
            blocks = _fetch_blocks(n_blocks)
        except Exception as exc:
            st.error(f"API error: {exc}")
            return

    latest = blocks[0]
    bits = latest["bits"]
    target = bits_to_target(bits)
    difficulty = latest["difficulty"]
    leading_zeros = count_leading_zero_bits(latest["id"])

    # Estimated hash rate: difficulty * 2^32 / target_block_time (600 s)
    # Unit conversion: /1e18 → EH/s
    hash_rate_eh = difficulty * (2 ** 32) / 600 / 1e18

    # -----------------------------------------------------------------------
    # Top metrics
    # -----------------------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Block Height", f"{latest['height']:,}")
    c2.metric("Difficulty", f"{difficulty:.3e}")
    c3.metric("Est. Hash Rate", f"{hash_rate_eh:.2f} EH/s")
    c4.metric("Leading Zero Bits", leading_zeros)

    # -----------------------------------------------------------------------
    # Target threshold visualisation
    # -----------------------------------------------------------------------
    st.subheader("Current Target Threshold (256-bit SHA-256 space)")
    target_hex = f"{target:064x}"
    st.code(
        f"Target:     {target_hex}\n"
        f"Block hash: {latest['id']}"
    )
    st.caption(
        f"The `bits` field `0x{bits:08x}` encodes a target requiring the block hash "
        f"to start with at least **{leading_zeros} leading zero bits** — a number < the target above. "
        "Miners iterate the nonce until SHA-256(SHA-256(header)) satisfies this constraint."
    )

    # -----------------------------------------------------------------------
    # Inter-block time distribution
    # -----------------------------------------------------------------------
    st.subheader(f"Inter-Block Time Distribution (last {n_blocks} blocks)")

    sorted_blocks = sorted(blocks, key=lambda b: b["height"])
    times_min = [
        (sorted_blocks[i + 1]["timestamp"] - sorted_blocks[i]["timestamp"]) / 60
        for i in range(len(sorted_blocks) - 1)
        if sorted_blocks[i + 1]["timestamp"] > sorted_blocks[i]["timestamp"]
    ]

    if not times_min:
        st.warning("Not enough data to plot distribution.")
        return

    mean_min = sum(times_min) / len(times_min)

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=times_min,
        nbinsx=35,
        marker_color="#F7931A",
        opacity=0.85,
        name="Observed intervals",
    ))
    fig.add_vline(
        x=10, line_dash="dash", line_color="red", line_width=2,
        annotation_text="Target: 10 min", annotation_position="top right",
    )
    fig.add_vline(
        x=mean_min, line_dash="dot", line_color="#00c853", line_width=2,
        annotation_text=f"Mean: {mean_min:.1f} min",
        annotation_position="top left",
    )
    fig.update_layout(
        xaxis_title="Time between consecutive blocks (minutes)",
        yaxis_title="Count",
        showlegend=False,
        margin=dict(t=30),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "Block inter-arrival times follow an **exponential distribution** because "
        "mining is a memoryless Poisson process: each hash attempt succeeds independently "
        "with constant probability. The Bitcoin protocol targets a mean of **10 minutes** "
        "and adjusts difficulty every 2 016 blocks to maintain it."
    )

    c_mean, c_std = st.columns(2)
    import statistics
    c_mean.metric("Mean inter-block time", f"{mean_min:.2f} min")
    if len(times_min) > 1:
        c_std.metric("Std dev", f"{statistics.stdev(times_min):.2f} min")
