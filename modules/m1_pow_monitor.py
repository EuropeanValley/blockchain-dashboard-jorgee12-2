"""M1 - Proof of Work Monitor."""

import statistics

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from api.blockchain_client import get_recent_blocks

_CHART_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Space Grotesk, sans-serif", size=12, color="#8B949E"),
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", showline=False, zeroline=False),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", showline=False, zeroline=False),
)


def _bits_to_target(bits: int) -> int:
    exp, coeff = (bits >> 24) & 0xFF, bits & 0x007FFFFF
    return coeff * (2 ** (8 * (exp - 3)))


def _leading_zeros(hash_hex: str) -> int:
    n = int(hash_hex, 16)
    return 256 - n.bit_length() if n else 256


@st.cache_data(ttl=60)
def _load(n: int) -> list[dict]:
    return get_recent_blocks(n)


def render() -> None:
    # ── Controls ─────────────────────────────────────────────────────────────
    c_slider, c_btn = st.columns([6, 1])
    with c_slider:
        n = st.slider("Blocks", 20, 150, 50, key="m1_n",
                      label_visibility="collapsed",
                      help="Number of recent blocks to analyse")
    with c_btn:
        if st.button("⟳", key="m1_refresh", help="Refresh data"):
            st.cache_data.clear()

    # ── Fetch ─────────────────────────────────────────────────────────────────
    with st.spinner(""):
        try:
            blocks = _load(n)
        except Exception as e:
            st.error(f"API error: {e}")
            return

    latest = blocks[0]
    bits       = latest["bits"]
    difficulty = latest["difficulty"]
    target     = _bits_to_target(bits)
    lz         = _leading_zeros(latest["id"])
    hr_eh      = difficulty * (2 ** 32) / 600 / 1e18

    # ── KPI row ───────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Block height",    f"{latest['height']:,}")
    k2.metric("Difficulty",      f"{difficulty:.3e}")
    k3.metric("Hash rate",       f"{hr_eh:.2f} EH/s")
    k4.metric("Leading zero bits", lz)
    k5.metric("Blocks analysed", n)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Target hex ────────────────────────────────────────────────────────────
    target_hex = f"{target:064x}"
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Current target threshold**")
        st.code(
            f"Target  {target_hex}\n"
            f"Hash    {latest['id']}",
            language=None,
        )
        st.caption(
            f"`bits = 0x{bits:08x}` expands to the 256-bit value above. "
            f"A valid hash must be smaller — requiring **{lz} leading zero bits**."
        )

    # ── Inter-block times ─────────────────────────────────────────────────────
    sorted_b  = sorted(blocks, key=lambda b: b["height"])
    times_min = [
        (sorted_b[i+1]["timestamp"] - sorted_b[i]["timestamp"]) / 60
        for i in range(len(sorted_b) - 1)
        if sorted_b[i+1]["timestamp"] > sorted_b[i]["timestamp"]
    ]

    if not times_min:
        return

    mean_m  = sum(times_min) / len(times_min)
    stdev_m = statistics.stdev(times_min) if len(times_min) > 1 else 0

    with col_r:
        st.markdown("**Inter-block time stats**")
        s1, s2 = st.columns(2)
        s1.metric("Mean",  f"{mean_m:.2f} min")
        s2.metric("Stdev", f"{stdev_m:.2f} min")
        st.caption(
            "Expected distribution: **Exponential** (memoryless Poisson process). "
            "Each hash attempt is independent → waiting times are exp-distributed."
        )

    # ── Histogram + time series ───────────────────────────────────────────────
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Inter-block time distribution", "Block times — sequence"),
        horizontal_spacing=0.08,
    )

    fig.add_trace(go.Histogram(
        x=times_min, nbinsx=30,
        marker_color="#F7931A", opacity=0.8, name="Observed",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=list(range(len(times_min))), y=times_min,
        mode="lines", line=dict(color="#F7931A", width=1.2),
        name="Interval",
    ), row=1, col=2)
    fig.add_hline(y=10,     line_dash="dash",  line_color="#EF5350", line_width=1.5,
                  annotation_text="10 min target", row=1, col=2)
    fig.add_hline(y=mean_m, line_dash="dot",   line_color="#66BB6A", line_width=1.5,
                  annotation_text=f"mean {mean_m:.1f} min", row=1, col=2)

    fig.update_layout(**_CHART_LAYOUT, height=320, showlegend=False)
    fig.update_xaxes(title_text="Minutes", row=1, col=1, gridcolor="#21262D")
    fig.update_xaxes(title_text="Block index", row=1, col=2, gridcolor="#21262D")
    fig.update_yaxes(title_text="Count", row=1, col=1, gridcolor="#21262D")
    fig.update_yaxes(title_text="Minutes", row=1, col=2, gridcolor="#21262D")

    st.plotly_chart(fig, use_container_width=True)
