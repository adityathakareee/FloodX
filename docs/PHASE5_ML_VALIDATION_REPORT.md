# FLOOD-X — PHASE 5: ML VALIDATION & TASK SEPARATION REPORT

**Project:** FLOOD-X — AI-Powered Flood-to-Action Decision Intelligence Platform  
**Target Basin:** Pune / Mula-Mutha River Basin, Maharashtra, India  
**Document Reference:** `docs/PHASE5_ML_VALIDATION_REPORT.md`  
**Date:** November 2026  
**Status:** VALIDATED & SCIENTIFICALLY BENCHMARKED  

---

## 1. EXECUTIVE SUMMARY

During Phase 2.2 and Phase 2.2.1, machine learning models were developed to evaluate daily flood risk in Pune. However, critical scientific limitations were identified:
1. **Single Test Disaster Constraint:** The held-out chronological test partition (2024) contained exactly one major flood event (July 24–26, 2024 Khadakwasla discharge disaster, 3 positive days). Precision metrics suffered from severe sample variance.
2. **Threshold Over-Fitting Risk:** In Phase 2.2, an uncalibrated XGBoost model achieved 0% disaster recall at default $\theta = 0.50$ and required post-hoc threshold tuning ($\theta = 0.25$) on the test partition.
3. **Task Conflation:** Retrospective diagnostic modeling (using completed 24h daily totals) was at risk of being conflated with prospective early-warning forecasting or real-time observational assessments.

In Phase 5, we have implemented a comprehensive scientific enhancement:
- **Leak-Free Event-Grouped Cross-Validation (`GroupKFold`, $K=5$):** Groups multi-day contiguous flood episodes together so no disaster episode is split between training and evaluation folds.
- **Three-Way ML Task Separation:** Isolates Task A (Retrospective Diagnosis), Task B (Current Condition Assessment), and Task C (Prospective Risk Assessment).
- **Rigorous Multi-Model Benchmark Comparison:** Evaluates Dummy Majority, 24-hour Rainfall Threshold heuristic (>50mm), Balanced Logistic Regression, Balanced Random Forest, and Calibrated XGBoost.
- **Brier Calibration Loss Analysis:** Quantifies probability calibration reliability.

---

## 2. THE THREE-WAY TASK SEPARATION ARCHITECTURE

To ensure scientific and operational integrity, FLOOD-X strictly decouples flood intelligence into three independent tasks:

| Dimension | Task A: Retrospective Diagnosis | Task B: Current Condition Assessment | Task C: Prospective Risk Assessment |
| :--- | :--- | :--- | :--- |
| **Purpose** | What happened historically? Event confirmation and feature importance. | What is occurring right now? Real-time operational state. | What will happen? Multi-horizon early-warning forecast. |
| **Temporal Frame** | Completed 24-hour daily summary (2020–2024 reanalysis). | Real-time / instantaneous to 1-hour trailing observations. | Forward-looking 6h, 12h, 24h, 48h lead-time windows. |
| **Input Data** | Completed ERA5/Open-Meteo reanalysis, 3d/7d antecedent precipitation, soil moisture. | Latest Open-Meteo hourly observations, river telemetry status, road closure status. | Open-Meteo High-Resolution NWP forecasts, simulated/bulletin dam discharge schedules. |
| **Model / Engine** | Supervised ML (XGBoost, Random Forest, Logistic Regression). | Rule-based engineering gatekeeper with freshness safeguards. | Physics-informed pluvial/riverine decision engine with audited thresholds. |
| **Outputs** | Daily flood event probability ($0.0 - 1.0$), feature attribution. | State: `NORMAL`, `ELEVATED_PLUVIAL_RISK`, `SEVERE_INUNDATION_RISK`, or `DATA_INSUFFICIENT`. | Risk Tiers (`GREEN`, `YELLOW`, `ORANGE`, `RED`), surcharge probabilities, evacuation triggers. |
| **Operational Boundary** | Research & post-event diagnostics only. Never for live dispatch. | Authority Command Center & Mobile live situation awareness. | Evacuation planning, shelter pre-activation, resource dispatch. |

---

## 3. EVENT-GROUPED CROSS-VALIDATION METHODOLOGY

### 3.1 Event Leakage Prevention
In standard $K$-Fold cross-validation, observations from consecutive days of a single flood disaster (e.g., July 24, 25, and 26, 2024) can be arbitrarily split across training and test folds. Because soil moisture and antecedent rainfall are highly autocorrelated across adjacent days, standard $K$-Fold allows information to leak between train and test splits, artificially inflating evaluation scores.

To eliminate temporal leakage:
- Contiguous positive flood days are assigned a unique cluster identifier (`EVENT_X`).
- Non-flood background days are clustered by year-month (`DRY_YYYY_M`).
- A 5-fold `GroupKFold` split is applied, guaranteeing that all days of an event appear entirely within a single fold.

### 3.2 Evaluation Metrics
- **Out-of-Fold ROC-AUC:** Measures discriminative ranking ability across independent folds.
- **Out-of-Fold PR-AUC:** Evaluates area under the Precision-Recall curve under extreme class imbalance (39 positive days out of 1,827 total records, 2.13% prevalence).
- **Brier Calibration Score:** Mean squared difference between predicted probabilities and actual binary outcomes ($0 \le BS \le 1$, where lower indicates superior probability calibration).
- **False Alarm Rate (%):** False positives divided by total negative days.

---

## 4. EXPERIMENTAL BENCHMARK RESULTS

The 5-fold event-grouped cross-validation was executed on the full 1,827-day Pune basin dataset (2020–2024).

| Model | Out-of-Fold ROC-AUC | Out-of-Fold PR-AUC | Brier Calibration Loss | Precision | Recall | F1-Score | Accuracy | False Alarm Rate (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dummy Majority** | 0.5000 | 0.0213 | 0.0213 | 0.00% | 0.00% | 0.0000 | 97.87% | 0.00% |
| **Rainfall Threshold (>50mm)** | 0.9049 | 0.1482 | 0.0209 | 11.11% | 2.56% | 0.0417 | 97.48% | 0.45% |
| **Logistic Regression (Balanced)** | **0.9222** | **0.1750** | 0.0758 | 13.02% | **71.79%** | **0.2205** | 89.16% | 10.46% |
| **Random Forest (Balanced)** | 0.9023 | 0.1008 | 0.0609 | 10.46% | 41.03% | 0.1667 | 91.24% | 7.66% |
| **XGBoost (Calibrated Scale)** | 0.8693 | 0.1075 | **0.0318** | 7.89% | 7.69% | 0.0779 | 96.11% | 1.96% |

### 4.1 Detailed Confusion Matrices

1. **Dummy Majority:**
   - TN: 1,788 | FP: 0 | FN: 39 | TP: 0
   - *Failure Mode:* Completely fails to detect any flood disaster (0% recall).

2. **Rainfall Threshold (>50mm Heuristic):**
   - TN: 1,780 | FP: 8 | FN: 38 | TP: 1
   - *Failure Mode:* Catches only 1 isolated cloudburst day. Misses 97.4% of flood days because major Pune floods are driven by upstream catchment dam releases (Khadakwasla) or multi-day saturated runoff, not purely local >50mm daily rainfall.

3. **Logistic Regression (Balanced):**
   - TN: 1,601 | FP: 187 | FN: 11 | TP: 28
   - *Advantage:* Captures 28 of 39 disaster days (**71.79% recall**). Out-of-fold PR-AUC is highest at 0.1750.
   - *Trade-off:* 187 false alarms across 5 years (approx. 37 false alarms per year during peak monsoon).

4. **Random Forest (Balanced):**
   - TN: 1,651 | FP: 137 | FN: 23 | TP: 16
   - *Characteristics:* 41.03% recall with a reduced false alarm rate of 7.66%.

5. **XGBoost (Calibrated Scale):**
   - TN: 1,753 | FP: 35 | FN: 36 | TP: 3
   - *Characteristics:* Lowest Brier loss (0.0318) and highest accuracy (96.11%), but uncalibrated tree structures require explicit probability adjustment to achieve operational disaster sensitivity.

### 4.2 5-Fold GroupKFold Partition Distribution & Sample Size Limitation

| Fold Index | Total Train Samples | Total Test Samples | Train Flood Events | Test Flood Events | Train Positive Days | Test Positive Days |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fold 1** | 1,460 | 367 | 9 | 2 | 33 | 6 |
| **Fold 2** | 1,462 | 365 | 9 | 2 | 35 | 4 |
| **Fold 3** | 1,462 | 365 | 9 | 2 | 33 | 6 |
| **Fold 4** | 1,463 | 364 | 9 | 2 | 29 | 10 |
| **Fold 5** | 1,461 | 366 | 8 | 3 | 26 | 13 |
| **Total Out-of-Fold** | — | **1,827** | — | **11** | — | **39** |

> [!WARNING] Critical Sample Size Limitation & Operational Boundary
> The historical register contains exactly **11 independent flood events** across 5 years (2020–2024, 39 positive days out of 1,827 total daily records; 2.13% class prevalence).
> Under 5-fold cross-validation, each evaluation fold tests only **2 to 3 independent flood episodes**.
> Consequently, single-fold variance is substantial, confidence bounds around recall and precision are broad, and all retrospective ML models must remain formally classified as **`EXPERIMENTAL_EXPLORATORY_BASELINE`** decision aids. They must **never** be deployed as autonomous operational triggers without direct municipal authority verification and upstream Khadakwasla spillway telemetry.

---

## 5. SCIENTIFIC FINDINGS & TAKEAWAYS

1. **The Fallacy of Simple Rainfall Thresholds:**
   The simple heuristic (24h rain > 50 mm) achieves only **2.56% recall**. This proves quantitatively that local rainfall alone is an inadequate predictor of flooding in Pune. Dam discharge from the upstream Khadakwasla reservoir is the dominant driver of riverine flooding, while soil saturation governs pluvial surcharge.

2. **Event-Grouped Cross-Validation Reveals True Generalization:**
   Under standard train-test splitting, models appear to achieve deceptively high scores. Grouped cross-validation demonstrates that capturing independent flood events without local river telemetry is fundamentally constrained to ~70% recall at ~10% false alarm rate.

3. **Probability Calibration is Mandatory:**
   Uncalibrated tree ensembles produce overconfident probabilities when exposed to extreme Vertisol soil moisture values. Logistic Regression with $L_2$ regularization provides well-behaved probability gradients, making it a critical baseline for decision support.

---

## 6. TELEMETRY FRESHNESS GATE SAFEGUARDS

For Task B (Current Condition Assessment), Phase 5 enforces a strict **Freshness Gate**:
- Observations $< 3.0$ hours old: `LIVE_FRESH`
- Observations $3.0 - 6.0$ hours old: `CACHED_VALID`
- Observations $6.0 - 24.0$ hours old: `STALE` (Warning displayed)
- Observations $> 24.0$ hours old: `EXPIRED` $\rightarrow$ Condition status automatically falls back to `DATA_INSUFFICIENT`.

This ensures that authorities and citizens are never presented with obsolete or unverified weather data masquerading as real-time conditions.

