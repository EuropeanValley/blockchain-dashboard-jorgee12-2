"""M3 - Difficulty History.

Plots Bitcoin mining difficulty over the last ~2 years, marks each
adjustment event, and shows the ratio of actual vs target block time
per adjustment period.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from api.blockchain_client import get_difficulty_history


# ---------------------------------------------------------------------------
# Cached data fetch
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def _fetch_difficulty(n_points: int) -> list[dict]:
    return get_difficulty_history(n_points)


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def build_dataframe(values: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(values)
    df["Date"] = pd.to_datetime(df["x"], unit="s")
    df = df.rename(columns={"y": "Difficulty"}).drop(columns=["x"])
    df = df.sort_values("Date").reset_index(drop=True)

    # Ratio = actual_avg_block_time / target_block_time (600 s)
    # Derivation: at each adjustment new_D = old_D * target / actual
    #   => actual / target = old_D / new_D = D[i-1] / D[i]
    df["Ratio"] = df["Difficulty"].shift(1) / df["Difficulty"]
    return df


# ---------------------------------------------------------------------------
# Streamlit render
# ---------------------------------------------------------------------------

def render() -> None:
    st.header("M3 — Difficulty History")
    st.caption(
        "Evolution of Bitcoin mining difficulty over the last ~2 years. "
        "Difficulty adjusts every 2 016 blocks (~2 weeks) to keep the "
        "average block time at 600 seconds."
    )

    col_slider, col_btn = st.columns([5, 1])
    with col_slider:
        n_points = st.slider("Data points (approx. weeks)", 30, 200, 100, key="m3_n")
    with col_btn:
        st.write("")
        if st.button("Refresh", key="m3_refresh"):
            st.cache_data.clear()

    with st.spinner("Loading difficulty data from Blockchain.info…"):
        try:
            values = _fetch_difficulty(n_points)
        except Exception as exc:
            st.error(f"API error: {exc}")
            return

    df = build_dataframe(values)
    df_ratio = df.dropna(subset=["Ratio"])
    # Remove clearly erroneous ratio values (e.g. sampled data artefacts)
    df_ratio = df_ratio[(df_ratio["Ratio"] > 0.5) & (df_ratio["Ratio"] < 2.0)]

    # -----------------------------------------------------------------------
    # Combined chart (difficulty + ratio)
    # -----------------------------------------------------------------------
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.65, 0.35],
        vertical_spacing=0.06,
        subplot_titles=["Mining Difficulty", "Actual / Target Block Time per Period"],
    )

    # — Difficulty line —
    fig.add_trace(
        go.Scatter(
            x=df["Date"], y=df["Difficulty"],
            mode="lines", name="Difficulty",
            line=dict(color="#F7931A", width=2),
        ),
        row=1, col=1,
    )

    # — Adjustment event markers (every data point IS an adjustment) —
    fig.add_trace(
        go.Scatter(
            x=df["Date"], y=df["Difficulty"],
            mode="markers", name="Adjustment event",
            marker=dict(color="#1565C0", size=5, symbol="circle"),
        ),
        row=1, col=1,
    )

    # — Ratio line —
    fig.add_trace(
        go.Scatter(
            x=df_ratio["Date"], y=df_ratio["Ratio"],
            mode="lines+markers", name="Block time ratio",
            line=dict(color="#1976D2", width=1.5),
            marker=dict(size=4),
        ),
        row=2, col=1,
    )

    # Reference line at ratio = 1
    fig.add_hline(
        y=1.0, row=2, col=1,
        line_dash="dash", line_color="red", line_width=1.5,
        annotation_text="Target = 1.0 (600 s avg)",
        annotation_position="bottom right",
    )

    fig.update_layout(
        height=540,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=40),
    )
    fig.update_yaxes(title_text="Difficulty", row=1, col=1)
    fig.update_yaxes(title_text="Ratio", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)

    # -----------------------------------------------------------------------
    # Explanation
    # -----------------------------------------------------------------------
    st.info(
        "**Difficulty adjustment formula** (Bitcoin, §6.1):\n\n"
        "```\nnew_difficulty = old_difficulty × (2016 × 600 s) / actual_period_time\n```\n\n"
        "The ratio chart shows `actual_avg_block_time / 600 s` for each period "
        "(derived as `D[i-1] / D[i]`). "
        "A ratio **< 1** means miners were faster than 10 min → difficulty increased. "
        "A ratio **> 1** means slower → difficulty decreased."
    )

    # -----------------------------------------------------------------------
    # Summary metrics
    # -----------------------------------------------------------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("Current difficulty", f"{df['Difficulty'].iloc[-1]:.3e}")
    growth = df["Difficulty"].iloc[-1] / df["Difficulty"].iloc[0]
    col2.metric(f"Growth over {n_points} periods", f"{growth:.2f}×")
    col3.metric("Adjustment events shown", len(df))

    with st.expander("Raw data table"):
        display_df = df[["Date", "Difficulty", "Ratio"]].copy()
        display_df["Difficulty"] = display_df["Difficulty"].apply(lambda x: f"{x:.3e}")
        display_df["Ratio"] = display_df["Ratio"].apply(
            lambda x: f"{x:.4f}" if pd.notna(x) else "—"
        )
        st.dataframe(display_df, use_container_width=True)
