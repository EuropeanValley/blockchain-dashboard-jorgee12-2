"""M3 - Difficulty History."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from api.blockchain_client import get_difficulty_history

_CHART_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="sans-serif", size=12, color="#8B949E"),
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=dict(gridcolor="#21262D", showline=False),
    yaxis=dict(gridcolor="#21262D", showline=False),
)


@st.cache_data(ttl=3600)
def _load(n: int) -> list[dict]:
    return get_difficulty_history(n)


def render() -> None:
    # ── Controls ──────────────────────────────────────────────────────────────
    c_sl, c_btn = st.columns([6, 1])
    with c_sl:
        n = st.slider("Periods", 30, 200, 100, key="m3_n",
                      label_visibility="collapsed",
                      help="Number of adjustment periods (~2 weeks each)")
    with c_btn:
        if st.button("⟳", key="m3_refresh"):
            st.cache_data.clear()

    with st.spinner(""):
        try:
            values = _load(n)
        except Exception as e:
            st.error(f"API error: {e}")
            return

    df = (
        pd.DataFrame(values)
          .assign(Date=lambda d: pd.to_datetime(d["x"], unit="s"),
                  Difficulty=lambda d: d["y"])
          .sort_values("Date")
          .reset_index(drop=True)
    )
    df["Ratio"] = df["Difficulty"].shift(1) / df["Difficulty"]
    df_ratio = df.dropna(subset=["Ratio"])
    df_ratio = df_ratio[(df_ratio["Ratio"] > 0.5) & (df_ratio["Ratio"] < 2.0)]

    # ── KPI row ───────────────────────────────────────────────────────────────
    cur   = df["Difficulty"].iloc[-1]
    start = df["Difficulty"].iloc[0]
    ratio_now = df_ratio["Ratio"].iloc[-1] if len(df_ratio) else float("nan")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Current difficulty",   f"{cur:.3e}")
    k2.metric("Growth vs period start", f"{cur / start:.2f}×")
    k3.metric("Last adj. ratio",      f"{ratio_now:.4f}" if ratio_now == ratio_now else "—")
    k4.metric("Periods shown",        len(df))

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Combined chart ────────────────────────────────────────────────────────
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.62, 0.38],
        vertical_spacing=0.05,
        subplot_titles=["Mining Difficulty", "Block Time Ratio  (actual avg / 600 s target)"],
    )

    # Difficulty line + markers
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["Difficulty"],
        mode="lines", name="Difficulty",
        line=dict(color="#F7931A", width=2),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["Difficulty"],
        mode="markers", name="Adjustment",
        marker=dict(color="#1565C0", size=5),
        showlegend=True,
    ), row=1, col=1)

    # Ratio area
    fig.add_trace(go.Scatter(
        x=df_ratio["Date"], y=df_ratio["Ratio"],
        mode="lines", name="Ratio",
        line=dict(color="#42A5F5", width=1.5),
        fill="tozeroy", fillcolor="rgba(66,165,245,0.08)",
    ), row=2, col=1)
    fig.add_hline(y=1.0, row=2, col=1,
                  line_dash="dash", line_color="#EF5350", line_width=1.5,
                  annotation_text="target = 1.0", annotation_position="bottom right")

    fig.update_layout(**_CHART_LAYOUT, height=500, showlegend=True,
                      legend=dict(orientation="h", y=1.06, x=0))
    fig.update_yaxes(title_text="Difficulty", row=1, col=1, gridcolor="#21262D")
    fig.update_yaxes(title_text="Ratio",      row=2, col=1, gridcolor="#21262D")
    fig.update_xaxes(title_text="Date",       row=2, col=1, gridcolor="#21262D")

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Formula & interpretation"):
        st.markdown(
            "```\nnew_difficulty = old_difficulty × (2016 × 600 s) / actual_period_time\n```\n"
            "Ratio = `D[i-1] / D[i]` ≈ actual avg block time / 600 s.  \n"
            "**< 1** → miners faster than target → difficulty ↑  \n"
            "**> 1** → miners slower than target → difficulty ↓"
        )
