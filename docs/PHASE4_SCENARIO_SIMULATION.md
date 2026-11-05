# FLOOD-X — PHASE 4: WHAT-IF DISASTER SCENARIO SIMULATION

## 1. Overview & Objectives

Emergency management authorities must evaluate system resilience under worst-case disaster scenarios before a catastrophic monsoon event occurs. The FLOOD-X **What-If Disaster Scenario Simulation Engine** enables incident commanders to test multi-sector resource sufficiency under extreme hydrological stress, compound dam releases, and fleet disruptions.

---

## 2. Configurable Scenario Parameters

Authorities can calibrate drill scenarios across 5 independent disaster dimensions:

| Parameter | Type & Range | Description |
|---|---|---|
| `rainfall_multiplier` | Float (0.5x – 5.0x) | Precipitation escalation multiplier simulating localized convective cloudbursts. |
| `dam_discharge_cfs` | Float (0 – 100,000 cfs) | Simulated Khadakwasla Dam spillway discharge rate into the Mutha River channel. |
| `resource_availability_factor` | Float (0.10 – 1.00) | Available fleet ratio (e.g. 0.70 simulates 30% of emergency vehicles immobilized or delayed). |
| `demand_surge_factor` | Float (0.5x – 4.0x) | Escalation of citizen rescue and medical assistance requests during peak flooding. |
| `additional_closed_edge_ids` | List[str] (Optional) | Specific road graph edge IDs to simulate as impassable due to fallen trees or landslides. |

---

## 3. Khadakwasla Dam Inundation Benchmarks

Drawing upon the Phase 2.3.1 scientific threshold audit, the simulation engine automatically maps discharge rates to verified physical inundation benchmarks along the Mutha River corridor:

- **$\ge$ 15,000 cfs:** **Baba Bhide Low-Level Causeway Submerged.** The primary low-water crossing between Deccan Gymkhana and Alka Talkies Chowk becomes completely impassable to vehicular and pedestrian traffic.
- **$\ge$ 35,000 cfs:** **Deccan Riverbank Inundation.** Pulachi Wadi riverbank settlements and the riverside DP road experience overbank water ingress.
- **$\ge$ 45,000 cfs:** **Sinhagad Road Severe Backwater Flooding.** Backwater pooling from downstream bottlenecks causes severe ground-floor flooding in Ekta Nagari and Anand Nagar.
- **$\ge$ 70,000 cfs:** **Basin-Wide Catastrophic Confluence Flooding.** Overbank inundation extends across the Mula-Mutha confluence at Sangamwadi, Bund Garden, and Yerawada margins.

---

## 4. In-Memory Isolation Guarantee

### Architectural Safeguard:
All calculations, road weight alterations, demand scalings, and OR-Tools optimization runs are executed **strictly in volatile process memory**.

```
Live Production Database             Isolated Simulation Sandbox (RAM)
------------------------             --------------------------------
[Active Road Closures]               [Simulated Impassable Edges]
[Persistent Resources]   == (Copy) =>[Scaled Fleet Quantities]
[Official Allocations]               [Ephemeral Optimization Runs]
   (ZERO MUTATIONS)                     (Discarded after Response)
```

The response payload explicitly returns:
```json
{
  "isolation_guarantee": "CONFIRMED: This scenario simulation operated strictly in-memory. No database records, confirmed road closures, or real resource quantities were altered."
}
```
Automated regression tests verify that row counts in `emergency_resources` and `road_closures` are identical before and after simulation runs.

---

## 5. Comparative Delta Metrics

The engine executes dual optimization runs (Baseline vs Simulated) to compute operational delta metrics:
1. **Total Resource Demand Units:** Baseline vs simulated demand units with percentage increase.
2. **Demand Coverage Percentage:** Measures degradation in system service capacity (e.g., from 92% down to 68%).
3. **Total Emergency Response Time:** Evaluates travel-time latency degradation across all dispatched units.
4. **Simulated Inundated Road Segments:** Quantifies newly isolated network links.

