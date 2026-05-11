"""M4 - AI Component: Block Arrival Anomaly Detector."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import scipy.stats as stats
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


@st.cache_data(ttl=120)
def _load(n: int) -> list[dict]:
    return get_recent_blocks(n)


def _detect(times_sec: list[float], alpha: float):
    arr  = np.array(times_sec, dtype=float)
    mu   = float(arr.mean())
    p_s  = stats.expon.sf(arr, scale=mu)
    p_f  = stats.expon.cdf(arr, scale=mu)
    kind = np.where(p_s < alpha, "Slow", np.where(p_f < alpha, "Fast", "Normal"))
    ks_stat, ks_p = stats.kstest(arr, "expon", args=(0, mu))
    df = pd.DataFrame({
        "min":  arr / 60,
        "p_slow": p_s, "p_fast": p_f,
        "type": kind,
        "anomaly": (p_s < alpha) | (p_f < alpha),
    })
    return df, mu, ks_stat, ks_p


def render(blocks: list) -> None:
    st.markdown('<p class="section-label">AI Anomaly Detector & Statistical Prediction — M4</p>', unsafe_allow_html=True)
    
    if not blocks:
        return

    # ── Controls ──────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns([4, 4, 1])
    with c1:
        n = st.slider("Blocks", 50, 300, 100, key="m4_n",
                      label_visibility="collapsed", help="Blocks to analyse")
    with c2:
        alpha = st.slider("Anomaly threshold α", 0.01, 0.10, 0.02, 0.01,
                          key="m4_a", label_visibility="collapsed")
    with c3:
        if st.button("⟳", key="m4_refresh"):
            st.cache_data.clear()

    # ── Fetch ─────────────────────────────────────────────────────────────────
    with st.spinner(""):
        try:
            blocks = _load(n)
        except Exception as e:
            st.error(f"API error: {e}")
            return

    sb = sorted(blocks, key=lambda b: b["height"])
    times = [
        sb[i+1]["timestamp"] - sb[i]["timestamp"]
        for i in range(len(sb) - 1)
        if sb[i+1]["timestamp"] > sb[i]["timestamp"]
    ]
    if len(times) < 10:
        st.warning("Not enough data.")
        return

    df, mu, ks_stat, ks_p = _detect(times, alpha)
    n_anom   = int(df["anomaly"].sum())
    n_slow   = int((df["type"] == "Slow").sum())
    n_fast   = int((df["type"] == "Fast").sum())
    anom_pct = 100 * n_anom / len(df)

    # ── KPI row ───────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Fitted μ",        f"{mu/60:.2f} min")
    k2.metric("Anomalies",       f"{n_anom} / {len(df)}")
    k3.metric("Rate",            f"{anom_pct:.1f}%")
    k4.metric("KS statistic",    f"{ks_stat:.4f}")
    k5.metric("KS p-value",      f"{ks_p:.4f}")

    if ks_p > 0.05:
        st.success(f"KS test p = {ks_p:.3f} > 0.05 — exponential fit is valid. Anomalies are statistically meaningful.")
    else:
        st.warning(f"KS test p = {ks_p:.3f} — marginal fit; data may span multiple difficulty epochs.")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["Distribution + Exp fit", "Anomalies — block sequence"],
        horizontal_spacing=0.08,
    )

    # Histogram
    fig.add_trace(go.Histogram(
        x=df["min"], nbinsx=35,
        histnorm="probability density",
        marker_color="#F7931A", opacity=0.75, name="Observed",
    ), row=1, col=1)

    x_max   = float(df["min"].quantile(0.98)) * 1.1
    xr      = np.linspace(0, x_max, 300)
    pdf_min = stats.expon.pdf(xr * 60, scale=mu) * 60
    fig.add_trace(go.Scatter(
        x=xr, y=pdf_min, mode="lines", name=f"Exp fit μ={mu/60:.1f} min",
        line=dict(color="#42A5F5", width=2),
    ), row=1, col=1)

    # Scatter with anomalies
    color_map = {"Normal": "#F7931A", "Slow": "#EF5350", "Fast": "#66BB6A"}
    for label, color in color_map.items():
        mask = df["type"] == label
        if not mask.any():
            continue
        fig.add_trace(go.Scatter(
            x=df.index[mask].tolist(),
            y=df.loc[mask, "min"].tolist(),
            mode="markers",
            marker=dict(color=color, size=7 if label == "Normal" else 11,
                        symbol="circle" if label == "Normal" else "diamond"),
            name=label,
        ), row=1, col=2)

    upper = -mu * np.log(alpha) / 60
    lower = -mu * np.log(1 - alpha) / 60
    fig.add_hline(y=mu/60,  line_dash="dot",  line_color="#8B949E",  line_width=1,
                  annotation_text=f"μ {mu/60:.1f}", row=1, col=2)
    fig.add_hline(y=upper,  line_dash="dash", line_color="#EF5350",  line_width=1.5,
                  annotation_text=f"slow >{upper:.0f}m", row=1, col=2)
    if lower > 0.5:
        fig.add_hline(y=lower, line_dash="dash", line_color="#66BB6A", line_width=1.5,
                      annotation_text=f"fast <{lower:.1f}m", row=1, col=2)

    fig.update_layout(**_CHART_LAYOUT, height=360, showlegend=True,
                      legend=dict(orientation="h", y=1.08, x=0))
    fig.update_xaxes(title_text="Minutes",     row=1, col=1, gridcolor="#21262D")
    fig.update_xaxes(title_text="Block index", row=1, col=2, gridcolor="#21262D")
    fig.update_yaxes(title_text="Density",     row=1, col=1, gridcolor="#21262D")
    fig.update_yaxes(title_text="Minutes",     row=1, col=2, gridcolor="#21262D")

    st.plotly_chart(fig, width='stretch')

    # ── Anomaly table ─────────────────────────────────────────────────────────
    if n_anom:
        adf = df[df["anomaly"]][["min", "type", "p_slow", "p_fast"]].copy()
        adf["min"]    = adf["min"].round(2)
        adf["p_slow"] = adf["p_slow"].apply(lambda x: f"{x:.4f}")
        adf["p_fast"] = adf["p_fast"].apply(lambda x: f"{x:.4f}")
        adf.columns   = ["Interval (min)", "Type", "P(T>t)", "P(T<t)"]
        st.dataframe(adf, width='stretch')
    else:
        st.success(f"No anomalies at α = {alpha}.")

    with st.expander("Model description"):
        st.markdown(
            r"""
**Model:** Statistical anomaly detection — Exponential distribution baseline.

Mining is a **Poisson process**: each hash attempt succeeds independently with
$p = 1/\text{difficulty}$, so inter-block times follow
$T \sim \text{Exp}(\hat\lambda = 1/\bar x)$ (fitted by MLE).

- **Slow anomaly** — $P(T > t) < \alpha$: unusually long gap.
- **Fast anomaly** — $P(T < t) < \alpha$: unusually short gap.

**Evaluation:** Kolmogorov–Smirnov test against the fitted exponential.
High KS p-value (> 0.05) confirms the model is appropriate.
            """
        )
