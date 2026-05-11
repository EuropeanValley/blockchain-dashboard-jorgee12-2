**Student:** Jorge Rodrigo Serrano (jorgee12)
**Course:** Cryptography | Universidad Alfonso X el Sabio


---

## 1. Cryptographic Metrics and Meaning

The dashboard implements several modules that bridge theoretical cryptographic concepts with real-time data from the Bitcoin network.

### 1.1 Proof of Work and Target Threshold (M1 & M2)
The core of Bitcoin's security is the **Proof of Work (PoW)** mechanism. In **Module M2**, we parse the 80-byte block header and perform local verification:
```python
computed_hash = sha256(sha256(raw_header))
is_valid = int(computed_hash, 16) <= target
```
This demonstrates the concept of **Difficulty adjustment**: as hash rate fluctuates, the target threshold scales to maintain 10-minute intervals.

### 1.2 Difficulty History and Adjustment (M3)
**Module M3** tracks the evolution of difficulty over time. Bitcoin adjusts difficulty every 2016 blocks based on the ratio between the actual time taken and the 2-week target.

---

## 2. AI Component: Statistical Anomaly Detection

For **Module M4**, we implemented an **Anomaly Detector** based on inter-block arrival times.

### 2.1 Model Selection
Mining follows a **Poisson process**. Inter-block times follow an **Exponential distribution** with parameter $\lambda = 1/10 \text{ min}^{-1}$. We use MLE to fit the model and detect outliers.

### 2.2 Evaluation
The model is evaluated using the **Kolmogorov-Smirnov (KS) test**, ensuring that the theoretical exponential model accurately reflects real-world data.

---

## 3. Beyond Course Notes: Security and Network Analysis

### 3.1 51% Attack Cost (M6)
We estimate the CapEx (Hardware) and OpEx (Electricity) required to overtake the network, currently requiring billions of USD in infrastructure.

### 3.2 Nakamoto Double-Spend Probability
Visualizing Section 11 of the 2008 whitepaper: the probability of an attacker catching up after $z$ confirmations.

### 3.3 Mempool & Fee Market (M7)
Real-time monitoring of network congestion and recommended fees via mempool.space.

### 3.4 Scalability and SegWit (M8)
Analysis of the "Witness Discount" and how SegWit enables Layer 2 scaling via the separation of signatures.

### 3.5 Nonce Entropy & ASIC Fingerprinting (M9)
Statistical analysis of nonces to identify patterns in the search space, demonstrating advanced probability theory applied to blockchain forensics.

---

## 4. UI/UX: Hypermodern Cinematic Design

The dashboard utilizes a "Hypermodern" aesthetic inspired by cinematic data visualization:
- **Perspective Grid Drift:** A background animation that creates a sense of depth and continuous data flow.
- **Cinematic Textures:** Subtle film grain overlays for a high-end, professional feel.
- **Holographic Gradients:** Text and UI elements use multi-tone gradients to simulate high-tech displays.
- **Floating Glassmorphism:** Components use vertical oscillation (floating) and deep saturation blurs to create a layered, modern interface.
- **Micro-interactions:** Interactive scaling and neon-pulse effects on hover to engage the user.

---

## 5. References
- Nakamoto, S. (2008). *Bitcoin: A Peer-to-Peer Electronic Cash System*.
- Blockstream.info API Documentation. `https://blockstream.info/api`
- Mempool.space API Documentation. `https://mempool.space/api`
- Universidad Alfonso X el Sabio. *Topic 7: Blockchain and Cryptography notes*.
