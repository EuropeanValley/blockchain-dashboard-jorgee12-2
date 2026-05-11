111[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/N3kLi3ZO)
[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=23640768&assignment_repo_type=AssignmentRepo)
# CryptoChain Analyzer Dashboard

Real-time Bitcoin cryptographic metrics dashboard.

## Student Information
- **Name:** Jorge Rodrigo Serrano
- **GitHub Username:** jorgee12-2

## Project Title
CryptoChain Analyzer Dashboard

## Chosen AI Approach
**M4 — Anomaly Detector:** Using a statistical baseline (Exponential distribution) to identify anomalous inter-block arrival times. Evaluated via the Kolmogorov-Smirnov test.

## Module Tracking
| Module | Description | Status |
|---|---|---|
| M1 | Proof of Work Monitor | ✅ Done |
| M2 | Block Header Analyzer | ✅ Done |
| M3 | Difficulty History | ✅ Done |
| M4 | AI Component (Anomaly Detector) | ✅ Done |
| M5 | Transaction Explorer | ✅ Done |
| M6 | Security Score | ✅ Done |
| M7 | Mempool & Fee Market | ✅ Done |
| M8 | SegWit & Scalability | ✅ Done |
| M9 | Nonce Entropy (ASIC Fingerprinting) | ✅ Done |

## Current Progress
- Refactored the dashboard into a **modular structure** with a sidebar navigation.
- Implemented **M1-M3** with live data from Blockstream and Blockchain.info.
- Completed the **M4 AI component** with statistical evaluation (KS-test).
- Added two optional modules (**M5 & M6**) and three extra modules (**M7, M8, M9**) for high-performance security and scalability analysis.
- Created and uploaded the final project report in PDF format to the `report/` directory.
- Addressed all previous teacher feedback regarding README structure and module tracking.

## Next Step
- None. Project completed and submitted for final evaluation.

## Main Problem or Blocker
None. All modules are fully operational and the project structure is now compliant with the requirements.

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

The dashboard uses a sidebar for navigation between modules.

## Project Structure

```
blockchain-dashboard-jorgee12-2/
├── README.md
├── requirements.txt
├── app.py                        # Dashboard entry point
├── api/
│   └── blockchain_client.py      # Blockstream + Blockchain.info helpers
├── modules/
│   ├── m1_pow_monitor.py         # M1: difficulty, hash rate, block time distribution
│   ├── m2_block_header.py        # M2: header parse + hashlib PoW verification
│   ├── m3_difficulty_history.py  # M3: difficulty chart + adjustment ratio
│   ├── m4_ai_component.py        # M4: exponential anomaly detector (KS-evaluated)
│   ├── m5_tx_explorer.py         # M5: Transaction network graph
│   ├── m6_security.py            # M6: 51% attack cost & Nakamoto prob.
│   ├── m7_mempool.py             # M7: Real-time Mempool & Fee market
│   ├── m8_witness_analyzer.py    # M8: SegWit weight & scalability
│   └── m9_nonce_entropy.py       # M9: ASIC Fingerprinting (Nonce entropy)
└── report/                       # Final PDF report
```

## APIs Used

| API | URL | Purpose |
|---|---|---|
| Blockstream | `https://blockstream.info/api` | Block data, raw headers, transactions |
| Blockchain.info | `https://blockchain.info` | Difficulty history chart |

<!-- student-repo-auditor:teacher-feedback:start -->
## Teacher Feedback

### Kick-off Review

Review time: 2026-04-29 20:31 CEST
Status: Amber

Strength:
- M2 already includes concrete block-header analysis work.

Improve now:
- The README should now reflect the checkpoint more explicitly, including progress, blockers, and updated module status.

Next step:
- Update the README so progress, blockers, module status, and next step match the checkpoint format exactly.
<!-- student-repo-auditor:teacher-feedback:end -->
