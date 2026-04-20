"""M2 - Block Header Analyzer.

Parses the 80-byte block header, verifies the Proof of Work locally using
hashlib, and counts leading zero bits in the resulting hash.
"""

import datetime
import hashlib
import struct

import streamlit as st

from api.blockchain_client import get_block, get_block_header_hex, get_tip_hash


# ---------------------------------------------------------------------------
# Cryptographic helpers
# ---------------------------------------------------------------------------

def parse_header(header_hex: str) -> dict:
    """Parse an 80-byte block header from its hex representation.

    Bitcoin header layout (all fields little-endian):
      [0:4]   version      – int32 LE
      [4:36]  prev_hash    – 32 bytes (displayed reversed = big-endian)
      [36:68] merkle_root  – 32 bytes (displayed reversed)
      [68:72] timestamp    – uint32 LE
      [72:76] bits         – uint32 LE  (compact target)
      [76:80] nonce        – uint32 LE
    """
    raw = bytes.fromhex(header_hex)
    if len(raw) != 80:
        raise ValueError(f"Expected 80 bytes, got {len(raw)}")

    version = struct.unpack_from("<i", raw, 0)[0]
    # Hash fields are stored in internal byte order (LE); reverse for display
    prev_hash = raw[4:36][::-1].hex()
    merkle_root = raw[36:68][::-1].hex()
    timestamp = struct.unpack_from("<I", raw, 68)[0]
    bits = struct.unpack_from("<I", raw, 72)[0]
    nonce = struct.unpack_from("<I", raw, 76)[0]

    return {
        "version": version,
        "prev_hash": prev_hash,
        "merkle_root": merkle_root,
        "timestamp": timestamp,
        "bits": bits,
        "nonce": nonce,
    }


def bits_to_target(bits: int) -> int:
    """Decode compact bits representation to 256-bit target."""
    exp = (bits >> 24) & 0xFF
    coeff = bits & 0x007FFFFF
    return coeff * (2 ** (8 * (exp - 3)))


def double_sha256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def verify_pow(header_hex: str) -> dict:
    """Compute SHA256(SHA256(header)) and verify it is below the target.

    Bitcoin stores hashes internally in little-endian order.
    Block explorers (and the API) display them reversed (big-endian).
    We reverse our computed bytes before comparing with the API hash.
    """
    raw = bytes.fromhex(header_hex)
    hash_bytes = double_sha256(raw)                  # internal order (LE)
    hash_display = hash_bytes[::-1].hex()            # reversed for display (BE)

    bits = struct.unpack_from("<I", raw, 72)[0]
    target = bits_to_target(bits)
    hash_int = int(hash_display, 16)
    is_valid = hash_int <= target

    n = hash_int
    leading_zero_bits = 256 - n.bit_length() if n else 256

    return {
        "hash_display": hash_display,
        "target": target,
        "is_valid": is_valid,
        "leading_zero_bits": leading_zero_bits,
    }


# ---------------------------------------------------------------------------
# Streamlit render
# ---------------------------------------------------------------------------

def render() -> None:
    st.header("M2 — Block Header Analyzer")
    st.caption(
        "Inspect the 80-byte block header structure and verify Proof of Work "
        "locally using Python's `hashlib`."
    )

    use_latest = st.checkbox("Use latest block", value=True, key="m2_use_latest")

    if use_latest:
        if st.button("Load latest block", key="m2_load_latest"):
            with st.spinner("Fetching tip hash…"):
                try:
                    st.session_state["m2_hash"] = get_tip_hash()
                except Exception as exc:
                    st.error(f"Error: {exc}")
                    return
        block_hash = st.session_state.get("m2_hash", "")
    else:
        block_hash = st.text_input(
            "Block hash (64 hex chars)",
            placeholder="000000000000000000…",
            key="m2_hash_input",
        )

    if not block_hash:
        st.info("Click 'Load latest block' or enter a block hash to begin.")
        return

    with st.spinner("Fetching block data…"):
        try:
            block = get_block(block_hash)
            header_hex = get_block_header_hex(block_hash)
        except Exception as exc:
            st.error(f"API error: {exc}")
            return

    fields = parse_header(header_hex)
    pow_result = verify_pow(header_hex)
    dt = datetime.datetime.utcfromtimestamp(fields["timestamp"])
    target_hex = f"{pow_result['target']:064x}"

    # -----------------------------------------------------------------------
    # Header fields
    # -----------------------------------------------------------------------
    st.subheader(f"Block #{block['height']:,} — 80-byte Header Fields")

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Version", fields["version"])
        st.metric("Timestamp", dt.strftime("%Y-%m-%d %H:%M:%S UTC"))
        st.metric("Bits (compact target)", f"0x{fields['bits']:08x}")
        st.metric("Nonce", f"{fields['nonce']:,}")
    with c2:
        st.metric("Transaction count", f"{block.get('tx_count', 'N/A'):,}")
        st.metric("Block size", f"{block.get('size', 0):,} bytes")
        st.metric("Leading zero bits", pow_result["leading_zero_bits"])

    st.markdown("**Previous block hash** (byte-reversed from LE storage):")
    st.code(fields["prev_hash"])
    st.markdown("**Merkle root** (byte-reversed from LE storage):")
    st.code(fields["merkle_root"])

    with st.expander("Raw 80-byte header (hex)"):
        st.code(header_hex)
        st.caption(
            "Layout: [version 4B LE][prev_hash 32B LE][merkle_root 32B LE]"
            "[timestamp 4B LE][bits 4B LE][nonce 4B LE]"
        )

    # -----------------------------------------------------------------------
    # Local PoW verification
    # -----------------------------------------------------------------------
    st.subheader("Local Proof-of-Work Verification (hashlib)")

    st.code(
        f"SHA256(SHA256(header))  = {pow_result['hash_display']}\n"
        f"Target threshold        = {target_hex}\n"
        f"API block id            = {block_hash}"
    )

    if pow_result["is_valid"]:
        st.success(
            f"✓ Valid Proof of Work — computed hash < target  "
            f"({pow_result['leading_zero_bits']} leading zero bits)"
        )
    else:
        st.error("✗ Invalid: computed hash ≥ target (unexpected for a real block).")

    st.markdown(
        f"The `bits` field `0x{fields['bits']:08x}` expands to the 256-bit target above. "
        "Any valid block hash must be **numerically smaller** than this value, "
        f"requiring at least **{pow_result['leading_zero_bits']} leading zero bits** "
        "in the SHA-256 output space. "
        "The nonce is the 4-byte value miners increment until the constraint is met."
    )

    # -----------------------------------------------------------------------
    # Byte-order explainer
    # -----------------------------------------------------------------------
    with st.expander("Why byte reversal?"):
        st.markdown(
            """
Bitcoin stores all hash values internally in **little-endian** byte order
(least-significant byte first). When displayed in block explorers and APIs,
they are reversed to produce the familiar **big-endian** hex string.

```
Internal bytes (LE):  b3 a2 ... 00 00 00 00
Display (reversed BE): 00 00 00 00 ... a2 b3
```

When we compute `SHA256(SHA256(raw_header))` we obtain bytes in internal order.
We reverse them (`[::-1].hex()`) before comparing with the API's hash string.
            """
        )
