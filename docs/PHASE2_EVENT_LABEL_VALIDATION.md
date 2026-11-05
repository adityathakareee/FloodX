# FLOOD-X — Phase 2.2: Historical Event Label Validation & Audit
**Project:** FLOOD-X: AI-Powered Flood-to-Action Decision Intelligence Platform  
**Pilot Region:** Pune / Mula-Mutha River Basin, Maharashtra, India  
**Scope:** Forensic Audit of Historical Flood Events Overlapping Available Weather Time Series (2020–2024)  
**Date:** November 2026  
**Status:** COMPLETED & APPROVED WITH LIMITATIONS  

---

## 1. Executive Summary

While the master Pune historical catalog spans 140 events across 1969–2024, the continuous 9-variable hourly meteorological reanalysis covers **January 1, 2020 to December 31, 2024 (5 calendar years)**.

A forensic audit of all raw entries in the **India Flood Inventory (IFI-Impacts, Zenodo:16994648)** and **Maharashtra Water Resources Department (WRD)** records overlapping the 2020–2024 window was conducted. The audit resolved three major empirical data challenges:
1. **Inverted Date Formats:** Identified records where dates were recorded in US `MM-DD-YYYY` rather than Indian `DD-MM-YYYY`, which previously resulted in 60-day calendar displacements.
2. **Duplicate Administrative Slices:** Identified multiday national flood disasters recorded across multiple duplicate rows (e.g., district-specific vs state-aggregate entries in July 2021).
3. **Rural Agricultural Flagging:** Filtered out unseasonal winter/spring rain events that caused rabi crop damage in rural tehsils (Junnar, Ambegaon, Shirur) without producing urban pluvial or riverine inundation in the Pune / Mula-Mutha pilot basin.

### Audit Summary Statistics
- **Total Raw Candidates in 2020–2024 Window:** 28 IFI records + 1 WRD Ground-Truth event = 29 candidates.
- **Date-Inverted Records Corrected:** 3 events (Aug 2020, Sept 2020, Oct 2020).
- **Duplicate Administrative Records Consolidated:** 5 entries.
- **Flagged / Excluded Non-Urban-Flood Entries:** 12 entries (8 rural crop damage, 1 non-basin river, 1 localized landslide, 2 rain-without-damage).
- **Unique Validated Physical Flood Events:** **11 distinct events**.
- **Total Verified Positive Flood Days:** **39 calendar days** ($2.13\%$ of $1,827$ days).

---

## 2. In-Depth Forensic Event-by-Event Audit Table

The table below catalogs all 29 candidate records evaluated during Phase 2.2:

| Raw Index / ID | Raw Recorded Dates | Validated Calendar Dates | Duration | Primary Driver | Reported Fatalities | Classification & Audit Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **WRD-2024-01** | 2024-07-24 to 2024-07-26 | **2024-07-24 to 2024-07-26** | 3.0 days | `COMBINED` | 4 deaths in Pune | **TIER 1 GROUND TRUTH VERIFIED.** Khadakwasla Dam release peaked at 35,574 cfs. Inundated Ekta Nagari (Sinhagad Rd) to 2.5m depth, submerged Baba Bhide Bridge and Pulachi Wadi. |
| **IFI-4668** | 03-01-2020 | 2020-01-03 | 1.0 day | Heavy Rains | 0 | **FLAGGED: RURAL AGRICULTURAL.** Unseasonal January rain causing damage to rabi wheat/onion crops across 10 rural districts. Zero urban/riverine flood in Pune basin. |
| **IFI-4675** | 20-07-2020 | 2020-07-20 | 1.0 day | Landslide | 0 | **FLAGGED: LANDSLIDE ONLY.** Single vehicle damaged on Western Ghats pass road; zero inundation reported in river corridors. |
| **IFI-4678** | `08-04-2020` to `08-06-2020` | **2020-08-04 to 2020-08-06** | 3.0 days | `COMBINED` | 2 deaths | **DATE-CORRECTED & VALIDATED.** Raw date had inverted format (`MM-DD-YYYY`: Month 08, Days 04 to 06). Confirmed by damage notes mentioning D.Y. Patil stadium windstorm on August 5, 2020. |
| **IFI-4685** | `09-05-2020` to `09-08-2020` | **2020-09-05 to 2020-09-08** | 4.0 days | `URBAN_PLUVIAL` | 0 | **DATE-CORRECTED & VALIDATED.** Raw date was `MM-DD-YYYY` (Sept 5 to Sept 8, 4 days). Intense convective pre-depression rainfall, shop and basement inundation. |
| **IFI-4689** | 19-09-2020 to 24-09-2020 | **2020-09-19 to 2020-09-24** | 6.0 days | `COMBINED` | 10 deaths | **VALIDATED ADMINISTRATIVE EVENT.** 6-day monsoon depression causing widespread riverine swell, compound wall collapse, and severe traffic gridlock. |
| **IFI-4695** | `10-10-2020` to `10-12-2020` | **2020-10-10 to 2020-10-12** | 3.0 days | `COMBINED` | 1 death | **DATE-CORRECTED & VALIDATED.** Raw date was `MM-DD-YYYY` (Oct 10 to Oct 12, 2-3 days). Precursor squall lines preceding Deep Depression BOB 02. |
| **IFI-4697** | 14-10-2020 | **2020-10-14 to 2020-10-20** | 7.0 days | `COMBINED` | 36 deaths (region) | **VALIDATED ADMINISTRATIVE EVENT.** The catastrophic Deep Depression BOB 02 deluge. Inundated 18,746 ha in Pune, rivers breached floodlines, 36 regional deaths. |
| **IFI-4698** | 15-10-2020 | Consolidated | — | `COMBINED` | — | **DUPLICATE CONSOLIDATION.** Intermediate daily report of continuous Oct 14–20 event. |
| **IFI-4700** | 16-10-2020 | Consolidated | — | `COMBINED` | 29 | **DUPLICATE CONSOLIDATION.** Peak casualty report of continuous Oct 14–20 event. |
| **IFI-4702** | 18-10-2020 to 20-10-2020 | Consolidated | — | `COMBINED` | — | **DUPLICATE CONSOLIDATION.** Inundation report of continuous Oct 14–20 event. |
| **IFI-4888** | 07-01-2021 to 08-01-2021 | 2021-01-07 | 2.0 days | Heavy Rains | 0 | **FLAGGED: RURAL AGRICULTURAL.** January unseasonal showers in rural tehsils. |
| **IFI-4891** | 18-02-2021 to 19-02-2021 | 2021-02-18 | 2.0 days | Unseasonal Rains | 0 | **FLAGGED: RURAL AGRICULTURAL.** February hailstorm affecting rural rabi crops. |
| **IFI-4894** | 14-04-2021 | 2021-04-14 | 1.0 day | Heavy Rains | 0 | **FLAGGED: RURAL AGRICULTURAL.** Pre-monsoon localized convective thunderstorm. |
| **IFI-4940** | 22-07-2021 to 26-07-2021 | **2021-07-22 to 2021-07-26** | 5.0 days | `COMBINED` | 1 death (Pune) | **VALIDATED ADMINISTRATIVE EVENT.** Historic Western Ghats monsoon deluge (Mahabaleshwar recorded 1,100 mm in 3 days; extreme catchment runoff into Pune rivers). |
| **IFI-4941** | 22-07-2021 to 26-07-2021 | Consolidated | — | `COMBINED` | — | **DUPLICATE CONSOLIDATION.** Exact duplicate entry of row 4940 (district-level slice). |
| **IFI-4939** | 26-07-2021 | Consolidated | — | `COMBINED` | — | **DUPLICATE CONSOLIDATION.** Final day peak slice of continuous July 22–26 event. |
| **IFI-4982** | 06-10-2021 | 2021-10-06 | 1.0 day | Heavy Rains | 0 | **FLAGGED: NON-BASIN RIVER.** Cause notes explicitly cite the "Girija River", which is in Aurangabad/Jalna district, not in the Pune / Mula-Mutha basin. |
| **IFI-4985** | 09-10-2021 | **2021-10-09** | 1.0 day | `COMBINED` | 0 | **VALIDATED ADMINISTRATIVE EVENT.** Monsoon withdrawal active depression. |
| **IFI-4989** | 01-12-2021 to 02-12-2021 | 2021-12-01 | 2.0 days | Heavy Rains | 0 | **FLAGGED: RURAL AGRICULTURAL.** December post-cyclonic unseasonal shower. |
| **IFI-5708** | 10-06-2022 | 2022-06-10 | 1.0 day | Heavy Rains | 0 | **FLAGGED: MONSOON ONSET.** Seasonal onset showers with zero inundation. |
| **IFI-5730** | 11-07-2022 | **2022-07-11 to 2022-07-13** | 3.0 days | `COMBINED` | 2 deaths | **VALIDATED ADMINISTRATIVE EVENT.** Active mid-monsoon flood spell with riverbank warnings. Consolidated with row 5743. |
| **IFI-5743** | 13-07-2022 | Consolidated | — | `COMBINED` | — | **DUPLICATE CONSOLIDATION.** Merged into July 11–13, 2022 sequence. |
| **IFI-5790** | 11-09-2022 | 2022-09-11 | 1.0 day | Heavy Rains | 0 | **FLAGGED: RAIN NO INUNDATION.** Moderate localized rain with zero flood damage. |
| **IFI-5804** | 16-09-2022 | **2022-09-16** | 1.0 day | `URBAN_PLUVIAL` | 1 death | **VALIDATED ADMINISTRATIVE EVENT.** Intense evening cloudburst causing flash runoff in urban storm nalas; 1 drowning. |
| **IFI-5825** | 17-10-2022 to 19-10-2022 | **2022-10-17 to 2022-10-19** | 3.0 days | `URBAN_PLUVIAL` | 2 deaths | **VALIDATED ADMINISTRATIVE EVENT.** Late-monsoon convective cloudburst causing severe urban underpass and nullah overtopping; 2 fatalities. |
| **IFI-6637** | 14-03-2023 to 17-03-2023 | 2023-03-14 | 4.0 days | Unseasonal Rains | 0 | **FLAGGED: RURAL AGRICULTURAL.** Spring hailstorm destroying rabi harvest in rural Junnar/Shirur tehsils. |
| **IFI-6656** | 09-04-2023 to 10-04-2023 | 2023-04-09 | 2.0 days | Heavy Rains | 0 | **FLAGGED: RURAL AGRICULTURAL.** April pre-monsoon convective shower in rural tehsils. |
| **IFI-6657** | 15-04-2023 | 2023-04-15 | 1.0 day | Heavy Rains | 0 | **FLAGGED: RURAL AGRICULTURAL.** Localized spring storm in rural tehsils. |

---

## 3. The 11 Validated Physical Flood Events

The 11 verified events and their continuous calendar dates are summarized below:

```
+----+-------------------+-------------------------+-----------+----------------------+----------------------------------------------------------+
| #  | Event Identifier  | Calendar Dates (ISO)    | Days (n)  | Primary Driver       | Geographic Corridor & Verified Physical Impacts          |
+----+-------------------+-------------------------+-----------+----------------------+----------------------------------------------------------+
| 1  | PUNE-FLD-2024-01  | 2024-07-24 to 2024-07-26| 3 days    | COMBINED             | Sinhagad Rd (Ekta Nagari 2.5m depth), Bhide Bridge (3m)  |
| 2  | PUNE-IFI-2022-10A | 2022-10-17 to 2022-10-19| 3 days    | URBAN_PLUVIAL        | Pune urban stream corridors & low-lying underpasses      |
| 3  | PUNE-IFI-2022-09A | 2022-09-16              | 1 day     | URBAN_PLUVIAL        | Pune city stormwater network & nalas                     |
| 4  | PUNE-IFI-2022-07A | 2022-07-11 to 2022-07-13| 3 days    | COMBINED             | Mutha & Mula riverbank low-lying settlements             |
| 5  | PUNE-IFI-2021-10A | 2021-10-09              | 1 day     | COMBINED             | Pune District river corridors                            |
| 6  | PUNE-IFI-2021-07A | 2021-07-22 to 2021-07-26| 5 days    | COMBINED             | Western Ghats dam catchments & downstream Mutha river    |
| 7  | PUNE-IFI-2020-10B | 2020-10-14 to 2020-10-20| 7 days    | COMBINED             | Deep Depression BOB 02: 18,746 ha flooded in Pune Dist.  |
| 8  | PUNE-IFI-2020-10A | 2020-10-10 to 2020-10-12| 3 days    | COMBINED             | Precursor depression squall lines & riverbank rise       |
| 9  | PUNE-IFI-2020-09B | 2020-09-19 to 2020-09-24| 6 days    | COMBINED             | Monsoon depression; widespread inundation & gridlock     |
| 10 | PUNE-IFI-2020-09A | 2020-09-05 to 2020-09-08| 4 days    | URBAN_PLUVIAL        | Pre-depression convective downpours; shop flooding       |
| 11 | PUNE-IFI-2020-08A | 2020-08-04 to 2020-08-06| 3 days    | COMBINED             | Intense coastal/ghat monsoon storm; river alert          |
+----+-------------------+-------------------------+-----------+----------------------+----------------------------------------------------------+
Total Validated Positive Flood Days: 39 Days
```

---

## 4. Evidentiary Guardrails & Compliance

1. **Sangli Gauge Quarantine:** Station `014-MDNURG` (Ankali Bridge, Krishna Basin, 205.3 km away) was **quarantined** and never used in feature calculation or label definition.
2. **No Proxy Conversions:** Environmental indicators ($\text{HAND} < 2\text{ m}$, river buffer $< 100\text{ m}$, rainfall $> 100\text{ mm}$) were **never** used as positive labels. Positive labels derive strictly from verified physical WRD release logs or authoritative IFI disaster impact reports.
3. **No Synthetic Balancing:** The training and evaluation sets contain **zero synthetic instances** (no SMOTE, no random jittering). The imbalanced class structure was respected and handled mathematically via loss reweighting (`scale_pos_weight`).

