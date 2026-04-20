"""M4 - AI Component: Block Arrival Anomaly Detector.

Model: statistical anomaly detection using an exponential distribution baseline.

Rationale: Bitcoin mining is a Poisson process — each hash attempt succeeds
independently with constant probability, so inter-block times follow an
exponential distribution with mean ~600 s. Deviations from this distribution
may indicate mining pool coordination, hardware outages, or network delays.

Method:
  1. Fetch the last N block timestamps.
  2. Compute inter-arrival times (consecutive block timestamp differences).
  3. Fit an Exponential(λ̂ = 1/x̄) distribution via maximum-likelihood.
  4. For each interval compute the two-tailed p-value:
       p_slow = P(T > t) = exp(-λ̂ t)      [unusually slow block]
       p_fast = P(T < t) = 1 - exp(-λ̂ t)  [unusually fast block]
  5. Flag as anomalous if min(p_slow, p_fast) < threshold.

Evaluation: Kolmogorov–Smirnov goodness-of-fit test against the fitted
exponential; anomaly rate (%) as secondary metric.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import scipy.stats as stats
import streamlit as st

from api.blockchain_client import get_recent_blocks


# ---------------------------------------------------------------------------
# Cached fetch
# ---------------------------------------------------------------------------

@st.cache_data(ttl=120)
def _fetch_blocks(n: int) -> list[dict]:
    return get_recent_blocks(n)


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------

def detect_anomalies(
    inter_times_sec: list[float], threshold: float
) -> tuple[pd.DataFrame, float, float, float, float]:
    """Fit exponential distribution and flag anomalous intervals.

    Returns:
        df          – DataFrame with per-interval results
        mu          – fitted mean (1/λ̂), seconds
        ks_stat     – KS test statistic
        ks_p        – KS test p-value
    """
    arr = np.array(inter_times_sec, dtype=float)
    mu = float(arr.mean())           # MLE: mean of exponential = 1/λ

    # Two-tailed p-values under fitted Exp(λ̂)
    p_slow = stats.expon.sf(arr, scale=mu)    # P(T > t) — too slow
    p_fast = stats.expon.cdf(arr, scale=mu)   # P(T < t) — too fast

    anomaly_slow = p_slow < threshold
    anomaly_fast = p_fast < threshold

    df = pd.DataFrame({
        "interval_sec": arr,
        "interval_min": arr / 60,
        "p_slow": p_slow,
        "p_fast": p_fast,
        "type": np.where(anomaly_slow, "Slow", np.where(anomaly_fast, "Fast", "Normal")),
        "anomaly": anomaly_slow | anomaly_fast,
    })

    # KS test: compare empirical distribution to fitted Exponential
    ks_stat, ks_p = stats.kstest(arr, "expon", args=(0, mu))

    return df, mu, ks_stat, ks_p


# ---------------------------------------------------------------------------
# Streamlit render
# ---------------------------------------------------------------------------

def render() -> None:
    st.header("M4 — AI Component: Anomaly Detector")
    st.caption(
        "Identifies blocks whose inter-arrival time deviates significantly from "
        "the expected exponential distribution."
    )

    with st.expander("Model description", expanded=False):
        st.markdown(
            r"""
**Model:** Statistical anomaly detection using an exponential distribution baseline.

**Rationale:** Bitcoin mining is a **Poisson process** — each of the $~10^{20}$
hash attempts per second succeeds independently with probability
$p = 1/\text{difficulty}$.  By the memoryless property, waiting times between
successes are exponentially distributed:

$$T \sim \text{Exp}(\lambda), \quad \lambda = \frac{p \cdot H}{1} \approx \frac{1}{600\,\text{s}}$$

where $H$ is the network hash rate.

**Method:**

1. Fetch inter-block times for the last $N$ blocks.
2. Estimate $\hat{\lambda} = 1/\bar{x}$ via maximum-likelihood.
3. For each interval $t_i$ compute the two-tailed p-value:
   - $p_{\text{slow}} = P(T > t_i) = e^{-\hat{\lambda} t_i}$
   - $p_{\text{fast}} = P(T < t_i) = 1 - e^{-\hat{\lambda} t_i}$
4. Flag as anomalous if $\min(p_\text{slow}, p_\text{fast}) < \alpha$.

**Evaluation metric:** Kolmogorov–Smirnov (KS) test — compares the empirical
CDF to the fitted exponential CDF.  A high KS p-value confirms the exponential
model is appropriate; anomalous blocks are then meaningful outliers.

**Limitations:** The fitted $\mu$ reflects the *current* epoch's hash rate.
Real anomalies can result from natural tail events, orphaned blocks, pool
pauses, or timestamp manipulation.
            """
        )

    # -----------------------------------------------------------------------
    # Controls
    # -----------------------------------------------------------------------
    col1, col2, col3 = st.columns([3, 3, 1])
    with col1:
        n_blocks = st.slider("Blocks to analyse", 50, 300, 100, key="m4_n")
    with col2:
        threshold = st.slider(
            "Anomaly p-value threshold (α)", 0.01, 0.10, 0.02, step=0.01, key="m4_thresh"
        )
    with col3:
        st.write("")
        if st.button("Refresh", key="m4_refresh"):
            st.cache_data.clear()

    # -----------------------------------------------------------------------
    # Fetch & compute
    # -----------------------------------------------------------------------
    with st.spinner("Fetching blocks…"):
        try:
            blocks = _fetch_blocks(n_blocks)
        except Exception as exc:
            st.error(f"API error: {exc}")
            return

    sorted_blocks = sorted(blocks, key=lambda b: b["height"])
    inter_times = [
        sorted_blocks[i + 1]["timestamp"] - sorted_blocks[i]["timestamp"]
        for i in range(len(sorted_blocks) - 1)
        if sorted_blocks[i + 1]["timestamp"] > sorted_blocks[i]["timestamp"]
    ]

    if len(inter_times) < 10:
        st.warning("Not enough valid inter-block intervals.")
        return

    df, mu, ks_stat, ks_p = detect_anomalies(inter_times, threshold)

    n_anomalies = int(df["anomaly"].sum())
    n_slow = int((df["type"] == "Slow").sum())
    n_fast = int((df["type"] == "Fast").sum())
    anomaly_rate = 100 * n_anomalies / len(df)

    # -----------------------------------------------------------------------
    # Evaluation metrics
    # -----------------------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fitted mean (μ̂)", f"{mu / 60:.2f} min")
    c2.metric("Anomalies", f"{n_anomalies} / {len(df)} ({anomaly_rate:.1f}%)")
    c3.metric("KS statistic", f"{ks_stat:.4f}")
    c4.metric("KS p-value", f"{ks_p:.4f}")

    if ks_p > 0.05:
        st.success(
            f"KS test: inter-block times fit an exponential distribution "
            f"(p = {ks_p:.3f} > 0.05). Anomaly detection is statistically grounded."
        )
    else:
        st.warning(
            f"KS test: marginal fit (p = {ks_p:.3f}). "
            "Data may span multiple difficulty epochs with different λ values."
        )

    # -----------------------------------------------------------------------
    # Distribution chart with exponential fit overlay
    # -----------------------------------------------------------------------
    st.subheader("Inter-Block Time Distribution with Exponential Fit")

    x_max = df["interval_min"].quantile(0.98) * 1.1
    x_range = np.linspace(0, x_max, 300)
    # Convert PDF from per-second to per-minute density
    pdf_per_min = stats.expon.pdf(x_range * 60, scale=mu) * 60

    fig1 = go.Figure()
    fig1.add_trace(go.Histogram(
        x=df["interval_min"],
        nbinsx=40,
        histnorm="probability density",
        marker_color="#F7931A", opacity=0.75,
        name="Observed",
    ))
    fig1.add_trace(go.Scatter(
        x=x_range, y=pdf_per_min,
        mode="lines", name=f"Exp fit (μ = {mu / 60:.1f} min)",
        line=dict(color="#1565C0", width=2.5),
    ))
    fig1.update_layout(
        xaxis_title="Time between blocks (minutes)",
        yaxis_title="Probability density",
        legend=dict(orientation="h"),
        margin=dict(t=20),
    )
    st.plotly_chart(fig1, use_container_width=True)

    # -----------------------------------------------------------------------
    # Anomaly scatter plot
    # -----------------------------------------------------------------------
    st.subheader("Anomaly Detection — Block Sequence")

    color_map = {"Normal": "#F7931A", "Slow": "#D32F2F", "Fast": "#388E3C"}
    fig2 = go.Figure()

    for label, color in color_map.items():
        mask = df["type"] == label
        fig2.add_trace(go.Scatter(
            x=df.index[mask],
            y=df.loc[mask, "interval_min"],
            mode="markers",
            marker=dict(color=color, size=6 if label == "Normal" else 10,
                        symbol="circle" if label == "Normal" else "diamond"),
            name=label,
        ))

    fig2.add_hline(
        y=mu / 60, line_dash="dash", line_color="gray",
        annotation_text=f"μ̂ = {mu / 60:.1f} min",
    )
    # Anomaly thresholds: P(T > t) = α  =>  t = -μ ln(α)
    upper_thresh_min = -mu * np.log(threshold) / 60
    lower_thresh_min = -mu * np.log(1 - threshold) / 60
    fig2.add_hline(
        y=upper_thresh_min, line_dash="dot", line_color="#D32F2F",
        annotation_text=f"Slow threshold: {upper_thresh_min:.1f} min",
        annotation_position="bottom right",
    )
    if lower_thresh_min > 0.3:
        fig2.add_hline(
            y=lower_thresh_min, line_dash="dot", line_color="#388E3C",
            annotation_text=f"Fast threshold: {lower_thresh_min:.1f} min",
            annotation_position="top right",
        )

    fig2.update_layout(
        xaxis_title="Block sequence index",
        yaxis_title="Inter-arrival time (minutes)",
        legend=dict(orientation="h"),
        margin=dict(t=20),
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.caption(
        f"**Slow anomalies** (red ◆): P(T > t) < {threshold} under fitted Exp — "
        f"interval > {upper_thresh_min:.1f} min. "
        f"**Fast anomalies** (green ◆): P(T < t) < {threshold}. "
        f"Threshold derived from α = {threshold}."
    )

    # -----------------------------------------------------------------------
    # Anomaly table
    # -----------------------------------------------------------------------
    if n_anomalies > 0:
        st.subheader(f"Anomalous Intervals ({n_anomalies} detected)")
        anom = df[df["anomaly"]][["interval_min", "type", "p_slow", "p_fast"]].copy()
        anom["interval_min"] = anom["interval_min"].round(2)
        anom["p_slow"] = anom["p_slow"].apply(lambda x: f"{x:.4f}")
        anom["p_fast"] = anom["p_fast"].apply(lambda x: f"{x:.4f}")
        anom = anom.rename(columns={"interval_min": "Interval (min)", "type": "Type"})
        st.dataframe(anom, use_container_width=True)
    else:
        st.success(f"No anomalies detected at α = {threshold}.")

    st.metric("Slow anomalies", n_slow)
    st.metric("Fast anomalies", n_fast)
