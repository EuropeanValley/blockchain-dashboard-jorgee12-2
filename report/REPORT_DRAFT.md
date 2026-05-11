# CryptoChain Analyzer Dashboard - Project Report
**Student:** Jorge Rodrigo Serrano (jorgee12-19)
**Course:** Cryptography | Universidad Alfonso X el Sabio
**Professor:** Jorge Calvo — Academic Year 2025–26

---

## 1. Cryptographic Metrics and Meaning

The dashboard implements several modules that bridge theoretical cryptographic concepts with real-time data from the Bitcoin network.

### 1.1 Proof of Work and Target Threshold (M1 & M2)
The core of Bitcoin's security is the **Proof of Work (PoW)** mechanism. In **Module M2**, we parse the 80-byte block header which includes:
- `version` (4B)
- `prev_hash` (32B)
- `merkle_root` (32B)
- `timestamp` (4B)
- `bits` (4B)
- `nonce` (4B)

The `bits` field encodes the **target threshold** (a 256-bit number). A block is considered valid only if its double-SHA256 hash is less than or equal to this target.
Our dashboard performs this verification locally:
```python
computed_hash = sha256(sha256(raw_header))
is_valid = int(computed_hash, 16) <= target
```
This demonstrates the concept of **Difficulty adjustment**: as more hash rate enters the network, the target threshold decreases (requiring more leading zeros), keeping the average block time around 10 minutes.

### 1.2 Difficulty History and Adjustment (M3)
**Module M3** tracks the evolution of difficulty over time. Bitcoin adjusts difficulty every 2016 blocks based on the ratio between the actual time taken and the 2-week target.
$$ \text{new\_difficulty} = \text{old\_difficulty} \times \frac{2016 \times 600\text{s}}{\text{actual\_time}} $$
We visualize this ratio to show how the network responds to fluctuations in mining power.

---

## 2. AI Component: Statistical Anomaly Detection

For **Module M4**, we implemented an **Anomaly Detector** based on the inter-block arrival times.

### 2.1 Model Selection
Mining is a **Poisson process** because each hash attempt is independent and has a very low probability of success. Consequently, the time between blocks follows an **Exponential distribution** with parameter $\lambda = 1/10 \text{ min}^{-1}$.

We use **Maximum Likelihood Estimation (MLE)** to fit an exponential distribution to the last $N$ blocks. We then identify "anomalies" as blocks whose arrival time $t$ has a very low probability under the fitted model:
- **Fast anomaly:** $P(T < t) < \alpha$
- **Slow anomaly:** $P(T > t) < \alpha$

### 2.2 Evaluation
The model is evaluated using the **Kolmogorov-Smirnov (KS) test**, which compares the empirical cumulative distribution function (ECDF) of our data with the theoretical CDF of the exponential distribution. A high p-value (> 0.05) indicates that the exponential model is a good fit for the data.

---

## 3. Beyond Course Notes: Security and Network Analysis

### 3.1 51% Attack Cost (M6)
We expanded the project by estimating the real-world cost of a 51% attack. Using current network hashrate (~600 EH/s) and specifications for modern hardware (Antminer S21 Pro), we estimate:
- **Hardware CapEx:** The cost to purchase enough miners (Billions of USD).
- **OpEx (Electricity):** The hourly cost to run the attack (Millions of USD/hour).

### 3.2 Nakamoto Double-Spend Probability
Based on Section 11 of the original **Nakamoto (2008)** whitepaper, we visualize the probability of an attacker with $q$ hashrate successfully catching up after $z$ confirmations. This provides a quantitative measure of transaction security.

### 3.3 Mempool & Fee Market (M7)
We integrated live data from **mempool.space** to provide:
- **Recommended fees** for different confirmation timeframes (Fastest, 30m, 60m).
- **Mempool weight visualization** via a gauge chart, allowing users to estimate network congestion.
This module helps bridge the gap between protocol-level metrics (hashrate, difficulty) and user-level utility (transaction fees).

---

## 4. UI/UX: State-of-the-Art Dashboard Design

The dashboard was built with a "Premium-First" philosophy, going beyond standard framework defaults:
- **Glassmorphism:** Using semi-transparent layers and background blur to create depth.
- **Micro-animations:** Pulsating "LIVE" indicators and marquee tickers for a real-time feel.
- **Typography:** Implementation of high-end fonts (*Inter* and *Space Grotesk*) to ensure clarity and a modern tech aesthetic.
- **Responsiveness:** Modular grid layout that adapts to different viewing conditions.

---

## 5. References
- Nakamoto, S. (2008). *Bitcoin: A Peer-to-Peer Electronic Cash System*.
- Blockstream.info API Documentation. `https://blockstream.info/api`
- Mempool.space API Documentation. `https://mempool.space/api`
- Blockchain.info API Documentation. `https://blockchain.info/api`
- Universidad Alfonso X el Sabio. *Topic 7: Blockchain and Cryptography notes*.
