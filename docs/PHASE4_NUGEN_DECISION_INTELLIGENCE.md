# FLOOD-X — PHASE 4: NUGEN DECISION INTELLIGENCE & NDMA SOP ADVISORY

## 1. Overview & Operational Principles

Emergency decision intelligence in FLOOD-X must bridge raw hydrological risk models and practical tactical field actions. During critical flood emergencies, municipal incident commanders require transparent, auditable, and actionable directives that adhere to statutory disaster management protocols.

---

## 2. Integration Architecture & Credential Handling

The Nugen Decision Intelligence subsystem operates under strict transparency principles:

```
                  +-----------------------------------+
                  |  Check Environment Configuration  |
                  |  (NUGEN_API_KEY, NUGEN_BASE_URL)  |
                  +-----------------------------------+
                                    |
                 +------------------+------------------+
                 |                                     |
         Credentials Present                  Credentials Missing
                 |                                     |
                 v                                     v
       +--------------------+               +-----------------------+
       |   NUGEN_API_LIVE   |               |  RULE_BASED_DECISION  |
       | Live Decision API  |               |  FALLBACK (Active)    |
       +--------------------+               +-----------------------+
                                                       |
                                            +-----------------------+
                                            |   NDMA Flood SOP      |
                                            |   Deterministic Rules |
                                            +-----------------------+
```

### Current Status:
- `is_available`: `False`
- `status`: `"NUGEN_UNAVAILABLE (Credentials Not Configured)"`
- `active_provider`: `"RULE_BASED_DECISION_FALLBACK"`
- `missing_configuration_notes`: Clear disclaimer indicating no mock requests were transmitted to unverified endpoints.

---

## 3. NDMA Standard Operating Procedure (SOP) Rule Matrix

When running the deterministic fallback engine, FLOOD-X applies structured rules derived from the **National Disaster Management Authority (NDMA) National Guidelines: Management of Floods (2008)** and the **Pune Municipal Corporation Disaster Management Plan**:

| Priority Tier | Trigger Condition | Tactical Actions Generated | Regulatory Reference |
|---|---|---|---|
| **CRITICAL** | Composite Score $\ge 70$ OR Low-lying DEM depression &lt; 550m | 1. Pre-position motorized swift water rescue boats & NDRF teams.<br>2. Stage Advanced Life Support (ALS) ambulances at dry perimeter.<br>3. Mandatory evacuation of low causeways. | NDMA Guidelines Sec 4.2 (Search & Rescue) & Sec 4.5 (Emergency Medical Care) |
| **HIGH** | Composite Score $50 - 69.9$ OR Causeway overflow risk | 1. Deploy Basic Life Support (BLS) ambulances outside flood fringe.<br>2. Position dewatering pump crews at underpasses.<br>3. Establish barrier checkpoints on low bridges.<br>4. Stockpile relief rations and water jerrycans. | NDMA Guidelines Sec 5.1 (Relief Camp Logistics) & Sec 6.3 (Perimeter Cordon) |
| **MODERATE** | Composite Score $35 - 49.9$ | 1. Monitor telemetry gauges and prospective rain forecasts.<br>2. Put secondary emergency vehicles on 15-minute standby. | NDMA Guidelines Sec 3.4 (Early Warning & Preparedness) |
| **LOW** | Composite Score &lt; 35 | Standard civil defense monitoring posture. | NDMA Guidelines Sec 3.1 |

---

## 4. Advisory Output Structure

Every generated decision advisory response envelope (`DecisionAdvisoryResponse`) contains:
- `advisory_id`: Unique identifier formatted as `ADV-PUNE-YYYYMMDD-XXXX`.
- `intelligence_provider`: Identifies whether live Nugen or NDMA SOP fallback generated the plan.
- `executive_summary`: High-level operational situation summary.
- `critical_observations`: List of key field findings (e.g. Sinhagad Road backwater risk, Baba Bhide causeway bridge submergence alert, fleet shortages).
- `priority_sector_rankings`: Ordered list of sectors with scores and primary risk drivers.
- `resource_shortage_summary`: Detailed breakdown of demanded vs available shortages.
- `tactical_action_plan`: Structured action cards citing specific NDMA SOP sections, assigned unit types, and urgency tiers (`IMMEDIATE (0-15 min)`, `HIGH (15-30 min)`).
- `route_caution_summary`: Bottleneck alerts for river crossings and low-lying arterial corridors.
- `ndma_compliance_notes`: Formal compliance statement.
- `official_disclaimer`: Emergency disclaimer reminding operators that advisory recommendations do not replace executive incident command authority.

