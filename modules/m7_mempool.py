"""M7 - Mempool & Fee Market."""

import streamlit as st
import plotly.graph_objects as go
from api.blockchain_client import get_mempool_fees, get_mempool_stats

def render() -> None:
    st.markdown('<p class="section-label">Mempool & Fee Market — M7</p>',
                unsafe_allow_html=True)
    
    try:
        fees = get_mempool_fees()
        stats = get_mempool_stats()
    except Exception as e:
        st.error(f"API Error: {e}")
        return

    # ── Fee cards ────────────────────────────────────────────────────────────
    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Fastest (10m)", f"{fees['fastestFee']} sat/vB")
    f2.metric("Half Hour",     f"{fees['halfHourFee']} sat/vB")
    f3.metric("Hour",          f"{fees['hourFee']} sat/vB")
    f4.metric("Minimum",       f"{fees['minimumFee']} sat/vB")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Mempool Stats ────────────────────────────────────────────────────────
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown("#### 📦 Pending Transactions")
        st.write(f"**Count:** {stats['count']:,}")
        st.write(f"**Vsize:** {stats['vsize']/1e6:.2f} MB")
        st.write(f"**Total Fee:** {stats['total_fee']/1e8:.2f} BTC")
        
    with c2:
        # Simple gauge chart for mempool weight
        vsize_mb = stats['vsize']/1e6
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = vsize_mb,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Mempool Vsize (MB)", 'font': {'size': 14}},
            gauge = {
                'axis': {'range': [None, 300], 'tickwidth': 1, 'tickcolor': "#8B949E"},
                'bar': {'color': "#F7931A"},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "rgba(255,255,255,0.1)",
                'steps': [
                    {'range': [0, 100], 'color': 'rgba(102, 187, 106, 0.1)'},
                    {'range': [100, 200], 'color': 'rgba(255, 167, 38, 0.1)'},
                    {'range': [200, 300], 'color': 'rgba(239, 83, 80, 0.1)'}],
            }
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={'color': "#8B949E", 'family': "Space Grotesk, sans-serif"},
            height=200,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, width='stretch')

    st.caption("Data source: mempool.space API. Fees represent the required rate to be included in the next blocks.")
