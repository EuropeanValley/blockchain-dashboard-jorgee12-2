[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/N3kLi3ZO)
[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=23640768&assignment_repo_type=AssignmentRepo)
# CryptoChain Analyzer Dashboard

Real-time Bitcoin cryptographic metrics dashboard.

## Student Information

| Field | Value |
|---|---|
| Student Name | Jorge Rodrigo Serrano |
| GitHub Username | jorgee12 |
| Project Title | CryptoChain Analyzer Dashboard |
| Chosen AI Approach | M4 — Anomaly Detector (exponential distribution baseline on inter-block times) |

## Module Tracking

| Module | What it should include | Status |
|---|---|---|
| M1 | Proof of Work Monitor | Done |
| M2 | Block Header Analyzer | Done |
| M3 | Difficulty History | Done |
| M4 | AI Component (Anomaly Detector) | Done |

## Current Progress

- M1: fetches last N blocks from Blockstream, shows difficulty, estimated hash rate, leading-zero threshold, and inter-block time histogram with exponential fit reference.
- M2: parses the raw 80-byte block header (version, prev_hash, merkle_root, timestamp, bits, nonce), computes SHA256(SHA256(header)) with hashlib, and verifies the hash is below the target.
- M3: plots Bitcoin difficulty history from Blockchain.info over ~2 years; marks every adjustment event; shows the actual-vs-target block time ratio per period.
- M4: fits an exponential distribution to inter-block times (MLE), flags anomalous blocks via two-tailed p-value, and evaluates goodness of fit with the KS test.
- UX: single-page dark dashboard with transaction network graph, KPI cards, dark Plotly charts.

## Next Step

Write and add the final report PDF to `report/` before the 14 May deadline.

## Main Problem or Blocker

None at the moment.

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

The dashboard auto-refreshes every 60 seconds when the toggle is enabled.

## Project Structure

```
blockchain-dashboard-jorgee12-2/
├── README.md
├── requirements.txt
├── app.py                        # Dashboard entry point (single-page layout)
├── .streamlit/config.toml        # Dark theme configuration
├── api/
│   └── blockchain_client.py      # Blockstream + Blockchain.info helpers
├── modules/
│   ├── m1_pow_monitor.py         # M1: difficulty, hash rate, block time distribution
│   ├── m2_block_header.py        # M2: header parse + hashlib PoW verification
│   ├── m3_difficulty_history.py  # M3: difficulty chart + adjustment ratio
│   └── m4_ai_component.py        # M4: exponential anomaly detector (KS-evaluated)
└── report/                       # Final PDF report (to be added)
```

## APIs Used

| API | URL | Purpose |
|---|---|---|
| Blockstream | `https://blockstream.info/api` | Block data, raw headers, transactions |
| Blockchain.info | `https://blockchain.info` | Difficulty history chart |

<!-- student-repo-auditor:teacher-feedback:start -->
## Teacher Feedback

### Kick-off Review

Review time: 2026-04-20 13:31 CEST
Status: Amber

Strength:
- Your repository keeps the expected classroom structure.

Improve now:
- The README is present but still misses part of the required kickoff information.

Next step:
- Complete the README fields for student information, AI approach, module status, and next step.
<!-- student-repo-auditor:teacher-feedback:end -->
