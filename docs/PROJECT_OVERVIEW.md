# FLOOD-X — Project Overview

> **Tagline:** PREDICT | PRIORITIZE | PROTECT  
> **Target Event:** PCCOE International Grand Challenge 2026  
> **Pilot Geography:** Pune / Mula-Mutha River Basin, Maharashtra, India  
> **Development Phase:** Phase 0 (Foundation & System Architecture)

---

## 1. Executive Summary

FLOOD-X is an enterprise-grade, AI-powered flood-to-action intelligence and disaster decision-support platform designed to protect lives, safeguard critical infrastructure, and empower municipal disaster management authorities.

Traditional flood warning systems rely on static threshold alerts that fail to give actionable, location-specific intelligence. FLOOD-X bridges this gap by unifying multi-source environmental telemetry, physics-informed hydrodynamic simulations, explainable AI, safe evacuation graph pathfinding, and emergency resource optimization into an integrated, dual-interface platform:
1. **FLOOD-X Authority Dashboard**: An situational awareness command cockpit for municipal commissioners, disaster management cells (PMC/PCMC), and emergency responders (NDRF/SDRF).
2. **FLOOD-X Citizen Android App**: A localized, battery-efficient mobile client providing citizen alerts, safe evacuation routing, nearby high-ground shelters, and offline SOS capabilities.

---

## 2. Geographical Focus: The Pune Pilot Basin

The initial deployment targets the **Pune Metropolitan Region (PMRDA)**, specifically the **Mula-Mutha River Basin**.

### Why the Mula-Mutha Basin?
- **Extreme Topographical Vulnerability**: Formed by the confluence of the Mula and Mutha rivers in the heart of Pune city, bounded by upstream dams (Khadakwasla, Panshet, Varasgaon, Mulshi, and Pawana).
- **Urban Encroachment & Low-Lying Hotspots**: Chronic monsoon inundation across low-lying settlements (Sinhagad Road, Pulachi Wadi, Sangamwadi, Holkar Bridge, Yerawada, and Deccan Gymkhana).
- **Dam Discharge Dynamics**: High-volume monsoon discharges from Khadakwasla Dam (exceeding 30,000–50,000 cusecs) lead to rapid downstream flash-flooding within 2 to 4 hours, requiring real-time time-to-impact calculations.

---

## 3. Platform Capabilities & Architecture Scope

FLOOD-X is architected as an extensible monorepo with 12 modular subsystems delivered incrementally across six structured phases:

1. **Multi-Source Environmental Data Ingestion**: Automated ingestion from Indian Meteorological Department (IMD), Central Water Commission (CWC), Pune Municipal Corporation (PMC) IoT river level gauges, and dam release telemetry.
2. **AI/ML Flood-Risk Prediction Engine**: Hydrological runoff and machine learning flood extent regression models.
3. **Vulnerability & Population Exposure Analysis**: Socio-economic ward profiling, demographic vulnerability mapping, and critical asset overlays (hospitals, substations, schools).
4. **Time-to-Impact Estimation**: Hydrodynamic wave propagation velocity modeling predicting flood crest arrival times downstream.
5. **GIS-Based Flood Visualization**: Dynamic PostGIS spatial layers, digital elevation models (DEM), and interactive catchment maps.
6. **Dynamic Evacuation & Safe Routing**: Real-time pathfinding algorithms that route citizens around inundated road networks and submerged bridges.
7. **Shelter Capacity Management**: Real-time shelter registry with live occupancy, relief material logistics, and medical support tracking.
8. **Emergency Resource Optimization**: Constraint-based dispatch optimization using Google OR-Tools for rescue boats, ambulances, NDRF personnel, and pumps.
9. **Nugen Aligned-Model Decision Intelligence**: Explainable natural language operational guidance aligned with National Disaster Management Authority (NDMA) Standard Operating Procedures (SOPs).
10. **What-If Scenario Simulation**: Interactive scenario runners allowing disaster commanders to simulate varying dam discharge levels (e.g., 40,000 cusecs vs. 80,000 cusecs) and review predicted flood footprints before opening floodgates.
11. **Authority Web Dashboard**: High-density React + TypeScript + Vite command center with real-time status reporting and spatial maps.
12. **Citizen Android Application**: React Native / Expo mobile app built for battery efficiency, low-bandwidth resilience, and clear emergency notifications.

---

## 4. Phase 0 Implementation Scope & Strict Boundary

Phase 0 establishes the software foundation, API contracts, database connections, and project structures.

In strict adherence to the **Phase 0 Boundary**:
- **NO** fabricated or simulated flood heatmaps are displayed on the frontend.
- **NO** mock live environmental sensor streams are presented as operational.
- **NO** machine learning models are trained or pretended to run.
- **ALL** future modules are explicitly tagged as `planned` or `not_configured`.
- The architecture is verified with end-to-end running servers, health discovery, and tolerance to degraded database states.

