"""M6 - Security Score."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from api.blockchain_client import get_tip_hash, get_block

_CHART_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="sans-serif", size=11, color="#6E7681"),
    margin=dict(l=8, r=8, t=32, b=8),
    xaxis=dict(gridcolor="#161B22", showline=False, zeroline=False),
    yaxis=dict(gridcolor="#161B22", showline=False, zeroline=False),
)

def _nakamoto_prob(q, z):
    """Nakamoto 2008, Section 11: Probability of an attacker catching up.
    q: attacker's share of network hashrate (0 < q < 0.5)
    z: number of confirmations
    """
    p = 1.0 - q
    lambda_val = z * (q / p)
    import math
    from scipy.special import gammaincc
    
    # Summation formula for Poisson distribution (Nakamoto §11)
    # sum_{k=0}^{z} [ (lambda^k * exp(-lambda)) / k! ] * [ 1 - (q/p)^(z-k) ]
    prob = 1.0
    sum_val = 0
    for k in range(z + 1):
        poisson = (math.pow(lambda_val, k) * math.exp(-lambda_val)) / math.factorial(k)
        sum_val += poisson * (1.0 - math.pow(q / p, z - k))
    
    return 1.0 - sum_val

def render() -> None:
    st.markdown('<p class="section-label">Security Score — M6 &nbsp;·&nbsp; Nakamoto Analysis</p>',
                unsafe_allow_html=True)
    
    # ── KPI Data ─────────────────────────────────────────────────────────────
    tip_hash = get_tip_hash()
    block = get_block(tip_hash)
    difficulty = block["difficulty"]
    # Estimate hashrate (EH/s)
    hr_eh = difficulty * (2**32) / 600 / 1e18

    # ── 51% Attack Cost Estimation ───────────────────────────────────────────
    st.markdown("### ⚡ 51% Attack Cost (Estimation)")
    
    col1, col2, col3 = st.columns(3)
    
    # Assumptions (typical 2024-2025 hardware)
    # Antminer S21 Pro (~234 TH/s, 3500W, ~$4500)
    miner_hr_th = 234.0
    miner_power_w = 3500.0
    electricity_cost_kwh = st.sidebar.slider("Electricity Cost ($/kWh)", 0.01, 0.20, 0.05, 0.01, key="elec_cost")
    
    total_miners_needed = (hr_eh * 1e6) / miner_hr_th
    total_power_gw = (total_miners_needed * miner_power_w) / 1e9
    
    elec_cost_hour = total_power_gw * 1e6 * electricity_cost_kwh
    hardware_cost_bn = (total_miners_needed * 4500) / 1e9

    col1.metric("Network Hashrate", f"{hr_eh:.2f} EH/s")
    col2.metric("Elec. Cost / Hour", f"${elec_cost_hour/1e6:.2f}M")
    col3.metric("Hardware CapEx", f"${hardware_cost_bn:.1f}B")
    
    st.caption(
        f"Estimated using **{total_miners_needed/1e6:.1f}M** Antminer S21 Pro units. "
        f"Consumes **{total_power_gw:.2f} GW** of electricity (approx. {total_power_gw/1.5:.1f} nuclear plants)."
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Nakamoto Probabilities ───────────────────────────────────────────────
    st.markdown("### 📉 Double-Spend Probability (Nakamoto 2008)")
    
    q_slider = st.slider("Attacker relative hashrate (q)", 0.05, 0.45, 0.25, 0.05, help="Proportion of total network hashrate controlled by attacker.")
    
    z_range = list(range(1, 13))
    probs = [_nakamoto_prob(q_slider, z) for z in z_range]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=z_range, y=probs,
        mode="lines+markers",
        line=dict(color="#EF5350", width=3),
        marker=dict(size=8, color="#EF5350", line=dict(width=1, color="white")),
        name="Success Prob."
    ))
    
    fig.update_layout(
        **_CHART_LAYOUT,
        height=300,
        xaxis_title="Confirmations (z)",
        yaxis_title="P(success)",
        title=dict(text=f"Probability of successful double-spend (q={q_slider:.2f})", font=dict(size=12)),
    )
    fig.update_yaxes(type="log", range=[-4, 0], gridcolor="#161B22")
    st.plotly_chart(fig, use_container_width=True)
    
    st.info(
        "As $z$ (confirmations) increases, the probability of an attacker with hashrate $q < 0.5$ "
        "catching up to the main chain drops exponentially. For $q=0.25$, 6 confirmations reduce "
        "risk to below 1%."
    )
    
    with st.expander("Theoretical Reference"):
        st.markdown(
            r"""
            **Nakamoto (2008) §11:** "The race between the honest chain and an attacker chain can be characterized 
            as a Binomial Random Walk. The probability of an attacker catching up from $z$ blocks behind is:"
            $$P = \begin{cases} 1 & \text{if } q \ge p \\ (q/p)^z & \text{if } q < p \end{cases}$$
            *Note: The actual calculation uses a Poisson distribution to account for the honest chain's progress.*
            """
        )
