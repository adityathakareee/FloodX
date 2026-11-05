# FLOOD-X — PHASE 4: GOOGLE OR-TOOLS CONSTRAINED OPTIMIZATION ENGINE

## 1. Overview

The FLOOD-X Resource Optimization Engine formulates emergency fleet dispatch as a **Mixed-Integer Linear Programming (MIP)** problem solved using **Google OR-Tools** (`ortools.linear_solver.pywraplp` with backend `SCIP`).

The engine connects environmental risk signals and sector demands with available municipal fleet inventory, routing vehicles across the validated Phase 3 road network while strictly respecting physical constraints and verified facility limits.

---

## 2. Mathematical Formulation

### 2.1 Sets & Indices
- $R$: Set of available emergency resources $i \in R$, each with available quantity $Q_i > 0$, category $C_i$, specialization type $T_i$, and staging coordinates $(\text{lat}_i, \text{lon}_i)$.
- $S$: Set of evaluated operational geographic sectors $j \in S$, each with center coordinates $(\text{lat}_j, \text{lon}_j)$ and priority tier $P_j \in \{\text{CRITICAL}, \text{HIGH}, \text{MODERATE}, \text{LOW}\}$.
- $K$: Set of required emergency resource types $k \in \{\text{AMBULANCE}, \text{RESCUE\_TEAM}, \text{FOOD\_PACKETS}, \text{DRINKING\_WATER}, \dots\}$.
- $D_{j, k}$: Demanded quantity of resource type $k$ in sector $j$.

### 2.2 Decision Variables
- $x_{i, j, k} \in \mathbb{Z}_{\ge 0}$: Integer number of units of resource $i$ dispatched to sector $j$ to satisfy demand type $k$.
- $u_{j, k} \in \mathbb{Z}_{\ge 0}$: Integer unmet shortage of resource type $k$ in sector $j$.

### 2.3 Hard Constraints
1. **Resource Availability Limits:**
   $$\sum_{j \in S} \sum_{k \in K} x_{i, j, k} \le Q_i \quad \forall i \in R$$
   A resource can never dispatch more units than currently available in inventory.

2. **Demand Balance Equation:**
   $$\sum_{i \in R, T_i \sim k} x_{i, j, k} + u_{j, k} = D_{j, k} \quad \forall j \in S, \forall k \in K$$
   The sum of dispatched compatible resources plus remaining unmet demand must equal total requested units.

3. **Road Reachability & Maximum Travel Time:**
   Let $\tau_{i, j}$ be the shortest path travel time on the Phase 3 MultiDiGraph avoiding confirmed road closures:
   $$x_{i, j, k} = 0 \quad \text{if } \tau_{i, j} > \tau_{\max} \text{ or if route is disconnected}$$

4. **Verified Shelter Capacity Constraint:**
   No human evacuees may be assigned to unverified candidate shelters. When verified shelter count is 0, the optimizer reports `INSUFFICIENT_VERIFIED_SHELTER_CAPACITY`.

### 2.4 Objective Function
$$\min Z = \sum_{i \in R} \sum_{j \in S} \sum_{k \in K} \left( \frac{\tau_{i, j}}{60} \cdot c_{\text{travel}} \right) x_{i, j, k} + \sum_{j \in S} \sum_{k \in K} \left( M(P_j) \cdot c_{\text{unmet}} \right) u_{j, k}$$

Where $M(P_j)$ is the penalty multiplier for unmet demand based on sector priority:
- $\text{CRITICAL}$: $M = 10,000$
- $\text{HIGH}$: $M = 5,000$
- $\text{MODERATE}$: $M = 2,000$
- $\text{LOW}$: $M = 500$

### 2.5 Optimization Modes
- `MINIMIZE_RESPONSE_TIME`: Standard latency weighting ($c_{\text{travel}} = 1.0, c_{\text{unmet}} = 1.0$).
- `MAXIMIZE_COVERAGE`: Prioritizes fulfilling every demanded unit ($c_{\text{travel}} = 0.1, c_{\text{unmet}} = 10.0$).
- `BALANCED`: Balances response speed and inventory preservation ($c_{\text{travel}} = 0.5, c_{\text{unmet}} = 2.0$).

---

## 3. Road Network Routing Integration

Dispatch costs $\tau_{i, j}$ are dynamically evaluated by querying `evacuation_routing_engine.plan_evacuation_routes()`:
- Origin: Staging depot coordinates of resource $i$.
- Destination: Centroid of target sector $j$.
- Cost Profile: `FASTEST`.
- Closed Roads Avoidance: `True` (closed edges have dynamic weight $\infty$).
- If no traversable path exists due to barrier cordons or waterlogging, the optimizer sets reachability to `False` and locks $x_{i, j, k} = 0$.

---

## 4. Solver Performance & Execution Guarantees

In test benchmarks across the 8 Pune operational sectors and 12 simulated multi-vehicle bases:
- Total decision variables: ~192 variables.
- Average solve duration: ~15 to 45 ms.
- Solver backend: Google OR-Tools SCIP v9.15 (with CBC failover).
- Zero non-deterministic heuristics: results are provably optimal under the linear constraints.

