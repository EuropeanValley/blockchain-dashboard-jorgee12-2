"""M5 - Transaction Explorer."""

import networkx as nx
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from api.blockchain_client import get_block_txs

_CHART_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Space Grotesk, sans-serif", size=11, color="#6E7681"),
    margin=dict(l=8, r=8, t=32, b=8),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", showline=False, zeroline=False),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", showline=False, zeroline=False),
)

@st.cache_data(ttl=60)
def _load_txs(block_hash):
    return get_block_txs(block_hash)

def _build_tx_graph(txs):
    G = nx.DiGraph()
    txid_set = {tx["txid"] for tx in txs}
    for tx in txs:
        out_val   = sum(v.get("value",0) for v in tx.get("vout",[])) / 1e8
        fee       = tx.get("fee") or 0
        vsize     = tx.get("size", 250) or 250
        fee_rate  = fee / vsize
        is_cb     = any(v.get("is_coinbase") for v in tx.get("vin",[]))
        G.add_node(tx["txid"],
                   value=out_val, fee_rate=fee_rate,
                   vsize=vsize, is_coinbase=is_cb,
                   n_in=len(tx.get("vin",[])),
                   n_out=len(tx.get("vout",[])))
    for tx in txs:
        for vin in tx.get("vin",[]):
            src = vin.get("txid","")
            if src in txid_set:
                G.add_edge(src, tx["txid"])
    return G

def _plot_tx_network(txs):
    G   = _build_tx_graph(txs)
    pos = nx.spring_layout(G, k=1.8, seed=42, iterations=60)

    ex, ey = [], []
    for u, v in G.edges():
        x0,y0 = pos[u]; x1,y1 = pos[v]
        ex += [x0,x1,None]; ey += [y0,y1,None]

    nodes     = list(G.nodes(data=True))
    nx_arr    = [pos[n][0] for n,_ in nodes]
    ny_arr    = [pos[n][1] for n,_ in nodes]
    fee_rates = [d.get("fee_rate",0) for _,d in nodes]
    sizes     = [max(8, min(45, d.get("vsize",250)/12)) for _,d in nodes]
    hover     = [
        f"<b>{n[:10]}…</b><br>"
        f"Value: {d.get('value',0):.5f} BTC<br>"
        f"Fee rate: {d.get('fee_rate',0):.2f} sat/vB<br>"
        f"vSize: {d.get('vsize',0)} B<br>"
        f"Inputs: {d.get('n_in',0)}  Outputs: {d.get('n_out',0)}"
        + ("<br><b>⛏ COINBASE</b>" if d.get("is_coinbase") else "")
        for n,d in nodes
    ]

    fig = go.Figure()
    if ex:
        fig.add_trace(go.Scatter(
            x=ex, y=ey, mode="lines",
            line=dict(width=1, color="rgba(247,147,26,0.25)"),
            hoverinfo="none", showlegend=False,
        ))

    cb_idx = [i for i,(n,d) in enumerate(nodes) if d.get("is_coinbase")]
    reg_idx= [i for i,(n,d) in enumerate(nodes) if not d.get("is_coinbase")]

    if reg_idx:
        fig.add_trace(go.Scatter(
            x=[nx_arr[i] for i in reg_idx],
            y=[ny_arr[i] for i in reg_idx],
            mode="markers",
            marker=dict(
                size=[sizes[i] for i in reg_idx],
                color=[fee_rates[i] for i in reg_idx],
                colorscale=[[0,"#0D2137"],[0.4,"#1565C0"],[0.75,"#F7931A"],[1,"#FFEB3B"]],
                showscale=True,
                colorbar=dict(title=dict(text="sat/vB", font=dict(size=9)),
                              thickness=10, tickfont=dict(size=9)),
                line=dict(color="rgba(255,255,255,0.15)", width=0.8),
            ),
            hovertext=[hover[i] for i in reg_idx],
            hoverinfo="text",
            name="Transaction",
        ))

    if cb_idx:
        fig.add_trace(go.Scatter(
            x=[nx_arr[i] for i in cb_idx],
            y=[ny_arr[i] for i in cb_idx],
            mode="markers",
            marker=dict(size=22, color="#F7931A",
                        symbol="star",
                        line=dict(color="#FFEB3B", width=2)),
            hovertext=[hover[i] for i in cb_idx],
            hoverinfo="text",
            name="⛏ Coinbase",
        ))

    fig.update_layout(**{
        **_CHART_LAYOUT,
        "margin": dict(l=0, r=0, t=8, b=0),
        "height": 460,
        "xaxis": dict(showgrid=False, zeroline=False, showticklabels=False),
        "yaxis": dict(showgrid=False, zeroline=False, showticklabels=False),
        "legend": dict(orientation="h", y=-0.02, font=dict(size=10)),
        "hoverlabel": dict(bgcolor="#0D1117", font_size=11),
    })
    return fig

def _plot_tx_bubbles(txs):
    rows = []
    for i, tx in enumerate(txs):
        fee      = tx.get("fee") or 0
        vsize    = tx.get("size", 250) or 250
        out_val  = sum(v.get("value",0) for v in tx.get("vout",[])) / 1e8
        rows.append(dict(
            idx      = i,
            fee_rate = fee / vsize,
            vsize    = vsize,
            n_out    = len(tx.get("vout",[])),
            value    = out_val,
            txid     = tx["txid"][:12] + "…",
            is_cb    = any(v.get("is_coinbase") for v in tx.get("vin",[])),
        ))
    df = pd.DataFrame(rows)
    df = df[~df["is_cb"]]

    fig = go.Figure(go.Scatter(
        x=df["idx"], y=df["fee_rate"],
        mode="markers",
        marker=dict(
            size=np.clip(df["vsize"]/18, 6, 40),
            color=df["n_out"],
            colorscale=[[0,"#1A237E"],[0.5,"#F7931A"],[1,"#FFEB3B"]],
            showscale=True,
            colorbar=dict(title=dict(text="outputs", font=dict(size=9)),
                          thickness=10, tickfont=dict(size=9)),
            opacity=0.8,
            line=dict(color="rgba(255,255,255,0.1)", width=0.5),
        ),
        hovertext=df.apply(
            lambda r: f"<b>{r['txid']}</b><br>fee: {r['fee_rate']:.2f} sat/vB"
                      f"<br>vSize: {r['vsize']} B<br>value: {r['value']:.5f} BTC"
                      f"<br>outputs: {r['n_out']}", axis=1),
        hoverinfo="text",
    ))
    fig.update_layout(
        **_CHART_LAYOUT,
        height=220,
        xaxis_title="Tx index in block",
        yaxis_title="Fee rate (sat/vB)",
        title=dict(text="Fee-rate per transaction  (size=vbytes, color=outputs)",
                   font=dict(size=11), x=0),
    )
    return fig

def render(block_hash: str) -> None:
    st.markdown('<p class="section-label">Transaction Network — block explorer</p>',
                unsafe_allow_html=True)
    with st.spinner("Fetching transactions…"):
        try:
            txs = _load_txs(block_hash)
        except Exception as e:
            st.error(f"Failed to load txs: {e}")
            return

    if txs:
        st.plotly_chart(_plot_tx_network(txs), width='stretch')
        st.plotly_chart(_plot_tx_bubbles(txs), width='stretch')
        st.caption(
            f"Showing {len(txs)} transactions. "
            "Node **size** = virtual bytes · **colour** = fee rate (sat/vB) · "
            "**★** = coinbase · edges = one tx spends another within this block."
        )
    else:
        st.info("No transaction data available for this block.")
