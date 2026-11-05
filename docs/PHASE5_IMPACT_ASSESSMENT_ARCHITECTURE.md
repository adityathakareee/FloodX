# FLOOD-X — PHASE 5: FLOOD IMPACT ASSESSMENT & SAR SATELLITE ARCHITECTURE

**Project:** FLOOD-X — AI-Powered Flood-to-Action Decision Intelligence Platform  
**Target Basin:** Pune / Mula-Mutha River Basin, Maharashtra, India  
**Document Reference:** `docs/PHASE5_IMPACT_ASSESSMENT_ARCHITECTURE.md`  
**Date:** November 2026  
**Status:** SPECIFIED, IMPLEMENTED & INTEGRATED  

---

## 1. EXECUTIVE SUMMARY & OBJECTIVES

Flood risk prediction alone is insufficient for operational disaster management. Emergency managers require concrete answers to tactical questions:
- Which hospitals and clinics are physically cut off or facing water ingress?
- Which schools and colleges in the evacuation zone must be excluded from shelter rosters?
- Which river bridges and low-level causeways are submerged?
- What is the total length of inundated roadways and which arterial corridors are impassable?
- How many citizens are exposed within the inundation footprint?

Phase 5 introduces the **Flood Impact Assessment Engine**, connecting remote sensing observation (Sentinel-1 SAR C-band), hydraulic dam discharge scenarios (Khadakwasla Dam), and PostGIS GIS spatial layers into an automated multi-sector vulnerability and exposure intelligence system.

---

## 2. SENTINEL-1 SAR SATELLITE INTEGRATION ARCHITECTURE

```
Copernicus Data Space Ecosystem (Sentinel-1A IW GRD)
                   │
                   ▼
       Radiometric Calibration &
       Speckle Filtering (Lee 5x5)
                   │
                   ▼
  Pre-Event (July 15) vs Post-Event (July 27)
         Amplitude Ratio (Δσ⁰)
                   │
                   ▼
       Thresholding: Δσ⁰ ≤ -3.5 dB
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
 Permanent Water Mask    Slope Mask (>5°)
   (OSM Riverbed)       (Copernicus DEM)
         └─────────┬─────────┘
                   ▼
         Urban False-Positive Filter
          (Building Footprints)
                   │
                   ▼
   Verified Flood Inundation Polygon
                   │
                   ▼
       [STRICT SCIENTIFIC BOUNDARY]
  SAR Backscatter Detects Water Extent ONLY.
  Flood Depth CANNOT Be Inferred From SAR Alone.
```

### 2.1 Sensor & Scene Specifications
- **Constellation:** Sentinel-1A C-band SAR (5.405 GHz center frequency).
- **Mode & Product:** Interferometric Wide Swath (IW), Ground Range Detected (GRD) at high resolution (10m pixel spacing).
- **Polarization:** Dual-polarization ($\text{VV} + \text{VH}$). $\text{VV}$ backscatter provides superior sensitivity to open water specular scattering.
- **Reference Historical Disaster Scene:**
  - *Pre-Event Baseline:* July 15, 2024 (monsoon baseflow).
  - *Post-Event Disaster:* July 27, 2024 00:45 UTC (Orbit 121, Descending pass, capturing peak inundation following the 35,574 cfs Khadakwasla spillway discharge).

### 2.2 Image Processing Pipeline
1. **Calibration:** Orbit state vectors applied; digital pixel values converted to sigma naught ($\sigma^0$) backscatter intensity in decibels (dB).
2. **Speckle Reduction:** A $5\times 5$ spatial Lee filter removes granular multiplicative speckle noise while preserving sharp water-land boundaries.
3. **Change Detection:** Decibel difference map $\Delta \sigma^0 = \sigma^0_{\text{post}} - \sigma^0_{\text{pre}}$. Open standing water acts as a specular reflector, scattering radar energy away from the sensor and producing an amplitude drop ($\Delta \sigma^0 \le -3.5\text{ dB}$).
4. **Permanent Water Body Masking:** The baseline OSM Mula-Mutha riverbed polygon is subtracted so that normal channel flow is not misclassified as "newly inundated land".
5. **Topographic Masking:** Terrain slopes $> 5.0^\circ$ derived from Copernicus GLO-90 DEM are excluded to eliminate shadow/layover artifacts.
6. **Urban Masking:** High-density concrete structures produce double-bounce reflections; low-lying tarmac and parking areas are cross-referenced with elevation to prevent specular false positives.

### 2.3 Strict Scientific Boundary: Extent vs Depth
> [!CAUTION]
> **SAR backscatter intensity measures surface roughness and dielectric contrast — it detects open standing water EXTENT ONLY.**  
> It is physically impossible to measure water depth from single-frequency SAR backscatter alone. FLOOD-X strictly prohibits inferring flood depth from SAR backscatter. Depth estimation requires hydraulic 2D overland flow modeling or calibrated stage gauges.

---

## 3. MULTI-SECTOR GIS SPATIAL OVERLAY ARCHITECTURE

The impact engine executes spatial distance and intersection calculations between the hazard polygon and PostGIS spatial entities:

### 3.1 Healthcare Facilities Exposure
Queried from PostGIS table `spatial_features` (`feature_type = 'HEALTHCARE'`, 185 total facilities):
- **CRITICAL Tier ($< 75\text{ m}$):** Direct water ingress to ground floors or immediate access severed. Emergency ambulances cannot reach facility (e.g., Phadke Hospital near Deccan riverbed).
- **HIGH Tier ($75\text{ m} - 250\text{ m}$):** Perimeter roadways compromised; secondary access required (e.g., Paranjape Hospital).
- **MODERATE Tier ($250\text{ m} - 600\text{ m}$):** Peripheral advisory zone; localized stormwater surcharge.

### 3.2 Educational Facilities Exposure
Queried from PostGIS table `spatial_features` (`feature_type = 'EDUCATION'`, 30 total facilities):
- Any school or college within $400\text{ m}$ of the active flood polygon is automatically flagged as **COMPROMISED**.
- In accordance with NDMA guidelines, schools located within hazard buffers are disqualified from being designated as emergency relief shelters.

### 3.3 Bridge & Causeway Hydraulic Registry
Crossings along the Mula and Mutha are audited against hydraulic discharge ratings:

| Bridge / Crossing | Waterway | Structure Type | Submersion Threshold | Vulnerability Note |
| :--- | :--- | :--- | :---: | :--- |
| **Baba Bhide Causeway** | Mutha | Low-Level Concrete Causeway | **15,000 cfs** | First crossing to submerge; flooded by 2.5m at 35k cfs. |
| **Pulachi Wadi Footbridge** | Mutha | Low-Level Pedestrian Causeway | **18,000 cfs** | Highly vulnerable to surge; immediately submerged. |
| **Sangam Confluence Bridge** | Mula-Mutha | Multi-span Girder Bridge | **38,000 cfs** | Backwater from Mula-Mutha confluence threatens ramps. |
| **Dengle Bridge** | Mutha | Historic Masonry/Girder | **42,000 cfs** | Approaches inundate; connects Court to Kasba Peth. |
| **Bund Garden Bridges** | Mula-Mutha | Weir & High-Level Road Bridge | **45,000 cfs** | Downstream backwater surcharge near Pune Station. |
| **Holkar Bridge** | Mula | High-Level Girder Bridge | **45,000 cfs** | Major connection between Khadki and Yerawada. |
| **SM Joshi Bridge** | Mutha | High-Level Elevated Deck | **48,000 cfs** | Passable during moderate-severe events; deck elevated. |

### 3.4 Road Transportation Disruption
Queried from PostGIS table `spatial_features` (`feature_type = 'EVACUATION_ROAD'`, 906 features, 164.5 km):
- Identifies all road centerlines within $15\text{ m}$ of the flood boundary.
- Calculates exact inundated roadway kilometers and percentage of network blocked.
- Automatically flags disrupted primary corridors (e.g., Deccan Gymkhana Riverbed Link Road, Pulachi Wadi Approach, Karve Road ramps).

---

## 4. POPULATION EXPOSURE ESTIMATION METHODOLOGY

### 4.1 Demographic Disaggregation Basis
Central Pune riparian wards (Kasba Peth, Shivajinagar Riverfront, Bhavani Peth, Yerawada) feature dense settlement patterns with an empirical demographic density of:
$$\rho_{\text{riverfront}} \approx 28,000\text{ persons / km}^2$$

### 4.2 Mathematical Exposure Formulation
The central population exposure estimate $P_{\text{est}}$ is calculated as:
$$P_{\text{est}} = A_{\text{flooded}} \times \rho_{\text{riverfront}}$$

To acknowledge spatial disaggregation and census estimation uncertainty, explicit confidence bounds are reported:
- **Lower Bound:** $P_{\text{lower}} = P_{\text{est}} \times 0.70$ ($-30\%$)
- **Upper Bound:** $P_{\text{upper}} = P_{\text{est}} \times 1.35$ ($+35\%$)

### 4.3 Mandatory Estimation Caveats
- Estimates represent daytime/nighttime ambient residential density proxy.
- Actual exposure varies significantly based on multi-story building verticality, ground-floor usage, and real-time citizen evacuation compliance.

---

## 5. AUDITED HISTORICAL BENCHMARK SCENARIOS

The impact engine provides calibrated comparisons against historical Pune disaster records:

| Scenario / Event | Date | Dam Discharge | 24h Rain | Exposed Pop (Est) | Inundated Roads | Submerged Bridges | Primary Affected Sectors |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Baseline Normal** | Seasonal | 2,500 cfs | 0.0 mm | 0 | 0.0 km | 0 | Normal channel flow; zero infrastructure disruption. |
| **July 2024 Disaster** | 2024-07-25 | 35,574 cfs | 114.2 mm | 18,200 | 4.8 km | 2 | Baba Bhide & Pulachi Wadi submerged; Deccan riverbed cut off; Patil Estate inundated. |
| **August 2019 Mega Flood** | 2019-08-04 | 45,400 cfs | 128.5 mm | 26,500 | 7.2 km | 4 | 4 causeways submerged; major citywide evacuations across Shivajinagar & Yerawada. |
| **September 2019 Flash Flood** | 2019-09-25 | 12,000 cfs | 106.0 mm (3h) | 14,000 | 5.1 km | 1 | Southern nala pluvial cloudburst (Ambil Odha); Katraj/Sahakar Nagar urban inundation. |

---

## 6. API ENDPOINTS & SYSTEM INTEGRATION

| Endpoint | Method | Response Model | Description |
| :--- | :---: | :--- | :--- |
| `/api/v1/impact/latest` | `GET` | `ImpactAssessmentResponse` | Generates baseline impact assessment using verified Sentinel-1 SAR extent. |
| `/api/v1/impact/assess` | `POST` | `ImpactAssessmentResponse` | Simulates multi-sector impact for custom Khadakwasla discharge ($Q$) and rain ($R$). |
| `/api/v1/impact/scenarios` | `GET` | `ImpactScenariosResponse` | Returns audited historical disaster benchmark comparisons. |
| `/api/v1/impact/layers` | `GET` | `ImpactLayersResponse` | Returns GeoJSON FeatureCollections for SAR polygons, exposed facilities, and bridges. |

