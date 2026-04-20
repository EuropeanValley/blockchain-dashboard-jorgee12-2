"""
Blockchain API client.

Primary source: Blockstream.info (block data, headers, transactions).
Secondary source: Blockchain.info (difficulty history chart).
"""

import requests

BLOCKSTREAM = "https://blockstream.info/api"
BLOCKCHAIN_INFO = "https://blockchain.info"


def get_tip_hash() -> str:
    r = requests.get(f"{BLOCKSTREAM}/blocks/tip/hash", timeout=10)
    r.raise_for_status()
    return r.text.strip()


def get_tip_height() -> int:
    r = requests.get(f"{BLOCKSTREAM}/blocks/tip/height", timeout=10)
    r.raise_for_status()
    return int(r.text.strip())


def get_block(block_hash: str) -> dict:
    """Return block metadata for the given hash."""
    r = requests.get(f"{BLOCKSTREAM}/block/{block_hash}", timeout=10)
    r.raise_for_status()
    return r.json()


def get_block_header_hex(block_hash: str) -> str:
    """Return the raw 80-byte block header as a hex string."""
    r = requests.get(f"{BLOCKSTREAM}/block/{block_hash}/header", timeout=10)
    r.raise_for_status()
    return r.text.strip()


def get_block_txs(block_hash: str, start_index: int = 0) -> list[dict]:
    """Return up to 25 transactions from a block (one API call)."""
    r = requests.get(f"{BLOCKSTREAM}/block/{block_hash}/txs/{start_index}", timeout=20)
    r.raise_for_status()
    return r.json()


def get_blocks_page(start_height: int) -> list[dict]:
    """Return up to 10 blocks at/below start_height (descending)."""
    r = requests.get(f"{BLOCKSTREAM}/blocks/{start_height}", timeout=15)
    r.raise_for_status()
    return r.json()


def get_recent_blocks(n: int = 50) -> list[dict]:
    """Return the last n blocks in descending height order."""
    tip_height = get_tip_height()
    blocks: list[dict] = []
    height = tip_height
    while len(blocks) < n:
        page = get_blocks_page(height)
        if not page:
            break
        blocks.extend(page)
        height = min(b["height"] for b in page) - 1
    return blocks[:n]


def get_difficulty_history(n_points: int = 150) -> list[dict]:
    """Return difficulty history as list of {"x": timestamp, "y": difficulty}.

    Tries Blockchain.info first; falls back to Blockstream epoch blocks.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 CryptoChain-Dashboard/1.0"}
        r = requests.get(
            f"{BLOCKCHAIN_INFO}/charts/difficulty",
            params={"timespan": "2years", "format": "json", "sampled": "true"},
            headers=headers,
            timeout=15,
        )
        r.raise_for_status()
        if not r.text.strip():
            raise ValueError("Empty response from Blockchain.info")
        data = r.json()
        values = data.get("values", [])
        if values:
            return values[-n_points:]
    except Exception:
        pass  # fall through to Blockstream fallback

    return _difficulty_history_from_blockstream(n_points)


def _difficulty_history_from_blockstream(n_periods: int = 100) -> list[dict]:
    """Build difficulty history by fetching one block per adjustment epoch.

    One epoch = 2016 blocks ≈ 2 weeks.  Makes n_periods API calls — cached
    by the caller for 1 hour so this is only slow on the first load.
    """
    tip_height = get_tip_height()
    # Height of the most recent completed adjustment epoch
    current_epoch = tip_height - (tip_height % 2016)

    results: list[dict] = []
    for i in range(n_periods):
        epoch_height = current_epoch - i * 2016
        if epoch_height < 0:
            break
        try:
            page = get_blocks_page(epoch_height)
            if not page:
                continue
            # page is descending; take the block closest to epoch_height
            block = max(page, key=lambda b: b["height"])
            results.append({"x": block["timestamp"], "y": block["difficulty"]})
        except Exception:
            continue

    return sorted(results, key=lambda d: d["x"])
