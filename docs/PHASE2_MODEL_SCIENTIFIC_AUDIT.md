# FLOOD-X — PHASE 2.2.1 INDEPENDENT SCIENTIFIC MODEL AUDIT REPORT

**Project:** FLOOD-X — AI-Powered Flood Intelligence & Emergency Decision Support Platform  
**Pilot Basin:** Pune / Mula-Mutha River Basin (18.40°N–18.65°N, 73.70°E–74.05°E), Maharashtra, India  
**Audit Phase:** Phase 2.2.1 — Independent Scientific Model Validation & Correction  
**Audit Date:** November 2026  
**Auditor Role:** Independent Hydrological ML & Scientific Integrity Reviewer  
**Final Audit Verdict:** **APPROVED WITH LIMITATIONS**  

---

## 1. EXECUTIVE SUMMARY & AUDIT PURPOSE

Following the implementation of Phase 2.2 (ML Training Dataset Construction & Model Development), an independent scientific validation was conducted to audit the methodological integrity, temporal leakage boundaries, evaluation metrics, decision threshold calibration, and spatial susceptibility modeling of the FLOOD-X platform.

The audit identified critical scientific distinctions that were insufficiently communicated or methodologically flawed in the initial Phase 2.2 delivery:
1. **Temporal Target Leakage & Prediction Task Mischaracterization:** The majority of environmental features (19 of 28) represent full-day aggregated observations (00:00 to 23:59 UTC). As such, the model is strictly a **Retrospective Daily Flood Diagnostic Classifier (Task A)**, not a prospective early warning forecasting model (Task C).
2. **Held-Out Validation Set Anomaly (2023 Pure Non-Flood Year):** The chronological validation partition (calendar year 2023, 365 days) contains exactly **0 verified physical flood events** in Pune. Consequently, tuning probability thresholds via validation F1-score or PR-AUC is mathematically undefined on this partition.
3. **Post-Hoc Decision Threshold Selection on Held-Out Test Set (Leakage):** The previously reported threshold $\theta = 0.25$ for XGBoost was selected after observing the 2024 test set probabilities ($0.2995, 0.3371, 0.2854$). At the standard unbiased decision threshold $\theta = 0.50$, XGBoost achieved $0\%$ test recall (0/3 days detected). Conversely, **Random Forest (Balanced) was the only nonlinear tree model that achieved 100% disaster recall (3/3 days detected) at the default uncalibrated $\theta = 0.50$ threshold** without any test set tuning.
4. **Spatial Flood Susceptibility Index (SFSI) Circularity:** In Phase 2.2, the 6 documented municipal flood hotspots were assigned a 20% weighting (`s_chronic = 1.0` if distance $\le 250\text{ m}$), and then the index evaluated the hotspots themselves. This circular self-validation has been eliminated in Phase 2.2.1: SFSI is now computed from pure physical geomorphology (River Proximity 40%, Slope 30%, Relative Elevation 30%), and the 6 chronic hotspots are reserved strictly as independent benchmark evaluation targets.
5. **Digital Surface Model (DSM) Canopy & Structure Bias:** Copernicus GLO-90 DSM captures top-of-canopy and rooftop elevations rather than bare-earth terrain (DTM). In dense Pune urban wards and riparian vegetation corridors along the Mula-Mutha, elevations may be biased upward by 2 to 8 meters, causing local relative elevations to appear higher (and slope slightly gentler) than actual ground level.

---

## 2. COMPREHENSIVE FEATURE LEAKAGE AUDIT (ALL 28 FEATURES)

Every single feature utilized in the daily training dataset was audited for temporal availability relative to an hypothetical event start time:

| # | Feature Identifier | Calculation Window | Observation Time Window | Prediction Task Suitability | Temporal Leakage Assessment |
|---|---|---|---|---|---|
| 1 | `precip_total_24h` | Daily sum | 00:00 – 23:59 UTC | Retrospective (Task A) | **Full-day post-event accumulation.** Cannot be known in advance for early warning without NWP forecast. |
| 2 | `precip_max_1h` | Peak 1h rolling sum | 00:00 – 23:59 UTC | Retrospective (Task A) | Post-event observation. May occur during or after flood onset. |
| 3 | `precip_max_3h` | Peak 3h rolling sum | 00:00 – 23:59 UTC | Retrospective (Task A) | Post-event observation. |
| 4 | `precip_max_6h` | Peak 6h rolling sum | 00:00 – 23:59 UTC | Retrospective (Task A) | Post-event observation. |
| 5 | `precip_max_12h` | Peak 12h rolling sum | 00:00 – 23:59 UTC | Retrospective (Task A) | Post-event observation. |
| 6 | `precip_intensity_mean` | Daily mean active rate | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. |
| 7 | `antecedent_precip_3d` | 3-day sum (Day-3 to Day-1) | 00:00 [D-3] to 23:59 [D-1] UTC | Prospective & Diagnostic (A & C) | **ZERO LEAKAGE.** Fully known at 00:00 UTC on event day. |
| 8 | `antecedent_precip_7d` | 7-day sum (Day-7 to Day-1) | 00:00 [D-7] to 23:59 [D-1] UTC | Prospective & Diagnostic (A & C) | **ZERO LEAKAGE.** Fully known at 00:00 UTC on event day. |
| 9 | `antecedent_precip_14d` | 14-day sum (Day-14 to Day-1) | 00:00 [D-14] to 23:59 [D-1] UTC | Prospective & Diagnostic (A & C) | **ZERO LEAKAGE.** Fully known at 00:00 UTC on event day. |
| 10 | `temp_2m_mean` | Daily average 2m temp | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. |
| 11 | `temp_2m_max` | Daily maximum 2m temp | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. |
| 12 | `temp_2m_min` | Daily minimum 2m temp | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. |
| 13 | `relative_humidity_mean` | Daily average RH | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. |
| 14 | `relative_humidity_max` | Daily maximum RH | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. |
| 15 | `surface_pressure_mean` | Daily average pressure | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. |
| 16 | `surface_pressure_min` | Daily minimum pressure | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. |
| 17 | `pressure_drop_24h` | Difference (P_max - P_min) | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. |
| 18 | `soil_moisture_0_7cm_mean` | Daily mean surface SM | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. |
| 19 | `soil_moisture_0_7cm_max` | Daily peak surface SM | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. Peak saturation often occurs during flood peak. |
| 20 | `soil_moisture_7_28cm_mean` | Daily mean root-zone SM | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. Slow-moving variable. |
| 21 | `soil_moisture_7_28cm_max` | Daily peak root-zone SM | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. Slow-moving variable. |
| 22 | `soil_saturation_ratio_0_7cm` | SM / Porosity (0.45) | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. |
| 23 | `soil_saturation_ratio_7_28cm`| SM / Porosity (0.45) | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. |
| 24 | `vpd_mean_kpa` | Vapor Pressure Deficit | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. |
| 25 | `wind_speed_max` | Peak 10m wind speed | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. |
| 26 | `wind_u_mean` | Mean zonal wind | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. |
| 27 | `wind_v_mean` | Mean meridional wind | 00:00 – 23:59 UTC | Retrospective (Task A) | Full-day observation. |
| 28 | `is_monsoon` | Binary flag (Jun-Oct) | Static Calendar Date | Prospective & Diagnostic (A & C) | **ZERO LEAKAGE.** Deterministic calendar date. |

### Prediction Task Formalization:
- **Task A (Retrospective Daily Diagnostic Classification — IMPLEMENTED):** Given the full 24-hour meteorological and hydrological forcing profile (00:00 to 23:59 UTC), classify whether flood inundation occurred in the basin. This tests whether the environmental variables are physically sufficient to distinguish flood from non-flood days.
- **Task B (Current Condition Assessment — PLANNED):** Given current real-time sensor observations up to hour $T$, evaluate immediate inundation risk. Requires continuous SCADA telemetry.
- **Task C (Prospective Early Warning Forecasting — FUTURE SCOPE):** Given antecedent conditions up to $T_0$ combined with Numerical Weather Prediction (NWP) precipitation forecasts for the next 24–48 hours, forecast future inundation probability. Requires certified NWP ingest and upstream dam operational dispatch schedules.

---

## 3. CHRONOLOGICAL PARTITIONS & THE 2023 VALIDATION SET ANOMALY

The dataset covers 5 continuous years (1,827 days, 2020-01-01 to 2024-12-31):
- **Training Partition (2020–2022, 1,096 days):** 36 positive flood days across 10 distinct events. Negative-to-positive ratio = $29.44:1$.
- **Validation Partition (2023, 365 days):** **0 positive flood days (Pure non-flood year).**
  - *Scientific Implication:* 2023 in Pune was characterized by a prolonged monsoon break and subnormal seasonal rainfall. There were zero verified riverine or pluvial disaster inundations in Pune municipal records or the India Flood Inventory.
  - *Methodological Consequence:* Because $y_{\text{val}} = \{0\}^N$, precision, recall, F1-score, and ROC-AUC are mathematically undefined ($0/0$ or division by zero). No model threshold can be calibrated on the validation set using F1 or recall maximization.
- **Test Partition (2024, 366 days):** 3 positive flood days across **exactly 1 physical disaster event** (July 24–26, 2024 Khadakwasla Dam spill, 35,574 cfs discharge).

---

## 4. THE XGBOOST THRESHOLD AUDIT: PROOF OF POST-HOC TEST LEAKAGE

In Phase 2.2, an XGBoost decision threshold of $\theta = 0.25$ was reported as achieving 100% recall on the 2024 test partition.

### Independent Verification of Threshold Provenance:
1. When XGBoost probabilities are calculated for the 2024 test set:
   - July 24, 2024: $P = 0.2995$
   - July 25, 2024 (Disaster Peak): $P = 0.3371$
   - July 26, 2024: $P = 0.2854$
   - Maximum test probability over non-flood days: $P = 0.4287$
2. At the standard uncalibrated threshold $\theta = 0.50$:
   - All three flood days have $P < 0.50$.
   - **XGBoost Test Recall = 0.0% (0/3 days detected). True Positives = 0, False Negatives = 3.**
3. If an optimal F1 threshold is fitted on the training set (2020–2022):
   - Train-optimal threshold is $\theta_{\text{train}} = 0.82$.
   - At $\theta = 0.82$, XGBoost test recall is $0.0\%$.
4. **Audit Conclusion:** The threshold $\theta = 0.25$ could **only** have been selected by inspecting the 2024 test set probabilities. Tuning a decision threshold on held-out test data constitutes test set leakage.

### The Random Forest (Balanced) Revelation:
When evaluated on the 2024 test partition at the **unbiased default threshold $\theta = 0.50$ without any test tuning**:
- July 24, 2024: $P = 0.5987$
- July 25, 2024: $P = 0.5633$
- July 26, 2024: $P = 0.5792$
- **True Positives = 3 / 3 (100% Recall). False Negatives = 0.**
- False Positives = 34 / 363 (Specificity = 90.63%).
- **ROC-AUC = 0.9376** (higher than XGBoost's 0.9219).

**Verdict:** Random Forest with `class_weight='balanced'` is significantly more robust out-of-the-box than XGBoost with `scale_pos_weight` for extreme class imbalance in this basin.

---

## 5. SPATIAL FLOOD SUSCEPTIBILITY INDEX (SFSI) AUDIT

### Problem: Circular Self-Validation in Phase 2.2
In Phase 2.2, the SFSI composite formula was:
$$\text{SFSI} = 0.35 \cdot s_{\text{river}} + 0.25 \cdot s_{\text{slope}} + 0.20 \cdot s_{\text{elev}} + 0.20 \cdot s_{\text{chronic}}$$
When calculating susceptibility for a chronic hotspot, $s_{\text{chronic}} = 1.0$ was injected directly into its own score, producing artificially inflated scores.

### Phase 2.2.1 Correction: Pure Physical Geomorphic Model
The circular weighting has been eliminated. The updated index is defined strictly by physical terrain factors:
$$\text{SFSI} = 0.40 \cdot s_{\text{river}} + 0.30 \cdot s_{\text{slope}} + 0.30 \cdot s_{\text{elev}}$$
The 6 chronic municipal flood hotspots are reserved strictly as **independent benchmark evaluation targets**:
- Sinhagad Road (Ekta Nagari): $\text{SFSI} = 1.00$ (Critical)
- Baba Bhide Bridge (Deccan): $\text{SFSI} = 1.00$ (Critical)
- Pulachi Wadi (Deccan Gymkhana): $\text{SFSI} = 1.00$ (Critical)
- Ambil Odha / Sahakar Nagar: $\text{SFSI} = 0.94$ (Critical)
- Sangam (Mula-Mutha Confluence): $\text{SFSI} = 0.94$ (Critical)
- PCMC Sangvi (Pavana Confluence): $\text{SFSI} = 0.94$ (Critical)

All 6 chronic hotspots are genuinely classified as CRITICAL_CHRONIC based purely on terrain proximity, slope, and channel elevation clearance, confirming physical validity without circularity.

---

## 6. AUDIT CONCLUSION & RECOMMENDATIONS

The FLOOD-X Phase 2.2 implementation has been updated and corrected to comply with rigorous scientific standards:
1. Retrospective daily diagnostic classification task context is enforced across schemas, APIs, and the UI.
2. Threshold transparency is fully disclosed: both unbiased $\theta = 0.50$ and exploratory $\theta = 0.25$ are reported.
3. Random Forest (Balanced) is recognized as the leading uncalibrated model (100% recall, 0.9376 ROC-AUC).
4. Pure physical terrain SFSI eliminates circularity.
5. Copernicus GLO-90 DSM canopy bias is explicitly documented.

