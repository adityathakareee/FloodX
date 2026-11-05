# FLOOD-X — Phase 2.2: Machine Learning System Architecture
**Project:** FLOOD-X: AI-Powered Flood-to-Action Decision Intelligence Platform  
**Pilot Region:** Pune / Mula-Mutha River Basin, Maharashtra, India  
**Scope:** Two-Tier Predictive & Geospatial ML Architecture  
**Date:** November 2026  
**Status:** IMPLEMENTED, TESTED & PRODUCTION-READY  

---

## 1. System Architecture Overview

To maintain scientific validity without manufacturing unobservable labels, FLOOD-X implements a **Decoupled Two-Tier ML Architecture**:

```
                                  +---------------------------------------------+
                                  |         FLOOD-X ML PIPELINE ENGINE          |
                                  +---------------------------------------------+
                                                         |
         +-----------------------------------------------+-----------------------------------------------+
         |                                                                                               |
         v                                                                                               v
+-----------------------------------------------+                               +-----------------------------------------------+
|                    TIER 1:                    |                               |                    TIER 2:                    |
|      TEMPORAL FLOOD EVENT CLASSIFICATION      |                               |         SPATIAL HAZARD SUSCEPTIBILITY         |
+-----------------------------------------------+                               +-----------------------------------------------+
| * Predicts daily probability of flood event   |                               | * Evaluates static terrain exposure across    |
|   occurrence across the Pune pilot basin.     |                               |   the Pune basin (100m grid resolution).      |
| * Model: XGBoost Classifier v1.0              |                               | * Multi-Criteria Analytical Hierarchy Process |
| * Features: 28 physical weather & soil vars   |                               |   (SFSI: River 35%, Slope 25%, Elev 20%,      |
|   (24h precip, 3d/7d API, soil saturation,    |                               |    Chronic Hotspots 20%).                     |
|    pressure drop, Tetens VPD).                |                               | * Chronic Hotspots Registry (137 PMC spots,   |
| * Chronological validation on 2024 test year  |                               |    Ekta Nagari, Pulachi Wadi, Bhide Bridge).  |
| * Output: P(Flood) & 4-Tier Alert Level       |                               | * Output: Relative SFSI Score (0.0 to 1.0) &  |
|   (NORMAL, WATCH, WARNING, EMERGENCY)         |                               |   Susceptibility Tier (Low to Critical)       |
+-----------------------------------------------+                               +-----------------------------------------------+
         |                                                                                               |
         +-----------------------------------------------+-----------------------------------------------+
                                                         |
                                                         v
                                        +----------------------------------+
                                        |      REST API & DASHBOARD        |
                                        | * FastAPI Backend (/api/v1/ml/*) |
                                        | * Interactive Risk Cockpit       |
                                        |   (/risk - FloodRiskPage.tsx)    |
                                        +----------------------------------+
```

---

## 2. Directory & Module Structure

```
FLOODX/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   └── ml.py                        # REST API endpoints for ML status, models, predict, explainability, SFSI
│   │   ├── schemas/
│   │   │   └── ml.py                        # Pydantic v2 schemas for requests, responses, and metrics
│   │   └── services/
│   │       └── ml/
│   │           ├── __init__.py
│   │           ├── label_validation.py      # Historical event audit, date correction, duplicate detection
│   │           ├── dataset_builder.py       # Zero-leakage daily feature engineering and Parquet builder
│   │           ├── model_trainer.py         # Chronological model training, comparison, and evaluation
│   │           ├── inference.py             # Deserialization, real-time prediction, and feature attribution
│   │           └── spatial_susceptibility.py# Physics-informed SFSI computation and hotspot registry
│   └── tests/
│       └── test_ml_pipeline.py              # 11 automated pytest tests covering all ML components
├── data/
│   ├── models/
│   │   ├── floodx_xgboost_model.joblib      # Serialized XGBoost production model
│   │   ├── feature_scaler.joblib            # Serialized StandardScaler fitted on training split
│   │   └── model_evaluation_report.json     # Comprehensive evaluation metrics across all 5 models
│   └── processed/
│       └── ml/
│           ├── daily_flood_training_dataset.parquet # 1,827 rows, 36 columns
│           ├── daily_flood_training_dataset.csv     # Inspection copy
│           └── spatial_susceptibility_results.json  # Pre-computed SFSI hotspot evaluations
└── frontend/
    └── src/
        ├── pages/
        │   └── FloodRiskPage.tsx            # Authority Dashboard Flood Risk Intelligence Page
        ├── services/
        │   └── api.ts                       # Integrated ML API service methods
        └── types/
            └── api.ts                       # TypeScript interfaces for ML schemas
```

---

## 3. REST API Contract (`/api/v1/ml/*`)

| Method | Endpoint | Description | Request Body | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/ml/status` | Current pipeline readiness & coverage | None | `MLStatusResponse` |
| `GET` | `/api/v1/ml/models` | List of investigated models & metadata | None | `List[MLModelMetadataResponse]` |
| `GET` | `/api/v1/ml/evaluation` | Chronological benchmark metrics on 2024 test | None | `MLEvaluationResponse` |
| `POST` | `/api/v1/ml/predict` | Real-time flood risk inference & guidance | `MLPredictionRequest` | `MLPredictionResponse` |
| `GET` | `/api/v1/ml/explainability` | Feature importance rankings & physical analysis | None | `MLExplainabilityResponse` |
| `GET` | `/api/v1/ml/spatial-susceptibility` | Geospatial SFSI scores & hotspot registry | None | `SpatialSusceptibilityResponse` |

---

## 4. Frontend Command Dashboard Integration

The Authority Web Dashboard shell was extended with a full **Flood Risk Intelligence & Predictive Modeling Cockpit** accessible via `/risk`:
- **Real-Time Interactive Inference Simulator:** Enables operators to input weather parameters or trigger pre-configured presets (*Dry Day*, *Monsoon Shower*, *July 2024 Cloudburst*), issuing real `POST /api/v1/ml/predict` calls and displaying calibrated alert tiers.
- **Model Benchmark Comparison Card:** Compares all five investigated architectures across accuracy, precision, recall, F1, ROC-AUC, and full confusion matrices.
- **Feature Importance & Hydrological Attribution:** Visualizes the top 10 environmental factors driving predictions (surface and root-zone soil saturation, Tetens VPD, antecedent rainfall).
- **Geospatial Susceptibility Hotspot Registry:** Displays Pune's chronic flood hotspots (Ekta Nagari, Bhide Bridge, Pulachi Wadi, Ambil Odha, PCMC Sangvi) with verified inundation depths and SFSI scores.

---

## 5. Transition Readiness for Phase 3 (Evacuation & Safe Routing)

The Phase 2.2 ML implementation establishes the direct inputs required for **Phase 3 (Dynamic Evacuation & Safe Routing)**:
1. **Dynamic Risk Ingestion:** When the ML predictor issues a `WARNING` or `EMERGENCY` tier, Phase 3 routing algorithms will penalize edges adjacent to high-susceptibility corridors.
2. **Submerged Bridge Avoidance:** Baba Bhide Bridge causeway and low-level bridges identified with high SFSI ($> 0.85$) will have edge weights set to infinity ($\infty$) upon Level-2 Alert, forcing routing graphs to redirect citizen evacuation over high-level bridges (Sambhaji, Lakdi Pul, Z-Bridge, SM Joshi Bridge).
3. **Muster Point Placement:** High-ground low-SFSI zones identified in the spatial susceptibility service will serve as primary safe shelter destinations.

