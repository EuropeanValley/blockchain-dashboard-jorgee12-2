"""M2 - Block Header Analyzer."""

import datetime
import hashlib
import struct

import streamlit as st

from api.blockchain_client import get_block, get_block_header_hex, get_tip_hash


def _parse(header_hex: str) -> dict:
    raw = bytes.fromhex(header_hex)
    if len(raw) != 80:
        raise ValueError(f"Expected 80 bytes, got {len(raw)}")
    return {
        "version":    struct.unpack_from("<i", raw, 0)[0],
        "prev_hash":  raw[4:36][::-1].hex(),
        "merkle_root":raw[36:68][::-1].hex(),
        "timestamp":  struct.unpack_from("<I", raw, 68)[0],
        "bits":       struct.unpack_from("<I", raw, 72)[0],
        "nonce":      struct.unpack_from("<I", raw, 76)[0],
    }


def _bits_to_target(bits: int) -> int:
    exp, coeff = (bits >> 24) & 0xFF, bits & 0x007FFFFF
    return coeff * (2 ** (8 * (exp - 3)))


def _verify(header_hex: str) -> dict:
    raw   = bytes.fromhex(header_hex)
    h     = hashlib.sha256(hashlib.sha256(raw).digest()).digest()[::-1].hex()
    bits  = struct.unpack_from("<I", raw, 72)[0]
    tgt   = _bits_to_target(bits)
    valid = int(h, 16) <= tgt
    lz    = 256 - int(h, 16).bit_length() if int(h, 16) else 256
    return {"hash": h, "target": tgt, "valid": valid, "leading_zeros": lz}


@st.cache_data(ttl=30)
def _load_latest() -> tuple[str, dict, str, dict]:
    tip   = get_tip_hash()
    block = get_block(tip)
    hdr   = get_block_header_hex(tip)
    return tip, block, hdr, _verify(hdr)


def render() -> None:
    # ── Load controls ────────────────────────────────────────────────────────
    col_mode, col_inp, col_btn = st.columns([2, 5, 1])
    with col_mode:
        use_latest = st.toggle("Latest block", value=True, key="m2_latest")
    with col_inp:
        manual_hash = st.text_input("Block hash", placeholder="64-char hex",
                                    key="m2_inp", label_visibility="collapsed",
                                    disabled=use_latest)
    with col_btn:
        refresh = st.button("⟳", key="m2_refresh", help="Reload")
        if refresh:
            st.cache_data.clear()

    # ── Fetch ────────────────────────────────────────────────────────────────
    if use_latest:
        with st.spinner(""):
            try:
                block_hash, block, header_hex, pow_r = _load_latest()
            except Exception as e:
                st.error(f"API error: {e}")
                return
    else:
        block_hash = manual_hash.strip()
        if not block_hash:
            st.info("Enter a block hash above.")
            return
        with st.spinner(""):
            try:
                block      = get_block(block_hash)
                header_hex = get_block_header_hex(block_hash)
                pow_r      = _verify(header_hex)
            except Exception as e:
                st.error(f"API error: {e}")
                return

    fields = _parse(header_hex)
    dt     = datetime.datetime.fromtimestamp(fields["timestamp"], datetime.UTC)

    # ── KPI row ──────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Height",          f"{block['height']:,}")
    k2.metric("Version",         fields["version"])
    k3.metric("Nonce",           f"{fields['nonce']:,}")
    k4.metric("Transactions",    f"{block.get('tx_count', '—'):,}")
    k5.metric("Leading zero bits", pow_r["leading_zeros"])

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── PoW verification (prominent) ─────────────────────────────────────────
    st.markdown("**Local Proof-of-Work verification** — `SHA256(SHA256(header))`")

    tgt_hex = f"{pow_r['target']:064x}"
    st.code(
        f"Computed  {pow_r['hash']}\n"
        f"Target    {tgt_hex}\n"
        f"API id    {block_hash}",
        language=None,
    )

    if pow_r["valid"]:
        st.success(f"✓  Hash < target  ·  {pow_r['leading_zeros']} leading zero bits  ·  Proof of Work valid")
    else:
        st.error("✗  Hash ≥ target — unexpected for a real block.")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Header field grid ────────────────────────────────────────────────────
    st.markdown(f"**Header fields** — block #{block['height']:,} &nbsp; · &nbsp; {dt.strftime('%Y-%m-%d %H:%M UTC')}")

    fl, fr = st.columns(2)
    with fl:
        st.markdown("**Timestamp**")
        st.code(dt.strftime("%Y-%m-%d %H:%M:%S UTC"), language=None)
        st.markdown("**Bits (compact target)**")
        st.code(f"0x{fields['bits']:08x}", language=None)
        st.markdown("**Block size / weight**")
        st.code(f"{block.get('size',0):,} B  ·  {block.get('weight',0):,} WU", language=None)

    with fr:
        st.markdown("**Previous block hash**")
        st.code(fields["prev_hash"], language=None)
        st.markdown("**Merkle root**")
        st.code(fields["merkle_root"], language=None)

    with st.expander("Raw 80-byte header + byte-order note"):
        st.code(header_hex, language=None)
        st.caption(
            "[version 4B LE][prev_hash 32B LE][merkle_root 32B LE]"
            "[timestamp 4B LE][bits 4B LE][nonce 4B LE]  "
            "— hash fields are stored little-endian internally and reversed for display."
        )
