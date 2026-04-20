"""CryptoChain Analyzer Dashboard — single-page entry point.

Run with:  streamlit run app.py
"""

import time, datetime, statistics, hashlib, struct

import networkx as nx
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import scipy.stats as stats
import streamlit as st
from plotly.subplots import make_subplots

from api.blockchain_client import (
    get_recent_blocks, get_tip_hash, get_block,
    get_block_header_hex, get_block_txs, get_difficulty_history,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CryptoChain Analyzer",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu,footer,header,.stDeployButton{display:none!important}
.block-container{padding:0.8rem 2rem 1rem 2rem}

/* KPI cards */
[data-testid="metric-container"]{
  background:#0D1117;border:1px solid #21262D;
  border-radius:10px;padding:16px 18px 12px;
}
[data-testid="stMetricValue"]{
  color:#F7931A;font-size:1.45rem!important;font-weight:700;
}
[data-testid="stMetricLabel"]{
  color:#6E7681;font-size:.72rem!important;
  text-transform:uppercase;letter-spacing:.06em;
}

/* Section dividers */
hr{border:none;border-top:1px solid #21262D;margin:.6rem 0}

/* Expanders */
.streamlit-expanderHeader{
  background:#0D1117!important;border:1px solid #21262D!important;
  border-radius:8px!important;color:#6E7681!important;font-size:.82rem!important;
}
.streamlit-expanderContent{
  background:#0D1117!important;border:1px solid #21262D!important;
  border-top:none!important;border-radius:0 0 8px 8px!important;
}

/* Code */
code,.stCode{background:#070B0F!important;border:1px solid #21262D;
  font-size:.78rem!important;}

/* Alert boxes */
.stAlert{border-radius:8px;border-left-width:3px}

/* Section labels */
.section-label{
  color:#6E7681;font-size:.7rem;text-transform:uppercase;
  letter-spacing:.1em;margin-bottom:.2rem;
}
</style>
""", unsafe_allow_html=True)

# ── Shared Plotly base layout ─────────────────────────────────────────────────
_DARK = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="sans-serif", size=11, color="#6E7681"),
    margin=dict(l=8, r=8, t=32, b=8),
    xaxis=dict(gridcolor="#161B22", showline=False, zeroline=False),
    yaxis=dict(gridcolor="#161B22", showline=False, zeroline=False),
)

# ════════════════════════════════════════════════════════════════════════════
# Cached data loaders
# ════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=30)
def load_tip_block():
    tip = get_tip_hash()
    return tip, get_block(tip), get_block_header_hex(tip)

@st.cache_data(ttl=60)
def load_recent_blocks(n):
    return get_recent_blocks(n)

@st.cache_data(ttl=60)
def load_txs(block_hash):
    return get_block_txs(block_hash)

@st.cache_data(ttl=3600)
def load_difficulty(n):
    return get_difficulty_history(n)

# ════════════════════════════════════════════════════════════════════════════
# Helper — PoW
# ════════════════════════════════════════════════════════════════════════════

def _bits_to_target(bits):
    exp, coeff = (bits >> 24) & 0xFF, bits & 0x007FFFFF
    return coeff * (2 ** (8 * (exp - 3)))

def _leading_zeros(h): return 256 - int(h,16).bit_length() if int(h,16) else 256

def _verify_pow(header_hex):
    raw  = bytes.fromhex(header_hex)
    h    = hashlib.sha256(hashlib.sha256(raw).digest()).digest()[::-1].hex()
    bits = struct.unpack_from("<I", raw, 72)[0]
    tgt  = _bits_to_target(bits)
    return h, tgt, int(h,16) <= tgt, _leading_zeros(h)

def _parse_header(header_hex):
    raw = bytes.fromhex(header_hex)
    return dict(
        version   = struct.unpack_from("<i", raw, 0)[0],
        prev_hash = raw[4:36][::-1].hex(),
        merkle_root=raw[36:68][::-1].hex(),
        timestamp = struct.unpack_from("<I", raw, 68)[0],
        bits      = struct.unpack_from("<I", raw, 72)[0],
        nonce     = struct.unpack_from("<I", raw, 76)[0],
    )

# ════════════════════════════════════════════════════════════════════════════
# Helper — transaction network graph
# ════════════════════════════════════════════════════════════════════════════

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

    # Edges
    ex, ey = [], []
    for u, v in G.edges():
        x0,y0 = pos[u]; x1,y1 = pos[v]
        ex += [x0,x1,None]; ey += [y0,y1,None]

    nodes     = list(G.nodes(data=True))
    nx_arr    = [pos[n][0] for n,_ in nodes]
    ny_arr    = [pos[n][1] for n,_ in nodes]
    fee_rates = [d.get("fee_rate",0) for _,d in nodes]
    sizes     = [max(8, min(45, d.get("vsize",250)/12)) for _,d in nodes]
    is_cb     = [d.get("is_coinbase",False) for _,d in nodes]
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

    # Coinbase node (special)
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
                colorbar=dict(title="sat/vB", thickness=10,
                              tickfont=dict(size=9), titlefont=dict(size=9)),
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

    fig.update_layout(
        **{**_DARK, "margin": dict(l=0,r=0,t=8,b=0)},
        height=460,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        legend=dict(orientation="h", y=-0.02, font=dict(size=10)),
        hoverlabel=dict(bgcolor="#0D1117", font_size=11),
    )
    return fig


def _plot_tx_bubbles(txs):
    """Fee-rate bubble chart: size=vsize, color=n_outputs, y=fee rate."""
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
    df = df[~df["is_cb"]]  # drop coinbase for fee chart

    fig = go.Figure(go.Scatter(
        x=df["idx"], y=df["fee_rate"],
        mode="markers",
        marker=dict(
            size=np.clip(df["vsize"]/18, 6, 40),
            color=df["n_out"],
            colorscale=[[0,"#1A237E"],[0.5,"#F7931A"],[1,"#FFEB3B"]],
            showscale=True,
            colorbar=dict(title="outputs", thickness=10,
                          tickfont=dict(size=9), titlefont=dict(size=9)),
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
        **_DARK,
        height=220,
        xaxis_title="Tx index in block",
        yaxis_title="Fee rate (sat/vB)",
        title=dict(text="Fee-rate per transaction  (size=vbytes, color=outputs)",
                   font=dict(size=11), x=0),
    )
    return fig

# ════════════════════════════════════════════════════════════════════════════
# Header
# ════════════════════════════════════════════════════════════════════════════

hdr_l, hdr_r = st.columns([5, 3])
with hdr_l:
    st.markdown("### ₿ &nbsp;CryptoChain Analyzer")
with hdr_r:
    rc1, rc2, rc3 = st.columns([3, 3, 2])
    with rc1:
        auto = st.toggle("Auto-refresh 60 s", key="auto")
    with rc2:
        if st.button("⟳ &nbsp;Refresh all", key="ref_all"):
            st.cache_data.clear()
    with rc3:
        st.caption(datetime.datetime.utcnow().strftime("%H:%M:%S UTC"))

st.markdown("<hr>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# Load core data
# ════════════════════════════════════════════════════════════════════════════

with st.spinner("Fetching latest block…"):
    try:
        tip_hash, tip_block, header_hex = load_tip_block()
    except Exception as e:
        st.error(f"Cannot reach Blockstream API: {e}")
        st.stop()

fields   = _parse_header(header_hex)
h_hash, h_target, h_valid, h_lz = _verify_pow(header_hex)
bits     = fields["bits"]
diff     = tip_block["difficulty"]
hr_eh    = diff * (2**32) / 600 / 1e18
dt       = datetime.datetime.utcfromtimestamp(fields["timestamp"])
tgt_hex  = f"{h_target:064x}"

# ════════════════════════════════════════════════════════════════════════════
# KPI bar
# ════════════════════════════════════════════════════════════════════════════

k1,k2,k3,k4,k5,k6 = st.columns(6)
k1.metric("Block height",      f"{tip_block['height']:,}")
k2.metric("Difficulty",        f"{diff:.3e}")
k3.metric("Hash rate",         f"{hr_eh:.2f} EH/s")
k4.metric("Leading zero bits", h_lz)
k5.metric("Transactions",      f"{tip_block.get('tx_count',0):,}")
k6.metric("Block time",        dt.strftime("%H:%M UTC"))

st.markdown("<hr>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# Section 1 — Transaction Network  |  Block Header
# ════════════════════════════════════════════════════════════════════════════

col_net, col_hdr = st.columns([6, 4], gap="large")

with col_net:
    st.markdown('<p class="section-label">Transaction Network — latest block</p>',
                unsafe_allow_html=True)
    with st.spinner("Fetching transactions…"):
        try:
            txs = load_txs(tip_hash)
        except Exception as e:
            txs = []
            st.warning(f"Tx fetch failed: {e}")

    if txs:
        st.plotly_chart(_plot_tx_network(txs), use_container_width=True)
        st.plotly_chart(_plot_tx_bubbles(txs), use_container_width=True)
        st.caption(
            f"Showing {len(txs)} transactions. "
            "Node **size** = virtual bytes · **colour** = fee rate (sat/vB) · "
            "**★** = coinbase · edges = one tx spends another within this block."
        )
    else:
        st.info("No transaction data available.")

with col_hdr:
    st.markdown('<p class="section-label">Block Header Analyzer — M2</p>',
                unsafe_allow_html=True)

    # PoW verification
    if h_valid:
        st.success(f"✓ Valid PoW — {h_lz} leading zero bits")
    else:
        st.error("✗ Invalid PoW")

    st.code(
        f"Computed  {h_hash}\n"
        f"Target    {tgt_hex}",
        language=None,
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    # Fields grid
    fa, fb = st.columns(2)
    with fa:
        st.metric("Version",  fields["version"])
        st.metric("Nonce",    f"{fields['nonce']:,}")
        st.metric("bits",     f"0x{bits:08x}")
    with fb:
        st.metric("Size",     f"{tip_block.get('size',0):,} B")
        st.metric("Weight",   f"{tip_block.get('weight',0):,} WU")
        st.metric("Timestamp", dt.strftime("%H:%M UTC"))

    st.markdown("**Prev hash**")
    st.code(fields["prev_hash"][:32]+"…", language=None)
    st.markdown("**Merkle root**")
    st.code(fields["merkle_root"][:32]+"…", language=None)

    with st.expander("Full hashes + byte-order note"):
        st.code(
            f"prev_hash:\n{fields['prev_hash']}\n\n"
            f"merkle_root:\n{fields['merkle_root']}\n\n"
            f"raw header:\n{header_hex}",
            language=None,
        )
        st.caption(
            "All hash fields stored little-endian internally, reversed for display. "
            "SHA256(SHA256(header)) computed with Python `hashlib`."
        )

st.markdown("<hr>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# Section 2 — PoW Monitor (M1)  |  Difficulty History (M3)
# ════════════════════════════════════════════════════════════════════════════

col_m1, col_m3 = st.columns([5, 5], gap="large")

# ── M1 ────────────────────────────────────────────────────────────────────
with col_m1:
    st.markdown('<p class="section-label">Proof-of-Work Monitor — M1</p>',
                unsafe_allow_html=True)
    n_blocks = st.slider("Blocks", 20, 150, 50, key="m1_n",
                         label_visibility="collapsed")
    with st.spinner(""):
        try:
            blocks = load_recent_blocks(n_blocks)
        except Exception as e:
            st.error(f"{e}"); blocks = []

    if blocks:
        sb = sorted(blocks, key=lambda b: b["height"])
        times_min = [
            (sb[i+1]["timestamp"] - sb[i]["timestamp"]) / 60
            for i in range(len(sb)-1)
            if sb[i+1]["timestamp"] > sb[i]["timestamp"]
        ]
        mean_m  = sum(times_min)/len(times_min) if times_min else 10
        stdev_m = statistics.stdev(times_min) if len(times_min)>1 else 0

        ma, mb = st.columns(2)
        ma.metric("Mean block time", f"{mean_m:.2f} min")
        mb.metric("Stdev",           f"{stdev_m:.2f} min")

        fig_m1 = make_subplots(rows=2, cols=1,
                               subplot_titles=["Inter-block times", "Sequence"],
                               vertical_spacing=0.12, row_heights=[0.55, 0.45])
        fig_m1.add_trace(go.Histogram(x=times_min, nbinsx=28,
                                      marker_color="#F7931A", opacity=0.8),
                         row=1, col=1)
        fig_m1.add_trace(go.Scatter(x=list(range(len(times_min))), y=times_min,
                                    mode="lines",
                                    line=dict(color="#F7931A", width=1.2)),
                         row=2, col=1)
        fig_m1.add_hline(y=10,     line_dash="dash", line_color="#EF5350",
                         line_width=1.5, row=2, col=1)
        fig_m1.add_hline(y=mean_m, line_dash="dot",  line_color="#66BB6A",
                         line_width=1.5, row=2, col=1)
        fig_m1.update_layout(**_DARK, height=380, showlegend=False)
        fig_m1.update_xaxes(gridcolor="#161B22")
        fig_m1.update_yaxes(gridcolor="#161B22")
        st.plotly_chart(fig_m1, use_container_width=True)

        st.caption(
            "Inter-block times follow an **exponential distribution** (memoryless Poisson "
            "process). Each hash attempt is independent — the target mean is **10 min**."
        )

# ── M3 ────────────────────────────────────────────────────────────────────
with col_m3:
    st.markdown('<p class="section-label">Difficulty History — M3</p>',
                unsafe_allow_html=True)
    n_periods = st.slider("Periods", 30, 200, 90, key="m3_n",
                          label_visibility="collapsed")
    with st.spinner(""):
        try:
            d_vals = load_difficulty(n_periods)
        except Exception as e:
            st.error(f"{e}"); d_vals = []

    if d_vals:
        df3 = (pd.DataFrame(d_vals)
               .assign(Date=lambda d: pd.to_datetime(d["x"], unit="s"),
                       Diff=lambda d: d["y"])
               .sort_values("Date").reset_index(drop=True))
        df3["Ratio"] = df3["Diff"].shift(1) / df3["Diff"]
        dr = df3.dropna(subset=["Ratio"])
        dr = dr[(dr["Ratio"]>0.5)&(dr["Ratio"]<2.0)]

        c_d, c_r = st.columns(2)
        c_d.metric("Current",         f"{df3['Diff'].iloc[-1]:.3e}")
        c_r.metric("Last adj. ratio", f"{dr['Ratio'].iloc[-1]:.4f}" if len(dr) else "—")

        fig_m3 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                               vertical_spacing=0.08, row_heights=[0.62, 0.38],
                               subplot_titles=["Difficulty", "Actual/Target ratio"])
        fig_m3.add_trace(go.Scatter(x=df3["Date"], y=df3["Diff"],
                                    mode="lines", line=dict(color="#F7931A", width=1.8),
                                    fill="tozeroy",
                                    fillcolor="rgba(247,147,26,0.06)"),
                         row=1, col=1)
        fig_m3.add_trace(go.Scatter(x=df3["Date"], y=df3["Diff"],
                                    mode="markers",
                                    marker=dict(color="#1565C0", size=4)),
                         row=1, col=1)
        fig_m3.add_trace(go.Scatter(x=dr["Date"], y=dr["Ratio"],
                                    mode="lines",
                                    line=dict(color="#42A5F5", width=1.4),
                                    fill="tozeroy",
                                    fillcolor="rgba(66,165,245,0.06)"),
                         row=2, col=1)
        fig_m3.add_hline(y=1.0, row=2, col=1,
                         line_dash="dash", line_color="#EF5350", line_width=1.2)
        fig_m3.update_layout(**_DARK, height=380, showlegend=False)
        fig_m3.update_xaxes(gridcolor="#161B22")
        fig_m3.update_yaxes(gridcolor="#161B22")
        st.plotly_chart(fig_m3, use_container_width=True)

        with st.expander("Formula"):
            st.code("new_D = old_D × (2016 × 600 s) / actual_period", language=None)
            st.caption("Ratio = D[i-1]/D[i] ≈ actual avg / 600 s target")

st.markdown("<hr>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# Section 3 — AI Anomaly Detector (M4, full width)
# ════════════════════════════════════════════════════════════════════════════

st.markdown('<p class="section-label">AI Anomaly Detector — M4 &nbsp;·&nbsp; Exponential baseline</p>',
            unsafe_allow_html=True)

a_col, b_col = st.columns([2, 1])
with a_col:
    n_m4 = st.slider("Blocks for anomaly detection", 50, 300, 100,
                     key="m4_n", label_visibility="collapsed")
with b_col:
    alpha = st.slider("α threshold", 0.01, 0.10, 0.02, 0.01,
                      key="m4_a", label_visibility="collapsed")

# reuse already-loaded blocks if possible
with st.spinner(""):
    try:
        m4_blocks = load_recent_blocks(n_m4)
    except Exception as e:
        st.error(f"{e}"); m4_blocks = []

if m4_blocks:
    sb4 = sorted(m4_blocks, key=lambda b: b["height"])
    t4  = [sb4[i+1]["timestamp"]-sb4[i]["timestamp"]
           for i in range(len(sb4)-1)
           if sb4[i+1]["timestamp"] > sb4[i]["timestamp"]]

    if len(t4) >= 10:
        arr  = np.array(t4, dtype=float)
        mu   = float(arr.mean())
        ps   = stats.expon.sf(arr, scale=mu)
        pf   = stats.expon.cdf(arr, scale=mu)
        kind = np.where(ps<alpha,"Slow", np.where(pf<alpha,"Fast","Normal"))
        df4  = pd.DataFrame({"min":arr/60,"p_slow":ps,"p_fast":pf,"type":kind,
                              "anomaly":(ps<alpha)|(pf<alpha)})
        ks_s, ks_p = stats.kstest(arr,"expon",args=(0,mu))

        n_an = int(df4["anomaly"].sum())
        n4a, n4b, n4c, n4d = st.columns(4)
        n4a.metric("Fitted μ",      f"{mu/60:.2f} min")
        n4b.metric("Anomalies",     f"{n_an}/{len(df4)}")
        n4c.metric("KS statistic",  f"{ks_s:.4f}")
        n4d.metric("KS p-value",    f"{ks_p:.4f}")

        if ks_p > 0.05:
            st.success(f"KS p={ks_p:.3f} > 0.05 — exponential fit valid.")
        else:
            st.warning(f"KS p={ks_p:.3f} — marginal fit (may span multiple epochs).")

        fig_m4 = make_subplots(rows=1, cols=2,
                               subplot_titles=["Distribution + Exp fit",
                                               "Anomalies — block sequence"],
                               horizontal_spacing=0.06)

        x_max  = float(df4["min"].quantile(0.97))*1.1
        xr     = np.linspace(0, x_max, 300)
        pdf_m  = stats.expon.pdf(xr*60, scale=mu)*60
        fig_m4.add_trace(go.Histogram(x=df4["min"], nbinsx=32,
                                      histnorm="probability density",
                                      marker_color="#F7931A", opacity=0.72),
                         row=1, col=1)
        fig_m4.add_trace(go.Scatter(x=xr, y=pdf_m, mode="lines",
                                    line=dict(color="#42A5F5", width=2)),
                         row=1, col=1)

        cmap = {"Normal":"#F7931A","Slow":"#EF5350","Fast":"#66BB6A"}
        for lbl, color in cmap.items():
            mask = df4["type"]==lbl
            if not mask.any(): continue
            fig_m4.add_trace(go.Scatter(
                x=df4.index[mask].tolist(), y=df4.loc[mask,"min"].tolist(),
                mode="markers",
                marker=dict(color=color,
                            size=6 if lbl=="Normal" else 11,
                            symbol="circle" if lbl=="Normal" else "diamond"),
                name=lbl,
            ), row=1, col=2)

        upper = -mu*np.log(alpha)/60
        fig_m4.add_hline(y=mu/60, line_dash="dot", line_color="#6E7681",
                         line_width=1, row=1, col=2)
        fig_m4.add_hline(y=upper, line_dash="dash", line_color="#EF5350",
                         line_width=1.2, row=1, col=2,
                         annotation_text=f"slow>{upper:.0f}m")

        fig_m4.update_layout(**_DARK, height=300, showlegend=True,
                             legend=dict(orientation="h", y=1.05, font=dict(size=10)))
        fig_m4.update_xaxes(gridcolor="#161B22")
        fig_m4.update_yaxes(gridcolor="#161B22")
        st.plotly_chart(fig_m4, use_container_width=True)

        with st.expander("Model"):
            st.markdown(
                r"Mining is a Poisson process → $T \sim \text{Exp}(\hat\lambda=1/\bar x)$ (MLE)."
                " Anomaly: $\min(P(T>t),\, P(T<t)) < \alpha$."
                " Evaluated with Kolmogorov–Smirnov test."
            )

# ── Auto-refresh ─────────────────────────────────────────────────────────────
if auto:
    time.sleep(60)
    st.rerun()
