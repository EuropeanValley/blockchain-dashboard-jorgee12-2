"""M8 - SegWit & Witness Analysis."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def render(blocks: list) -> None:
    st.markdown('<p class="section-label">Witness & Scalability — M8</p>',
                unsafe_allow_html=True)
    
    if not blocks:
        st.warning("No block data available.")
        return

    df = pd.DataFrame(blocks)
    # Calculate weight/size ratio and witness discount
    # SegWit discount: witness data is counted as 1/4 of a byte for weight
    df['witness_ratio'] = (df['weight'] - df['size']) / df['weight']
    
    avg_size = df['size'].mean() / 1e3
    avg_weight = df['weight'].mean() / 1e3
    avg_discount = (1 - (df['size'].mean() / df['weight'].mean())) * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Block Size", f"{avg_size:.1f} KB")
    c2.metric("Avg Weight", f"{avg_weight:.1f} KWU")
    c3.metric("Witness Discount", f"{avg_discount:.1f}%")

    st.markdown("<hr>", unsafe_allow_html=True)

    # Visualization of Size vs Weight over time
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(df))), y=df['size']/1e3,
        mode='lines', name='Size (KB)',
        line=dict(color='#F7931A', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=list(range(len(df))), y=df['weight']/1e3,
        mode='lines', name='Weight (KWU)',
        line=dict(color='#1565C0', width=2, dash='dot')
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk, sans-serif", size=11, color="#8B949E"),
        height=300,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="Block Sequence",
        yaxis_title="Units",
        legend=dict(orientation="h", y=1.1, x=0)
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Cryptographic Context: SegWit"):
        st.markdown(
            """
            **Segregated Witness (SegWit)** separates transaction signatures (witness data) from the 
            transaction data. 
            - **Weight (WU):** A measurement unit where witness data is 4x "cheaper" than non-witness data.
            - **Scale:** This allows Bitcoin blocks to effectively reach up to 4MB in size while maintaining 
            compatibility with the 1MB legacy limit.
            - **Security:** Moving signatures to a separate "witness tree" fixes transaction malleability, 
            enabling Layer 2 solutions like the Lightning Network.
            """
        )
