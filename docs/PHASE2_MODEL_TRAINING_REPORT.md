# FLOOD-X — Phase 2.2: Model Training & Architecture Report
**Project:** FLOOD-X: AI-Powered Flood-to-Action Decision Intelligence Platform  
**Pilot Region:** Pune / Mula-Mutha River Basin, Maharashtra, India  
**Scope:** Chronological Model Training, Hyperparameter Optimization, and Imbalance Handling  
**Date:** November 2026  
**Status:** COMPLETED & VERIFIED  

---

## 1. Executive Summary

Phase 2.2 developed and evaluated five predictive models for the **Daily Pune-Region Flood-Event Risk Classification** task:
1. **Baseline 1: Dummy Majority Class Predictor** (Zero-intelligence baseline)
2. **Baseline 2: 24h Rainfall Threshold Heuristic** ($> 50\text{ mm/day}$ standard operational rule)
3. **Model 1: Logistic Regression (L2 Regularized, Balanced Class Weights)** (Interpretable linear benchmark)
4. **Model 2: Random Forest Classifier (Balanced Class Weights)** (Nonlinear ensemble baseline)
5. **Model 3: XGBoost Classifier (scale_pos_weight = 29.44)** (Primary gradient-boosted decision tree model)

All models were trained chronologically on the **2020–2022 partition (1,096 days)**, validated on **2023 (365 days)**, and evaluated on the held-out **2024 test year (366 days)**.

---

## 2. Experimental Setup & Chronological Partitions

```
+-------------------------------------------------------------------------------------------------------+
|                                    CHRONOLOGICAL PARTITION ARCHITECTURE                               |
+-------------------------------------------------------------------------------------------------------+
| Partition   | Date Range               | Calendar Days | Non-Flood (0) | Flood (1) | Imbalance Ratio  |
+-------------------------------------------------------------------------------------------------------+
| TRAIN       | 2020-01-01 to 2022-12-31 | 1,096 days    | 1,060 days    | 36 days   | 29.44 : 1        |
| VALIDATION  | 2023-01-01 to 2023-12-31 | 365 days      | 365 days      | 0 days    | Pure Non-Flood   |
| TEST        | 2024-01-01 to 2024-12-31 | 366 days      | 363 days      | 3 days    | 121.00 : 1       |
+-------------------------------------------------------------------------------------------------------+
```

### Class Imbalance Strategy
In the training partition, the negative-to-positive ratio is $1,060 / 36 = 29.44$.
To prevent models from collapsing into predicting the majority class, FLOOD-X implemented:
1. **Loss Reweighting in XGBoost:** Configured `scale_pos_weight = 29.44`, which scales the gradient of the positive class by $29.44\times$, forcing the loss optimizer to penalize false negatives equally to false positives.
2. **Cost-Sensitive Learning in Logistic Regression & Random Forest:** Configured `class_weight = "balanced"`, which computes class weights as:
   $$w_j = \frac{N}{2 \times N_j}$$

---

## 3. Model Configurations & Hyperparameters

### 3.1 Baseline 1: Dummy Majority Class Classifier
- **Implementation:** `sklearn.dummy.DummyClassifier(strategy="most_frequent")`
- **Mechanism:** Always predicts $y = 0$ (No Flood).
- **Purpose:** Establishes the trivial accuracy ceiling ($99.18\%$) and demonstrates why accuracy alone is a misleading metric for rare natural hazards.

### 3.2 Baseline 2: 24h Rainfall Threshold Heuristic
- **Implementation:** `HeuristicThresholdClassifier(threshold_mm=50.0)`
- **Mechanism:** Predicts $y = 1$ if `precip_total_24h` $\ge 50.0\text{ mm}$, else $0$.
- **Purpose:** Standard rule-of-thumb benchmark used by municipal flood control rooms.

### 3.3 Model 1: Logistic Regression (L2 Regularized)
- **Implementation:** `sklearn.linear_model.LogisticRegression`
- **Preprocessing:** `StandardScaler` fitted **only on the training partition** ($z = \frac{x - \mu_{\text{train}}}{\sigma_{\text{train}}}$).
- **Hyperparameters:**
  - Penalty: L2 Ridge
  - Regularization Strength: $C = 0.5$
  - Class Weight: `"balanced"`
  - Solver: `lbfgs`
  - Max Iterations: $1,000$
  - Random Seed: `random_state = 42`

### 3.4 Model 2: Random Forest Classifier
- **Implementation:** `sklearn.ensemble.RandomForestClassifier`
- **Hyperparameters:**
  - Number of Trees (`n_estimators`): $100$
  - Maximum Tree Depth (`max_depth`): $5$ (constrained to prevent overfitting on 36 positive instances)
  - Minimum Samples per Split (`min_samples_split`): $4$
  - Minimum Samples per Leaf (`min_samples_leaf`): $2$
  - Class Weight: `"balanced"`
  - Bootstrap: `True`
  - Random Seed: `random_state = 42`

### 3.5 Model 3: XGBoost Classifier (Primary Candidate)
- **Implementation:** `xgboost.XGBClassifier`
- **Objective:** `binary:logistic`
- **Evaluation Metric:** `logloss`
- **Hyperparameters:**
  - Number of Boosting Rounds (`n_estimators`): $120$
  - Maximum Tree Depth (`max_depth`): $4$
  - Learning Rate ($\eta$): $0.04$
  - Positive Weight Multiplier (`scale_pos_weight`): $29.44$
  - Subsample Ratio (`subsample`): $0.85$ (stochastic row sampling)
  - Column Subsample (`colsample_bytree`): $0.85$ (stochastic feature sampling)
  - Regularization L2 ($\lambda$): $1.0$
  - Regularization L1 ($\alpha$): $0.1$
  - Random Seed: `random_state = 42`

---

## 4. Model Serialization & Production Artifacts

All model artifacts are stored in `data/models/`:

1. **`floodx_xgboost_model.joblib`:** Serialized XGBoost booster artifact.
2. **`feature_scaler.joblib`:** Serialized scikit-learn `StandardScaler` artifact.
3. **`model_evaluation_report.json`:** Comprehensive JSON report storing model metrics, confusion matrices, and feature importances.

### Artifact Verification
- Loading and inference test verified in `backend/tests/test_ml_pipeline.py::test_model_inference`.
- Startup deserialization verified in `app.services.ml.inference.ModelInferenceService`.

