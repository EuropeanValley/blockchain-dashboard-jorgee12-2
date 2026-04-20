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
    """Return difficulty history from Blockchain.info charts API.

    Each entry is {"x": unix_timestamp, "y": difficulty_value}.
    """
    r = requests.get(
        f"{BLOCKCHAIN_INFO}/charts/difficulty",
        params={"timespan": "2years", "format": "json", "sampled": "true"},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("values", [])[-n_points:]
