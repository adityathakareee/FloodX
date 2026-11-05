import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  Truck,
  Activity,
  Sliders,
  Sparkles,
  RefreshCw,
  Plus,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Compass,
  ArrowRight,
  Database,
  Building2,
  Users,
  Package,
  Layers,
  Key,
  Flame,
  Check,
  ChevronRight,
  Zap,
} from 'lucide-react';
import { apiService } from '../services/api';
import {
  ResourceItem,
  ResourceListResponse,
  DemandAssessmentResponse,
  DemandAssessmentItem,
  PriorityRankingResponse,
  PriorityAreaItem,
  OptimizationRunResponse,
  OptimizationAssignmentItem,
  ResourceAllocationItem,
  ScenarioSimulationResponse,
  NugenStatusResponse,
  DecisionAdvisoryResponse,
} from '../types/api';

export const CommandCenterPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'priorities' | 'inventory' | 'optimization' | 'simulation' | 'nugen'>('priorities');
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  // Authority token management
  const [tokenInput, setTokenInput] = useState<string>('');
  const [hasToken, setHasToken] = useState<boolean>(false);
  const [tokenMsg, setTokenMsg] = useState<string | null>(null);

  // State: Priorities & Demands
  const [priorities, setPriorities] = useState<PriorityAreaItem[]>([]);
  const [demands, setDemands] = useState<DemandAssessmentResponse | null>(null);

  // State: Inventory
  const [resources, setResources] = useState<ResourceItem[]>([]);
  const [resourceStats, setResourceStats] = useState<{ total: number; avail: number; alloc: number }>({ total: 0, avail: 0, alloc: 0 });
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [allocations, setAllocations] = useState<ResourceAllocationItem[]>([]);

  // State: Optimization
  const [optObjective, setOptObjective] = useState<'MINIMIZE_RESPONSE_TIME' | 'MAXIMIZE_COVERAGE' | 'BALANCED'>('MINIMIZE_RESPONSE_TIME');
  const [avoidRoadClosures, setAvoidRoadClosures] = useState<boolean>(true);
  const [maxTravelMinutes, setMaxTravelMinutes] = useState<number>(60);
  const [optimizationResult, setOptimizationResult] = useState<OptimizationRunResponse | null>(null);
  const [optLoading, setOptLoading] = useState<boolean>(false);

  // State: Scenario Simulation
  const [simRainMultiplier, setSimRainMultiplier] = useState<number>(1.5);
  const [simDamDischarge, setSimDamDischarge] = useState<number>(45000);
  const [simFleetAvailability, setSimFleetAvailability] = useState<number>(0.8);
  const [simDemandSurge, setSimDemandSurge] = useState<number>(1.3);
  const [simulationResult, setSimulationResult] = useState<ScenarioSimulationResponse | null>(null);
  const [simLoading, setSimLoading] = useState<boolean>(false);

  // State: Nugen Decision Intelligence
  const [nugenStatus, setNugenStatus] = useState<NugenStatusResponse | null>(null);
  const [advisory, setAdvisory] = useState<DecisionAdvisoryResponse | null>(null);
  const [advisoryLoading, setAdvisoryLoading] = useState<boolean>(false);

  // Initialize and check token
  useEffect(() => {
    const active = apiService.hasAuthorityToken();
    setHasToken(active);
    loadInitialData();
  }, [refreshTrigger]);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [prioRes, demRes, resList, allocList, nugStatus] = await Promise.allSettled([
        apiService.getPriorityRankings(),
        apiService.getDemandAssessments(),
        apiService.listResources(),
        apiService.listAllocations(),
        apiService.getNugenStatus(),
      ]);

      if (prioRes.status === 'fulfilled') setPriorities(prioRes.value.ranked_areas);
      if (demRes.status === 'fulfilled') setDemands(demRes.value);
      if (resList.status === 'fulfilled') {
        setResources(resList.value.items);
        setResourceStats({
          total: resList.value.total,
          avail: resList.value.available_total,
          alloc: resList.value.allocated_total,
        });
      }
      if (allocList.status === 'fulfilled') setAllocations(allocList.value);
      if (nugStatus.status === 'fulfilled') setNugenStatus(nugStatus.value);
    } catch (err) {
      console.error('Error loading command center data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveToken = () => {
    if (!tokenInput.trim()) {
      apiService.clearAuthorityToken();
      setHasToken(false);
      setTokenMsg('Authority token cleared (View-Only Mode).');
      return;
    }
    apiService.setAuthorityToken(tokenInput.trim());
    setHasToken(true);
    setTokenMsg('Authority credentials stored in memory.');
    setTokenInput('');
  };

  const handleSeedDrillData = async () => {
    try {
      const res = await apiService.seedDemoResources(true);
      alert(`Drill Inventory Seeded: ${res.count} realistic simulated resources populated.`);
      setRefreshTrigger((prev) => prev + 1);
    } catch (err: any) {
      alert(`Failed to seed demo resources. Ensure valid ADMIN Authority Token is set: ${err.message}`);
    }
  };

  const handleRunOptimization = async () => {
    setOptLoading(true);
    try {
      const res = await apiService.executeOptimization({
        objective: optObjective,
        avoid_closed_roads: avoidRoadClosures,
        max_travel_time_sec: maxTravelMinutes * 60,
        enforce_capacity_limits: true,
      });
      setOptimizationResult(res);
      setRefreshTrigger((prev) => prev + 1);
    } catch (err: any) {
      alert(`Optimization execution failed: ${err.message}. Admin Authority required.`);
    } finally {
      setOptLoading(false);
    }
  };

  const handleRunSimulation = async () => {
    setSimLoading(true);
    try {
      const res = await apiService.simulateScenario({
        scenario_name: `Disaster Drill (${simRainMultiplier}x Rain, ${simDamDischarge.toLocaleString()} cfs)`,
        rainfall_multiplier: simRainMultiplier,
        dam_discharge_cfs: simDamDischarge,
        resource_availability_factor: simFleetAvailability,
        demand_surge_factor: simDemandSurge,
      });
      setSimulationResult(res);
    } catch (err: any) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      setSimLoading(false);
    }
  };

  const handleGenerateAdvisory = async () => {
    setAdvisoryLoading(true);
    try {
      const res = await apiService.generateDecisionAdvisory({
        include_shortage_analysis: true,
        include_sop_guidelines: true,
      });
      setAdvisory(res);
    } catch (err: any) {
      alert(`Failed to generate advisory: ${err.message}`);
    } finally {
      setAdvisoryLoading(false);
    }
  };

  const handleApproveBatch = async () => {
    const proposed = allocations.filter((a) => a.status === 'PROPOSED');
    if (proposed.length === 0) {
      alert('No pending PROPOSED allocations to approve.');
      return;
    }
    try {
      const ids = proposed.map((p) => p.id);
      await apiService.approveAllocations(ids);
      alert(`Successfully approved and dispatched ${ids.length} resource allocations.`);
      setRefreshTrigger((prev) => prev + 1);
    } catch (err: any) {
      alert(`Approval failed: ${err.message}. Admin Authority token required.`);
    }
  };

  const filteredResources = selectedCategory === 'ALL'
    ? resources
    : resources.filter((r) => r.category === selectedCategory);

  return (
    <div className="space-y-6">
      {/* Top Header & Authority Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 text-xs font-bold rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                PHASE 4 OPERATIONAL
              </span>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                <Check className="w-3 h-3" /> OR-Tools MIP Solver Active
              </span>
            </div>
            <h1 className="text-2xl font-bold text-white mt-1">
              Authority Decision Intelligence & Resource Optimization
            </h1>
            <p className="text-slate-400 text-sm mt-0.5">
              Command Center for Multi-Sector Evacuation Prioritization, Fleet Constrained Optimization, and NDMA SOP Action Dispatch
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/vulnerability"
              className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20 border border-cyan-500/30 flex items-center gap-1.5 transition-colors"
              title="View Sentinel-1 SAR Multi-Sector Flood Impact Assessment"
            >
              <Users className="w-3.5 h-3.5 text-cyan-400" /> Flood Impact View
            </Link>
            <button
              onClick={handleSeedDrillData}
              className="px-3.5 py-2 text-xs font-medium rounded-lg bg-slate-800 text-slate-200 hover:bg-slate-700 border border-slate-700 flex items-center gap-1.5 transition-colors"
              title="Populates realistic simulated Pune fleet and relief items"
            >
              <Database className="w-3.5 h-3.5 text-indigo-400" /> Seed Drill Inventory
            </button>
            <button
              onClick={() => setRefreshTrigger((prev) => prev + 1)}
              className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700"
              title="Refresh telemetry"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Authority Token Input Mini-Bar */}
        <div className="mt-4 pt-3 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <Key className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-slate-300 font-medium">Command Authorization:</span>
            <span className={`px-2 py-0.5 rounded font-mono ${hasToken ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'}`}>
              {hasToken ? 'ADMIN_TOKEN_ACTIVE' : 'VIEW_ONLY'}
            </span>
            {tokenMsg && <span className="text-slate-400 italic ml-2">{tokenMsg}</span>}
          </div>
          <div className="flex items-center gap-2">
            <input
              type="password"
              placeholder="Paste X-Authority-Token..."
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-slate-200 placeholder-slate-500 text-xs focus:outline-none focus:border-indigo-500 w-52"
            />
            <button
              onClick={handleSaveToken}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-2.5 py-1 rounded text-xs transition-colors"
            >
              {tokenInput ? 'Save' : 'Clear'}
            </button>
          </div>
        </div>
      </div>

      {/* Primary KPI Ribbon */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>TRACKED ASSETS</span>
            <Truck className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-1">
            {resourceStats.avail} <span className="text-xs font-normal text-slate-400">/ {resourceStats.total} Avail</span>
          </div>
          <div className="text-xs text-indigo-400 mt-1 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-indigo-400 inline-block"></span>
            {resourceStats.alloc} Units Currently Allocated
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>SECTORS EVALUATED</span>
            <Compass className="w-4 h-4 text-red-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-1">
            {priorities.filter((p) => p.priority_level === 'CRITICAL_PRIORITY').length} <span className="text-xs font-normal text-red-400">Critical Priority</span>
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {priorities.filter((p) => p.priority_level === 'HIGH_PRIORITY').length} High / {priorities.length} Total Pilot Sectors
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>DEMAND ESTIMATE</span>
            <Activity className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-1">
            {demands ? demands.total_ambulances_demanded + demands.total_rescue_teams_demanded : '--'} <span className="text-xs font-normal text-slate-400">Urgent Units</span>
          </div>
          <div className="text-xs text-amber-400 mt-1">
            {demands ? `${demands.total_ambulances_demanded} Ambulances, ${demands.total_rescue_teams_demanded} Boats` : '--'}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>DECISION INTELLIGENCE</span>
            <Sparkles className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-white mt-1 flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
            {nugenStatus?.active_provider === 'NUGEN_API_LIVE' ? 'Nugen Live' : 'NDMA SOP Fallback'}
          </div>
          <div className="text-xs text-emerald-400 mt-1">
            Deterministic SOP Rules Active
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-slate-800 flex gap-2">
        <button
          onClick={() => setActiveTab('priorities')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'priorities'
            ? 'border-indigo-500 text-white bg-indigo-500/5'
            : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
        >
          <ShieldAlert className="w-4 h-4 text-indigo-400" /> 1. Priorities & Demand
        </button>
        <button
          onClick={() => setActiveTab('inventory')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'inventory'
            ? 'border-indigo-500 text-white bg-indigo-500/5'
            : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
        >
          <Package className="w-4 h-4 text-indigo-400" /> 2. Resource Inventory
        </button>
        <button
          onClick={() => setActiveTab('optimization')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'optimization'
            ? 'border-indigo-500 text-white bg-indigo-500/5'
            : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
        >
          <Zap className="w-4 h-4 text-indigo-400" /> 3. Google OR-Tools MIP
        </button>
        <button
          onClick={() => setActiveTab('simulation')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'simulation'
            ? 'border-indigo-500 text-white bg-indigo-500/5'
            : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
        >
          <Sliders className="w-4 h-4 text-indigo-400" /> 4. What-If Simulation
        </button>
        <button
          onClick={() => setActiveTab('nugen')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'nugen'
            ? 'border-indigo-500 text-white bg-indigo-500/5'
            : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
        >
          <Sparkles className="w-4 h-4 text-indigo-400" /> 5. AI Advisory (SOP)
        </button>
      </div>

      {/* ==================================================================== */}
      {/* TAB 1: Priorities & Multi-Sector Demand */}
      {/* ==================================================================== */}
      {activeTab === 'priorities' && (
        <div className="space-y-5">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-indigo-400" />
                  Multi-Factor Strategic Response Prioritization
                </h2>
                <p className="text-slate-400 text-xs mt-1">
                  Formula: <span className="font-mono text-indigo-300">0.35 × Risk + 0.30 × Demand + 0.20 × Accessibility + 0.15 × Infrastructure</span>
                </p>
              </div>
              <div className="text-xs text-slate-400 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
                8 Pune Operational Sectors Ranked
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold">
                    <th className="py-2.5 px-3">Rank</th>
                    <th className="py-2.5 px-3">Sector</th>
                    <th className="py-2.5 px-3">Priority Level</th>
                    <th className="py-2.5 px-3">Composite Score</th>
                    <th className="py-2.5 px-3">Primary Risk Driver</th>
                    <th className="py-2.5 px-3">Ambulances</th>
                    <th className="py-2.5 px-3">Rescue Boats</th>
                    <th className="py-2.5 px-3">Recommended SOP Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {priorities.map((item) => {
                    const secDemand = demands?.sectors.find((s) => s.sector_id === item.sector_id);
                    const isCritical = item.priority_level === 'CRITICAL_PRIORITY';
                    const isHigh = item.priority_level === 'HIGH_PRIORITY';

                    return (
                      <tr key={item.sector_id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-3 font-bold font-mono">
                          #{item.rank}
                        </td>
                        <td className="py-3 px-3 font-semibold text-white">
                          {item.sector_name}
                          {item.sector_id === 'PUNE_SEC_SINHAGAD' && (
                            <span className="block text-[10px] text-red-400 font-normal">
                              Elevation &lt; 550m (DEM Copernicus depression)
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-bold ${isCritical
                              ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                              : isHigh
                                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                              }`}
                          >
                            {item.priority_level.replace('_PRIORITY', '')}
                          </span>
                        </td>
                        <td className="py-3 px-3 font-mono font-bold text-white">
                          {item.priority_score.toFixed(1)} / 100
                        </td>
                        <td className="py-3 px-3 text-slate-300">
                          {item.primary_risk_driver}
                        </td>
                        <td className="py-3 px-3 font-mono">
                          {secDemand ? secDemand.required_ambulances : '--'}
                        </td>
                        <td className="py-3 px-3 font-mono">
                          {secDemand ? secDemand.required_rescue_teams : '--'}
                        </td>
                        <td className="py-3 px-3 text-slate-400 max-w-xs truncate" title={item.recommended_tactical_action}>
                          {item.recommended_tactical_action}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 2: Resource Inventory & Deployments */}
      {/* ==================================================================== */}
      {activeTab === 'inventory' && (
        <div className="space-y-5">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Package className="w-5 h-5 text-indigo-400" />
                  Emergency Resource & Fleet Inventory
                </h2>
                <p className="text-slate-400 text-xs mt-1">
                  Track real-time quantities of vehicles, swift water rescue teams, medical gear, and relief supplies
                </p>
              </div>

              {/* Category filter pills */}
              <div className="flex flex-wrap gap-1.5 text-xs">
                {['ALL', 'EMERGENCY_VEHICLE', 'HUMAN_RESOURCE', 'RELIEF_RESOURCE'].map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                    className={`px-3 py-1 rounded-lg border transition-colors ${selectedCategory === cat
                      ? 'bg-indigo-600 text-white border-indigo-500 font-semibold'
                      : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200'
                      }`}
                  >
                    {cat.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>

            {/* Simulated Baseline Notice */}
            {resources.length > 0 && resources.every((r) => r.is_simulated || r.verification_status !== 'VERIFIED') && (
              <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-xs text-amber-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                <span>
                  <strong>Simulated Baseline Fleet Notice:</strong> 0 verified municipal emergency assets exist in the active database. All {resources.length} inventory records are flagged as <code>SIMULATED</code> for drill scenarios and tactical evaluation.
                </span>
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold">
                    <th className="py-2.5 px-3">Resource Code</th>
                    <th className="py-2.5 px-3">Name</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3">Base Location</th>
                    <th className="py-2.5 px-3 text-right">Available</th>
                    <th className="py-2.5 px-3 text-right">Allocated</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Authority</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {filteredResources.map((res) => (
                    <tr key={res.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-2.5 px-3 font-mono font-semibold text-indigo-300">
                        {res.resource_id}
                      </td>
                      <td className="py-2.5 px-3 font-medium text-white">
                        {res.name}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">
                        {res.category.replace('_', ' ')}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[11px]">
                        {res.resource_type}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">
                        {res.base_address || res.assigned_location_name || 'Central Depo'}
                      </td>
                      <td className="py-2.5 px-3 text-right font-bold text-emerald-400 font-mono">
                        {res.available_quantity}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono text-slate-400">
                        {res.allocated_quantity}
                      </td>
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${res.operational_status === 'AVAILABLE'
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                              : res.operational_status === 'ALLOCATED'
                                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                : 'bg-slate-700 text-slate-300'
                              }`}
                          >
                            {res.operational_status}
                          </span>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold ${res.verification_status === 'VERIFIED'
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                              : 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
                              }`}
                          >
                            {res.verification_status || (res.is_simulated ? 'SIMULATED' : 'UNVERIFIED')}
                          </span>
                        </div>
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 truncate max-w-[120px]">
                        {res.responsible_authority}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Proposed Allocations & Approval Sub-Panel */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Dispatch Proposals & Active Deployments
                </h3>
                <p className="text-slate-400 text-xs mt-0.5">
                  Review assignments generated by Google OR-Tools or manual dispatches before approving deployment
                </p>
              </div>
              <button
                onClick={handleApproveBatch}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
              >
                <Check className="w-3.5 h-3.5" /> Approve Pending Dispatches
              </button>
            </div>

            {allocations.length === 0 ? (
              <div className="text-center py-6 text-slate-500 text-xs">
                No active or proposed allocations found. Execute an OR-Tools optimization run in Tab 3 to generate proposals.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase font-semibold">
                      <th className="py-2 px-3">Allocation ID</th>
                      <th className="py-2 px-3">Resource</th>
                      <th className="py-2 px-3">Target Sector</th>
                      <th className="py-2 px-3 text-right">Quantity</th>
                      <th className="py-2 px-3">Status</th>
                      <th className="py-2 px-3 text-right">Est. Travel Time</th>
                      <th className="py-2 px-3">Allocated By</th>
                      <th className="py-2 px-3">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    {allocations.map((alloc) => (
                      <tr key={alloc.id} className="hover:bg-slate-800/40">
                        <td className="py-2.5 px-3 font-mono text-indigo-300 font-semibold">{alloc.allocation_id}</td>
                        <td className="py-2.5 px-3 font-medium text-white">{alloc.resource_name}</td>
                        <td className="py-2.5 px-3 text-slate-300">{alloc.demand_sector_name}</td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold">{alloc.assigned_quantity}</td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${alloc.status === 'PROPOSED'
                              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                              : alloc.status === 'APPROVED'
                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                : 'bg-slate-800 text-slate-400'
                              }`}
                          >
                            {alloc.status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono">
                          {alloc.estimated_travel_time_sec ? `${Math.round(alloc.estimated_travel_time_sec / 60)} mins` : '--'}
                        </td>
                        <td className="py-2.5 px-3 text-slate-400">{alloc.allocated_by}</td>
                        <td className="py-2.5 px-3">
                          {alloc.status === 'APPROVED' && (
                            <button
                              onClick={async () => {
                                try {
                                  await apiService.releaseAllocation(alloc.id, 'Manual stand-down');
                                  setRefreshTrigger((prev) => prev + 1);
                                } catch (err: any) {
                                  alert(`Release failed: ${err.message}`);
                                }
                              }}
                              className="text-red-400 hover:text-red-300 text-[11px] underline"
                            >
                              Release
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 3: Google OR-Tools Mathematical Optimization */}
      {/* ==================================================================== */}
      {activeTab === 'optimization' && (
        <div className="space-y-5">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Zap className="w-5 h-5 text-indigo-400" />
              Google OR-Tools Constrained MIP Optimization
            </h2>
            <p className="text-slate-400 text-xs mt-1">
              Computes mathematically optimal emergency dispatches minimizing response time across the Pune road network
            </p>

            {/* Parameter configuration */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4 pt-4 border-t border-slate-800">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Solver Objective</label>
                <select
                  value={optObjective}
                  onChange={(e: any) => setOptObjective(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="MINIMIZE_RESPONSE_TIME">Min Response Time (Latency Minimization)</option>
                  <option value="MAXIMIZE_COVERAGE">Max Demand Coverage (High Shortage Penalty)</option>
                  <option value="BALANCED">Balanced Multi-Objective</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Max Travel Window ({maxTravelMinutes} minutes)
                </label>
                <input
                  type="range"
                  min="15"
                  max="120"
                  step="5"
                  value={maxTravelMinutes}
                  onChange={(e) => setMaxTravelMinutes(Number(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>

              <div className="flex flex-col justify-end">
                <button
                  onClick={handleRunOptimization}
                  disabled={optLoading}
                  className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
                >
                  <Zap className={`w-4 h-4 ${optLoading ? 'animate-spin' : ''}`} />
                  {optLoading ? 'Solving Mathematical MIP...' : 'Execute OR-Tools Optimization'}
                </button>
              </div>
            </div>

            {/* Verified Shelter Capacity Enforcement Notice */}
            <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg flex items-start gap-2.5 text-xs text-amber-300">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Verified Shelter Rule Enforced:</span> Zero unverified shelter facilities are allocated. In the baseline system, all 64 municipal shelters are unverified candidates awaiting structural clearance.
              </div>
            </div>
          </div>

          {/* Results Display */}
          {optimizationResult && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="text-xs text-slate-400">SOLVER STATUS</div>
                  <div className="text-xl font-bold text-emerald-400 mt-1 flex items-center gap-1.5">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    {optimizationResult.solver_status}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    {optimizationResult.solver_name}
                  </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="text-xs text-slate-400">DEMAND COVERAGE</div>
                  <div className="text-2xl font-bold text-white mt-1">
                    {optimizationResult.demand_coverage_pct}%
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    {optimizationResult.total_assigned_resources} Assigned / {optimizationResult.total_unmet_demand_count} Unmet
                  </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="text-xs text-slate-400">SOLVER LATENCY</div>
                  <div className="text-2xl font-bold text-white mt-1 font-mono">
                    {optimizationResult.execution_duration_ms} ms
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    MIP Branch-and-Cut Complete
                  </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <div className="text-xs text-slate-400">TOTAL TRAVEL TIME</div>
                  <div className="text-2xl font-bold text-white mt-1 font-mono">
                    {optimizationResult.total_response_time_minutes} min
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Across {optimizationResult.assignments.length} dispatches
                  </div>
                </div>
              </div>

              {/* Assignments list */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow">
                <h3 className="text-sm font-bold text-white mb-3">
                  Optimal Dispatches Assigned ({optimizationResult.assignments.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {optimizationResult.assignments.map((asn) => (
                    <div key={asn.assignment_id} className="bg-slate-950 border border-slate-800 p-3.5 rounded-lg flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="font-mono text-indigo-400 font-bold">{asn.assignment_id}</span>
                          <div className="flex items-center gap-1.5">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold ${asn.verification_status === 'VERIFIED'
                                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                : 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                                }`}
                            >
                              {asn.verification_status || (asn.is_simulated ? 'SIMULATED' : 'UNVERIFIED')}
                            </span>
                            <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                              Qty: {asn.assigned_quantity}
                            </span>
                          </div>
                        </div>
                        <div className="font-semibold text-white text-sm">{asn.resource_name}</div>
                        <div className="text-xs text-slate-400 flex items-center gap-1.5 mt-1">
                          <span>{asn.from_location}</span>
                          <ArrowRight className="w-3 h-3 text-slate-500" />
                          <span className="text-slate-200 font-medium">{asn.target_sector_name}</span>
                        </div>
                      </div>

                      <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-indigo-400" /> {asn.estimated_travel_time_minutes} min
                        </span>
                        <span>{(asn.estimated_distance_m / 1000).toFixed(1)} km</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Unmet Demands */}
              {optimizationResult.unmet_demands.length > 0 && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow">
                  <h3 className="text-sm font-bold text-red-400 mb-3 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" /> Unmet Demands & Bottleneck Analysis
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="bg-slate-950 text-slate-400 border-b border-slate-800 font-semibold">
                          <th className="py-2 px-3">Sector</th>
                          <th className="py-2 px-3">Resource Type</th>
                          <th className="py-2 px-3 text-right">Demanded</th>
                          <th className="py-2 px-3 text-right">Allocated</th>
                          <th className="py-2 px-3 text-right text-red-400">Shortage</th>
                          <th className="py-2 px-3">Bottleneck Cause</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800 text-slate-300">
                        {optimizationResult.unmet_demands.map((u, idx) => (
                          <tr key={idx}>
                            <td className="py-2 px-3 font-medium text-white">{u.sector_name}</td>
                            <td className="py-2 px-3 font-mono">{u.resource_type}</td>
                            <td className="py-2 px-3 text-right font-mono">{u.demanded_quantity}</td>
                            <td className="py-2 px-3 text-right font-mono">{u.allocated_quantity}</td>
                            <td className="py-2 px-3 text-right font-mono font-bold text-red-400">{u.shortage_quantity}</td>
                            <td className="py-2 px-3 text-slate-400">{u.reason}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 4: What-If Disaster Simulation */}
      {/* ==================================================================== */}
      {activeTab === 'simulation' && (
        <div className="space-y-5">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Sliders className="w-5 h-5 text-indigo-400" />
              What-If Disaster Drill Simulator (Strict In-Memory Isolation)
            </h2>
            <p className="text-slate-400 text-xs mt-1">
              Simulate extreme cloudburst rainfall, Khadakwasla Dam discharge surges, and fleet offline factors without mutating live operational records.
            </p>

            {/* Slider controls */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4 pt-4 border-t border-slate-800">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Rainfall Multiplier: <span className="font-mono text-indigo-400 font-bold">{simRainMultiplier}x</span>
                </label>
                <input
                  type="range"
                  min="1.0"
                  max="4.0"
                  step="0.25"
                  value={simRainMultiplier}
                  onChange={(e) => setSimRainMultiplier(Number(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Khadakwasla Dam: <span className="font-mono text-indigo-400 font-bold">{simDamDischarge.toLocaleString()} cfs</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="80000"
                  step="5000"
                  value={simDamDischarge}
                  onChange={(e) => setSimDamDischarge(Number(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Fleet Availability: <span className="font-mono text-indigo-400 font-bold">{Math.round(simFleetAvailability * 100)}%</span>
                </label>
                <input
                  type="range"
                  min="0.3"
                  max="1.0"
                  step="0.05"
                  value={simFleetAvailability}
                  onChange={(e) => setSimFleetAvailability(Number(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>

              <div className="flex flex-col justify-end">
                <button
                  onClick={handleRunSimulation}
                  disabled={simLoading}
                  className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
                >
                  <Sliders className={`w-4 h-4 ${simLoading ? 'animate-spin' : ''}`} />
                  {simLoading ? 'Simulating...' : 'Run Drill Simulation'}
                </button>
              </div>
            </div>

            {/* Benchmark thresholds guide */}
            <div className="mt-4 pt-3 border-t border-slate-800 text-xs text-slate-400">
              <span className="font-semibold text-slate-300">Dam Benchmarks:</span> 15k cfs (unverified Bhide Causeway overflow caution), 35.5k cfs (observed July 2024 peak reference), 45k & 70k cfs (hypothetical drill scenarios; primary municipal hydraulic validation pending).
            </div>
          </div>

          {/* Simulation Results */}
          {simulationResult && (
            <div className="space-y-4">
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs text-emerald-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>{simulationResult.isolation_guarantee}</span>
              </div>

              {/* Benchmarks triggered */}
              {simulationResult.dam_submergence_benchmarks_triggered.length > 0 && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-xs text-red-300 space-y-1">
                  <div className="font-bold flex items-center gap-1.5 text-red-400">
                    <AlertTriangle className="w-4 h-4" /> Flood Inundation Benchmarks Triggered:
                  </div>
                  {simulationResult.dam_submergence_benchmarks_triggered.map((b, i) => (
                    <div key={i} className="pl-5">• {b}</div>
                  ))}
                </div>
              )}

              {/* Delta metrics grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {simulationResult.delta_metrics.map((m, i) => (
                  <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                    <div className="text-xs text-slate-400 font-medium">{m.metric_name}</div>
                    <div className="text-xl font-bold text-white mt-1">
                      {m.simulated_value.toFixed(1)}{' '}
                      <span className={`text-xs ${m.pct_change > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                        ({m.pct_change > 0 ? '+' : ''}{m.pct_change.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1">{m.interpretation}</div>
                  </div>
                ))}
              </div>

              {/* Tactical Recommendations */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow">
                <h3 className="text-sm font-bold text-white mb-2">Tactical Recommendations for Simulated Scenario</h3>
                <ul className="text-xs text-slate-300 space-y-1.5 pl-4 list-disc">
                  {simulationResult.tactical_recommendations.map((rec, i) => (
                    <li key={i}>{rec}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 5: Nugen Decision Intelligence & SOP Advisory */}
      {/* ==================================================================== */}
      {activeTab === 'nugen' && (
        <div className="space-y-5">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-indigo-400" />
                  Nugen Decision Intelligence & NDMA SOP Advisory
                </h2>
                <p className="text-slate-400 text-xs mt-1">
                  Provider:{' '}
                  <span className="font-semibold text-emerald-400">
                    {nugenStatus?.active_provider || 'RULE_BASED_DECISION_FALLBACK'}
                  </span>
                  {' '}— Deterministic SOP rule-based advisory aligned with NDMA guidelines
                </p>
              </div>

              <button
                onClick={handleGenerateAdvisory}
                disabled={advisoryLoading}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold flex items-center gap-2 transition-colors disabled:opacity-50"
              >
                <Sparkles className={`w-4 h-4 ${advisoryLoading ? 'animate-spin' : ''}`} />
                {advisoryLoading ? 'Generating Plan...' : 'Generate Operational Advisory'}
              </button>
            </div>

            {nugenStatus?.missing_configuration_notes && (
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-400">
                <span className="font-semibold text-slate-300">Integration Note:</span> {nugenStatus.missing_configuration_notes}
              </div>
            )}
          </div>

          {/* Advisory display */}
          {advisory && (
            <div className="space-y-5">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow">
                <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-2 mb-3">
                  <span className="font-mono text-indigo-400 font-bold">{advisory.advisory_id}</span>
                  <span>{new Date(advisory.generated_at).toLocaleString()}</span>
                </div>

                <div className="text-sm text-slate-200 leading-relaxed font-medium">
                  {advisory.executive_summary}
                </div>

                {/* Critical observations */}
                <div className="mt-4 pt-4 border-t border-slate-800">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Critical Field Observations:</h4>
                  <ul className="text-xs text-slate-300 space-y-1 pl-4 list-disc">
                    {advisory.critical_observations.map((obs, i) => (
                      <li key={i}>{obs}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Tactical Action Plan cards */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow">
                <h3 className="text-sm font-bold text-white mb-3">
                  Tactical Action Plan ({advisory.tactical_action_plan.length} Orders)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {advisory.tactical_action_plan.map((act, i) => (
                    <div key={i} className="bg-slate-950 border border-slate-800 p-4 rounded-lg flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between text-xs mb-1.5">
                          <span
                            className={`px-2 py-0.5 rounded font-bold ${act.priority_level === 'CRITICAL'
                              ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                              : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                              }`}
                          >
                            {act.priority_level}
                          </span>
                          <span className="font-mono text-[11px] text-slate-400">{act.urgency}</span>
                        </div>
                        <div className="text-white font-semibold text-xs">{act.target_sector}</div>
                        <div className="text-slate-300 text-xs mt-1">{act.description}</div>
                      </div>

                      <div className="mt-3 pt-2 border-t border-slate-800/80 text-[11px] text-indigo-300 font-mono">
                        {act.regulatory_reference}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

