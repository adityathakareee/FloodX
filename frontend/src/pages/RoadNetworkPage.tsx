import React, { useState, useEffect, useMemo } from 'react';
import {
  Navigation,
  Activity,
  Layers,
  MapPin,
  RefreshCw,
  Sliders,
  Shield,
  AlertTriangle,
  Info,
  Compass,
  ArrowRight,
  GitBranch,
  Maximize2,
  Clock,
  Gauge,
  Key,
  CheckCircle2,
  AlertCircle,
  Home,
  Route as RouteIcon,
  LifeBuoy,
  Lock,
  Unlock,
  Send,
  Users,
  Check,
  Radio,
  ExternalLink
} from 'lucide-react';
import { apiService } from '../services/api';
import {
  NetworkStatusResponse,
  NetworkStatisticsResponse,
  RoadsPaginatedResponse,
  NodesPaginatedResponse,
  GraphEdgeItem,
  GraphNodeItem,
  EvacuationStatusResponse,
  EvacuationStatisticsResponse,
  InfrastructureSafetyItem,
  RoadClosureItem,
  ShelterItem,
  RoutePlanResponse,
  RouteAlternativeItem,
  ShelterRecommendationResponse,
  RoadExposureItem
} from '../types/api';

type TabMode = 'routes' | 'bridges' | 'closures' | 'shelters' | 'topology';

export const RoadNetworkPage: React.FC = () => {
  // Navigation & Mode
  const [activeTab, setActiveTab] = useState<TabMode>('routes');
  const [citizenMode, setCitizenMode] = useState<boolean>(false);

  // General Loading & Status
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Phase 3.1 Topology State
  const [status, setStatus] = useState<NetworkStatusResponse | null>(null);
  const [statistics, setStatistics] = useState<NetworkStatisticsResponse | null>(null);
  const [sampleRoads, setSampleRoads] = useState<GraphEdgeItem[]>([]);
  const [sampleNodes, setSampleNodes] = useState<GraphNodeItem[]>([]);
  const [selectedHighway, setSelectedHighway] = useState<string>('all');
  const [selectedEdge, setSelectedEdge] = useState<GraphEdgeItem | null>(null);
  const [rebuilding, setRebuilding] = useState<boolean>(false);
  const [rebuildToken, setRebuildToken] = useState<string>('');
  const [showRebuildModal, setShowRebuildModal] = useState<boolean>(false);
  const [rebuildSuccess, setRebuildSuccess] = useState<string | null>(null);

  // Phase 3.2 Evacuation Subsystem State
  const [evacStatus, setEvacStatus] = useState<EvacuationStatusResponse | null>(null);
  const [evacStats, setEvacStats] = useState<EvacuationStatisticsResponse | null>(null);
  const [infrastructure, setInfrastructure] = useState<InfrastructureSafetyItem[]>([]);
  const [closures, setClosures] = useState<RoadClosureItem[]>([]);
  const [shelters, setShelters] = useState<ShelterItem[]>([]);

  // Bridge Submergence Simulation
  const [simulatedDischarge, setSimulatedDischarge] = useState<number>(0);
  const [dischargeLoading, setDischargeLoading] = useState<boolean>(false);

  // Route Planning State
  const [originLat, setOriginLat] = useState<number>(18.5140);
  const [originLon, setOriginLon] = useState<number>(73.8450);
  const [destLat, setDestLat] = useState<number>(18.5300);
  const [destLon, setDestLon] = useState<number>(73.8450);
  const [costProfile, setCostProfile] = useState<'FASTEST' | 'SAFEST' | 'BALANCED'>('SAFEST');
  const [algorithm, setAlgorithm] = useState<'A_STAR' | 'DIJKSTRA'>('A_STAR');
  const [findAlternatives, setFindAlternatives] = useState<boolean>(true);
  const [routingInProgress, setRoutingInProgress] = useState<boolean>(false);
  const [routePlan, setRoutePlan] = useState<RoutePlanResponse | null>(null);
  const [activeRouteIndex, setActiveRouteIndex] = useState<number>(0); // 0 = primary, 1 = alt 1, etc.

  // Shelter Recommendations State
  const [recsLoading, setRecsLoading] = useState<boolean>(false);
  const [shelterRecs, setShelterRecs] = useState<ShelterRecommendationResponse | null>(null);
  const [recNeedMedical, setRecNeedMedical] = useState<boolean>(false);
  const [recNeedWheelchair, setRecNeedWheelchair] = useState<boolean>(false);

  // New Closure Modal State
  const [showClosureModal, setShowClosureModal] = useState<boolean>(false);
  const [newClosureEdgeId, setNewClosureEdgeId] = useState<string>('');
  const [newClosureRoadName, setNewClosureRoadName] = useState<string>('');
  const [newClosureReason, setNewClosureReason] = useState<string>('Heavy waterlogging > 0.5m');
  const [newClosureAuthority, setNewClosureAuthority] = useState<string>('Pune Traffic Police Unit 1');

  // Authority Authentication Token State
  const [authorityTokenInput, setAuthorityTokenInput] = useState<string>(() => apiService.getAuthorityToken() || '');
  const [isTokenSaved, setIsTokenSaved] = useState<boolean>(() => !!apiService.getAuthorityToken());

  // Layer Toggles
  const [showRoads, setShowRoads] = useState<boolean>(true);
  const [showNodes, setShowNodes] = useState<boolean>(false);
  const [showBridges, setShowBridges] = useState<boolean>(true);
  const [showWaterways, setShowWaterways] = useState<boolean>(true);
  const [showRouteOverlay, setShowRouteOverlay] = useState<boolean>(true);

  // Preset Origin-Destination Coordinates (Known Pune Hotspots & Safe Shelters)
  const PRESET_ROUTES = [
    {
      label: 'Pulachi Wadi / Alka Chowk → Sancheti Relief Centre',
      orig: { lat: 18.5140, lon: 73.8450, name: 'Pulachi Wadi / Lakdi Pul' },
      dest: { lat: 18.5300, lon: 73.8450, name: 'Sancheti High School Shelter' },
    },
    {
      label: 'Sinhagad Road (Ekta Nagari) → Kothrud Relief Hall',
      orig: { lat: 18.4850, lon: 73.8300, name: 'Ekta Nagari Sinhagad Rd' },
      dest: { lat: 18.5080, lon: 73.8150, name: 'Kothrud Ward Relief Hall' },
    },
    {
      label: 'Baba Bhide Causeway → Shivaji Nagar Elevated Shelter',
      orig: { lat: 18.5178, lon: 73.8485, name: 'Baba Bhide Causeway' },
      dest: { lat: 18.5350, lon: 73.8500, name: 'Shivaji Nagar Elevated Post' },
    },
  ];

  useEffect(() => {
    fetchInitialData();
  }, [selectedHighway]);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [statusRes, statsRes, roadsRes, nodesRes, evacStatusRes, evacStatsRes, infraRes, closuresRes, sheltersRes] =
        await Promise.all([
          apiService.getRoutingStatus(),
          apiService.getRoutingStatistics(),
          apiService.getRoutingRoads({
            limit: 300,
            highway: selectedHighway === 'all' ? undefined : selectedHighway,
          }),
          apiService.getRoutingNodes({ limit: 400 }),
          apiService.getEvacuationStatus().catch(() => null),
          apiService.getEvacuationStatistics().catch(() => null),
          apiService.getEvacuationInfrastructure().catch(() => []),
          apiService.getEvacuationClosures().catch(() => []),
          apiService.getShelters({ limit: 50 }).catch(() => ({ total: 0, items: [] })),
        ]);

      setStatus(statusRes);
      setStatistics(statsRes);
      setSampleRoads(roadsRes.items);
      setSampleNodes(nodesRes.items);
      if (evacStatusRes) setEvacStatus(evacStatusRes);
      if (evacStatsRes) setEvacStats(evacStatsRes);
      setInfrastructure(infraRes);
      setClosures(closuresRes);
      setShelters(sheltersRes.items);
    } catch (err: any) {
      console.error('Failed to load evacuation intelligence:', err);
      setError(err?.message || 'Failed to connect to evacuation API');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateDischarge = async (cfs: number) => {
    setSimulatedDischarge(cfs);
    try {
      setDischargeLoading(true);
      const updatedInfra = await apiService.getEvacuationInfrastructure(cfs > 0 ? cfs : undefined);
      setInfrastructure(updatedInfra);
    } catch (err: any) {
      console.error('Failed to simulate discharge:', err);
    } finally {
      setDischargeLoading(false);
    }
  };

  const handlePlanRoute = async () => {
    try {
      setRoutingInProgress(true);
      const plan = await apiService.planEvacuationRoute({
        origin_lat: originLat,
        origin_lon: originLon,
        destination_lat: destLat,
        destination_lon: destLon,
        cost_profile: costProfile,
        algorithm: algorithm,
        find_alternatives: findAlternatives,
      });
      setRoutePlan(plan);
      setActiveRouteIndex(0);
      setShowRouteOverlay(true);
    } catch (err: any) {
      alert(`Route calculation failed: ${err?.message || 'No route available'}`);
    } finally {
      setRoutingInProgress(false);
    }
  };

  const handleFindShelterRecommendations = async () => {
    try {
      setRecsLoading(true);
      const res = await apiService.getShelterRecommendations(
        originLat,
        originLon,
        costProfile,
        recNeedMedical ? true : undefined,
        recNeedWheelchair ? true : undefined,
        5
      );
      setShelterRecs(res);
    } catch (err: any) {
      alert(`Failed to get shelter recommendations: ${err?.message}`);
    } finally {
      setRecsLoading(false);
    }
  };

  const handleCreateClosure = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newClosureEdgeId || !newClosureRoadName) return;

    if (authorityTokenInput) {
      apiService.setAuthorityToken(authorityTokenInput);
      setIsTokenSaved(true);
    }

    try {
      await apiService.createRoadClosure({
        edge_id: newClosureEdgeId,
        road_name: newClosureRoadName,
        reason: newClosureReason,
        reporting_authority: newClosureAuthority,
      });
      setShowClosureModal(false);
      setNewClosureEdgeId('');
      setNewClosureRoadName('');
      const updatedClosures = await apiService.getEvacuationClosures();
      setClosures(updatedClosures);
      alert('Road closure registered. Graph pathfinding will dynamically avoid this segment.');
    } catch (err: any) {
      alert(`Failed to create closure: ${err?.message || 'Unauthorized: Authority token required'}`);
    }
  };

  const handleClearClosure = async (closureId: number) => {
    let token = apiService.getAuthorityToken();
    if (!token) {
      const prompted = prompt('Please enter the Authority Secret Token to clear this road closure:');
      if (!prompted) return;
      apiService.setAuthorityToken(prompted);
      setAuthorityTokenInput(prompted);
      setIsTokenSaved(true);
    }
    try {
      await apiService.deleteRoadClosure(closureId, 'Authority Officer');
      const updatedClosures = await apiService.getEvacuationClosures();
      setClosures(updatedClosures);
    } catch (err: any) {
      alert(`Failed to clear closure: ${err?.message || 'Unauthorized: Invalid authority token'}`);
    }
  };

  const handleRebuild = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rebuildToken) return;

    try {
      setRebuilding(true);
      setRebuildSuccess(null);
      const res = await apiService.rebuildRoutingGraph(rebuildToken);
      setRebuildSuccess(res.message);
      setShowRebuildModal(false);
      setRebuildToken('');
      fetchInitialData();
    } catch (err: any) {
      alert(`Rebuild failed: ${err?.message || 'Unauthorized token'}`);
    } finally {
      setRebuilding(false);
    }
  };

  // Geographic SVG Projection (Pune Basin Bounds)
  const mapBounds = {
    minLon: 73.815,
    maxLon: 73.895,
    minLat: 18.468,
    maxLat: 18.555,
  };

  const projectToSvg = (lon: number, lat: number, width = 800, height = 500) => {
    const x = ((lon - mapBounds.minLon) / (mapBounds.maxLon - mapBounds.minLon)) * width;
    const y = height - ((lat - mapBounds.minLat) / (mapBounds.maxLat - mapBounds.minLat)) * height;
    return { x, y };
  };

  // Mula-Mutha river centerline coordinates
  const MUTHA_RIVER_COORDS = [
    [73.825, 18.475],
    [73.832, 18.490],
    [73.840, 18.505],
    [73.847, 18.516],
    [73.855, 18.523],
    [73.864, 18.530],
    [73.875, 18.533],
    [73.890, 18.538],
  ];

  // Active route being inspected
  const activeRoute = useMemo(() => {
    if (!routePlan || !routePlan.primary_route) return null;
    if (activeRouteIndex === 0) return routePlan.primary_route;
    return routePlan.alternatives[activeRouteIndex - 1] || routePlan.primary_route;
  }, [routePlan, activeRouteIndex]);

  const getHighwayColor = (hw: string) => {
    switch (hw) {
      case 'trunk':
      case 'trunk_link':
        return '#F59E0B'; // Amber
      case 'primary':
      case 'primary_link':
        return '#00F0FF'; // Cyan
      case 'secondary':
      case 'secondary_link':
        return '#10B981'; // Emerald
      case 'tertiary':
      case 'tertiary_link':
        return '#6366F1'; // Indigo
      default:
        return '#64748B'; // Slate
    }
  };

  if (loading && !status) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
        <span className="font-mono text-sm text-slate-400">Loading Evacuation Intelligence Subsystem...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Official Emergency Disclaimer Banner */}
      <div className="p-3.5 bg-rose-950/40 border-2 border-rose-500/60 rounded-2xl flex items-start justify-between gap-3 text-rose-200">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5 animate-pulse" />
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-bold text-xs uppercase tracking-wider text-rose-300">
                Official Emergency Decision-Support Notice
              </span>
              <span className="text-[10px] bg-rose-900/60 text-rose-200 px-2 py-0.5 rounded font-mono">
                PUNE MUNICIPAL / DDMA BENCHMARK
              </span>
            </div>
            <p className="text-xs text-rose-200/90 leading-relaxed font-sans">
              Evacuation routes and reachability metrics are experimental decision-support models based on Copernicus GLO-90 DSM (~90m) elevation,
              OSM road geometry, and historical CWPRS cloudburst benchmarks. In an active flood emergency, always follow official
              police barricades, NDRF rescue directives, and PMC Disaster Management instructions.
            </p>
          </div>
        </div>

        {/* Citizen Mode Toggle */}
        <button
          onClick={() => setCitizenMode(!citizenMode)}
          className={`px-3 py-1.5 rounded-xl border text-xs font-mono font-bold flex items-center gap-2 flex-shrink-0 transition-all ${citizenMode
              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50'
              : 'bg-slate-800/80 text-slate-300 border-slate-700 hover:border-slate-500'
            }`}
        >
          <Radio className={`w-3.5 h-3.5 ${citizenMode ? 'text-emerald-400 animate-pulse' : 'text-slate-400'}`} />
          <span>{citizenMode ? 'Citizen View' : 'Authority View'}</span>
        </button>
      </div>

      {/* Header and Operational Readiness Status */}
      <div className="bg-[#0D152A] border border-[#1E325F]/70 rounded-2xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Shield className="w-6 h-6 text-cyan-400" />
              <h1 className="text-xl font-bold text-white tracking-wide">
                FLOOD-AWARE EVACUATION & SAFE ROUTING INTELLIGENCE
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-950/80 text-cyan-300 border border-cyan-800">
                PHASE 3.2 ACTIVE
              </span>
            </div>
            <p className="text-xs text-slate-400 max-w-3xl">
              MultiDiGraph pathfinding on 1,488 directed road segments combined with Copernicus GLO-90 DSM (~90m) terrain hazard exposure,
              active municipal road closures, Khadakwasla discharge what-if simulation, and verified relief shelters.
            </p>
          </div>

          {/* Quick Metrics Badge */}
          <div className="flex items-center gap-3">
            <div className="text-right">
              <span className="text-[10px] font-mono text-slate-400 uppercase block">Active Closures</span>
              <span className="text-sm font-bold font-mono text-amber-400">{closures.length} Segments Blocked</span>
            </div>
            <div className="h-8 w-px bg-slate-700" />
            <div className="text-right">
              <span className="text-[10px] font-mono text-slate-400 uppercase block">Verified Shelters</span>
              <span className="text-sm font-bold font-mono text-emerald-400">{evacStatus?.verified_shelters_count ?? 0} Verified</span>
            </div>
          </div>
        </div>

        {/* Tab Navigation Strip */}
        <div className="flex flex-wrap items-center gap-2 mt-6 pt-4 border-t border-[#1E325F]/60">
          <button
            onClick={() => setActiveTab('routes')}
            className={`px-3.5 py-2 rounded-xl text-xs font-mono font-bold flex items-center gap-2 transition-all ${activeTab === 'routes'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-sm'
                : 'bg-[#0A1022] text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
          >
            <RouteIcon className="w-4 h-4 text-cyan-400" />
            <span>Evacuation Route Planner</span>
          </button>

          <button
            onClick={() => setActiveTab('bridges')}
            className={`px-3.5 py-2 rounded-xl text-xs font-mono font-bold flex items-center gap-2 transition-all ${activeTab === 'bridges'
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50 shadow-sm'
                : 'bg-[#0A1022] text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
          >
            <Compass className="w-4 h-4 text-amber-400" />
            <span>Critical Bridges & Dam Discharge</span>
          </button>

          <button
            onClick={() => setActiveTab('closures')}
            className={`px-3.5 py-2 rounded-xl text-xs font-mono font-bold flex items-center gap-2 transition-all ${activeTab === 'closures'
                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/50 shadow-sm'
                : 'bg-[#0A1022] text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
          >
            <Lock className="w-4 h-4 text-rose-400" />
            <span>Road Closures ({closures.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('shelters')}
            className={`px-3.5 py-2 rounded-xl text-xs font-mono font-bold flex items-center gap-2 transition-all ${activeTab === 'shelters'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-sm'
                : 'bg-[#0A1022] text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
          >
            <Home className="w-4 h-4 text-emerald-400" />
            <span>Shelters & Relief Centers</span>
          </button>

          <button
            onClick={() => setActiveTab('topology')}
            className={`px-3.5 py-2 rounded-xl text-xs font-mono font-bold flex items-center gap-2 transition-all ${activeTab === 'topology'
                ? 'bg-purple-500/20 text-purple-300 border border-purple-500/50 shadow-sm'
                : 'bg-[#0A1022] text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
          >
            <GitBranch className="w-4 h-4 text-purple-400" />
            <span>Network Topology (Phase 3.1)</span>
          </button>
        </div>
      </div>

      {/* ==================================================================== */}
      {/* TAB 1: DYNAMIC EVACUATION ROUTE PLANNER */}
      {/* ==================================================================== */}
      {activeTab === 'routes' && (
        <div className="space-y-6">
          {/* Preset Quick-Buttons */}
          <div className="bg-[#0D152A] border border-[#1E325F]/70 rounded-2xl p-4">
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-2 font-bold">
              Quick Evacuation Scenarios (Pune Flood Corridors):
            </span>
            <div className="flex flex-wrap gap-2">
              {PRESET_ROUTES.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setOriginLat(p.orig.lat);
                    setOriginLon(p.orig.lon);
                    setDestLat(p.dest.lat);
                    setDestLon(p.dest.lon);
                  }}
                  className="px-3 py-1.5 rounded-lg bg-[#0A1022] border border-[#1C2D54] hover:border-cyan-500 text-xs text-slate-300 font-mono flex items-center gap-2 transition-all"
                >
                  <MapPin className="w-3.5 h-3.5 text-cyan-400" />
                  <span>{p.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Interactive Routing Parameters & GIS Viewport Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: Route Controls (4 Cols) */}
            <div className="lg:col-span-4 bg-[#0D152A] border border-[#1E325F]/70 rounded-2xl p-5 space-y-4">
              <div className="flex items-center gap-2 border-b border-[#1E325F]/60 pb-3">
                <Sliders className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Routing Parameters
                </h3>
              </div>

              {/* Origin Coordinates */}
              <div className="space-y-2">
                <label className="text-[11px] font-mono text-slate-400 font-bold flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" /> Origin Point (Lat, Lon):
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="number"
                    step="0.0001"
                    value={originLat}
                    onChange={(e) => setOriginLat(parseFloat(e.target.value))}
                    className="bg-[#0A1022] border border-[#1C2D54] rounded-lg px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:border-cyan-500"
                    placeholder="Latitude"
                  />
                  <input
                    type="number"
                    step="0.0001"
                    value={originLon}
                    onChange={(e) => setOriginLon(parseFloat(e.target.value))}
                    className="bg-[#0A1022] border border-[#1C2D54] rounded-lg px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:border-cyan-500"
                    placeholder="Longitude"
                  />
                </div>
              </div>

              {/* Destination Coordinates */}
              <div className="space-y-2">
                <label className="text-[11px] font-mono text-slate-400 font-bold flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-rose-400" /> Destination Point (Lat, Lon):
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="number"
                    step="0.0001"
                    value={destLat}
                    onChange={(e) => setDestLat(parseFloat(e.target.value))}
                    className="bg-[#0A1022] border border-[#1C2D54] rounded-lg px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:border-cyan-500"
                    placeholder="Latitude"
                  />
                  <input
                    type="number"
                    step="0.0001"
                    value={destLon}
                    onChange={(e) => setDestLon(parseFloat(e.target.value))}
                    className="bg-[#0A1022] border border-[#1C2D54] rounded-lg px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:border-cyan-500"
                    placeholder="Longitude"
                  />
                </div>
              </div>

              {/* Cost Profile */}
              <div className="space-y-1.5">
                <label className="text-[11px] font-mono text-slate-400 font-bold block">
                  Safety vs Speed Profile:
                </label>
                <div className="grid grid-cols-3 gap-1.5">
                  {(['SAFEST', 'BALANCED', 'FASTEST'] as const).map((prof) => (
                    <button
                      key={prof}
                      onClick={() => setCostProfile(prof)}
                      className={`px-2 py-1.5 rounded-lg border text-xs font-mono font-bold transition-all ${costProfile === prof
                          ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50'
                          : 'bg-[#0A1022] text-slate-400 border-[#1C2D54]'
                        }`}
                    >
                      {prof}
                    </button>
                  ))}
                </div>
                <span className="text-[10px] text-slate-500 font-mono block">
                  {costProfile === 'SAFEST' && 'Routes via high-elevation terrain, avoiding river corridors.'}
                  {costProfile === 'BALANCED' && 'Balances travel time efficiency with flood hazard avoidance.'}
                  {costProfile === 'FASTEST' && 'Minimizes travel time; accepts higher flood exposure risk.'}
                </span>
              </div>

              {/* Algorithm & Alternatives */}
              <div className="space-y-2 pt-2 border-t border-[#1E325F]/40">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-400">Pathfinding Algorithm:</span>
                  <select
                    value={algorithm}
                    onChange={(e) => setAlgorithm(e.target.value as any)}
                    className="bg-[#0A1022] border border-[#1C2D54] rounded px-2 py-1 text-slate-200 text-xs font-mono"
                  >
                    <option value="A_STAR">A* (Admissible Heuristic)</option>
                    <option value="DIJKSTRA">Dijkstra (Exact Shortest)</option>
                  </select>
                </div>

                <label className="flex items-center gap-2 text-xs font-mono text-slate-300 cursor-pointer pt-1">
                  <input
                    type="checkbox"
                    checked={findAlternatives}
                    onChange={(e) => setFindAlternatives(e.target.checked)}
                    className="rounded bg-[#0A1022] border-[#1C2D54] text-cyan-500"
                  />
                  <span>Discover Alternative Evacuation Paths</span>
                </label>
              </div>

              {/* Action Button */}
              <button
                onClick={handlePlanRoute}
                disabled={routingInProgress}
                className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-mono font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 transition-all disabled:opacity-50"
              >
                {routingInProgress ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Pathfinding MultiDiGraph...</span>
                  </>
                ) : (
                  <>
                    <Navigation className="w-4 h-4" />
                    <span>Calculate Evacuation Route</span>
                  </>
                )}
              </button>

              {/* Route Summary Results */}
              {routePlan && (
                <div className="mt-4 pt-3 border-t border-[#1E325F]/60 space-y-2.5 font-mono text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 font-bold">Status:</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${routePlan.status === 'SUCCESS' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-rose-950 text-rose-300 border border-rose-800'
                      }`}>
                      {routePlan.status}
                    </span>
                  </div>

                  {routePlan.status === 'SUCCESS' && routePlan.primary_route && (
                    <>
                      {/* Route Switcher Tabs if Alternatives exist */}
                      {routePlan.alternatives.length > 0 && (
                        <div className="flex items-center gap-1.5 pt-1">
                          <button
                            onClick={() => setActiveRouteIndex(0)}
                            className={`px-2 py-1 rounded text-[10px] font-bold border transition-all ${activeRouteIndex === 0
                                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50'
                                : 'bg-[#0A1022] text-slate-400 border-slate-800'
                              }`}
                          >
                            Primary
                          </button>
                          {routePlan.alternatives.map((alt, aIdx) => (
                            <button
                              key={alt.route_id}
                              onClick={() => setActiveRouteIndex(aIdx + 1)}
                              className={`px-2 py-1 rounded text-[10px] font-bold border transition-all ${activeRouteIndex === aIdx + 1
                                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/50'
                                  : 'bg-[#0A1022] text-slate-400 border-slate-800'
                                }`}
                            >
                              Alt {aIdx + 1}
                            </button>
                          ))}
                        </div>
                      )}

                      {activeRoute && (
                        <div className="p-3 bg-[#0A1022] border border-[#1C2D54] rounded-xl space-y-2">
                          <div className="flex justify-between text-slate-400">
                            <span>Travel Distance:</span>
                            <strong className="text-white">{(activeRoute.total_distance_m / 1000).toFixed(2)} km</strong>
                          </div>
                          <div className="flex justify-between text-slate-400">
                            <span>Est. Travel Time:</span>
                            <strong className="text-emerald-400">{(activeRoute.total_travel_time_sec / 60).toFixed(1)} mins</strong>
                          </div>
                          {activeRouteIndex > 0 && activeRoute.overlap_percentage !== undefined && (
                            <div className="flex justify-between text-slate-400">
                              <span>Primary Overlap:</span>
                              <strong className="text-cyan-300">
                                {activeRoute.overlap_percentage.toFixed(1)}% ({activeRoute.shared_edges_count ?? 0} shared edges)
                              </strong>
                            </div>
                          )}
                          <div className="flex justify-between text-slate-400">
                            <span>Hazardous Segments:</span>
                            <strong className={activeRoute.hazardous_segments_count > 0 ? 'text-rose-400' : 'text-emerald-400'}>
                              {activeRoute.hazardous_segments_count} critical / high
                            </strong>
                          </div>
                          <div className="flex justify-between text-slate-400">
                            <span>Caution Segments:</span>
                            <strong className="text-amber-400">{activeRoute.caution_segments_count} segments</strong>
                          </div>
                          {activeRoute.directionality_uncertainty_note && (
                            <div className="text-[10px] text-amber-300/90 bg-amber-950/30 p-1.5 rounded border border-amber-800/40">
                              ℹ {activeRoute.directionality_uncertainty_note}
                            </div>
                          )}
                          {activeRoute.speed_assumptions_note && (
                            <div className="text-[10px] text-slate-400 bg-slate-900/60 p-1.5 rounded border border-slate-800">
                              ⚡ {activeRoute.speed_assumptions_note}
                            </div>
                          )}
                          <p className="text-[11px] text-slate-300 border-t border-[#1C2D54] pt-2 italic">
                            "{activeRoute.explanation}"
                          </p>
                        </div>
                      )}
                    </>
                  )}

                  {routePlan.warnings.length > 0 && (
                    <div className="p-2 bg-amber-950/30 border border-amber-600/40 rounded text-[10px] text-amber-300 space-y-1">
                      {routePlan.warnings.map((w, wi) => (
                        <div key={wi}>⚠ {w}</div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Right Column: Interactive Evacuation GIS Map (8 Cols) */}
            <div className="lg:col-span-8 bg-[#0D152A] border border-[#1E325F]/70 rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-[#1E325F]/60 pb-3">
                <div className="flex items-center gap-2">
                  <Compass className="w-5 h-5 text-cyan-400" />
                  <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                    Evacuation Corridor GIS Viewport
                  </h2>
                </div>
                <div className="flex items-center gap-2 text-xs font-mono">
                  <span className="text-slate-400 text-[11px]">Map Layers:</span>
                  <button
                    onClick={() => setShowRouteOverlay(!showRouteOverlay)}
                    className={`px-2 py-0.5 rounded border text-[10px] ${showRouteOverlay ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40' : 'text-slate-500 border-slate-800'
                      }`}
                  >
                    Route Lines
                  </button>
                  <button
                    onClick={() => setShowBridges(!showBridges)}
                    className={`px-2 py-0.5 rounded border text-[10px] ${showBridges ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' : 'text-slate-500 border-slate-800'
                      }`}
                  >
                    Bridges
                  </button>
                </div>
              </div>

              {/* Map SVG Container */}
              <div className="relative w-full h-[520px] bg-[#060B18] border border-[#1E325F] rounded-xl overflow-hidden shadow-inner flex items-center justify-center">
                <svg viewBox="0 0 800 500" className="w-full h-full">
                  {/* 1. Mula-Mutha River */}
                  {showWaterways && (
                    <path
                      d={MUTHA_RIVER_COORDS.map(([lon, lat], i) => {
                        const p = projectToSvg(lon, lat);
                        return `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`;
                      }).join(' ')}
                      fill="none"
                      stroke="#1D4ED8"
                      strokeWidth="10"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      opacity="0.5"
                    />
                  )}

                  {/* 2. Base Road Network */}
                  {showRoads &&
                    sampleRoads.map((edge) => {
                      const coords = edge.geometry_geojson?.coordinates;
                      if (!coords || coords.length < 2) return null;
                      const pathData = coords
                        .map(([lon, lat], i) => {
                          const p = projectToSvg(lon, lat);
                          return `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`;
                        })
                        .join(' ');

                      return (
                        <path
                          key={edge.edge_id}
                          d={pathData}
                          fill="none"
                          stroke={getHighwayColor(edge.highway)}
                          strokeWidth={edge.highway.includes('trunk') || edge.highway.includes('primary') ? 1.8 : 1.0}
                          strokeOpacity={0.4}
                        />
                      );
                    })}

                  {/* 3. Alternative Routes (Dashed Orange) */}
                  {showRouteOverlay &&
                    routePlan?.alternatives?.map((alt, aIdx) => {
                      const coords = alt.geometry_geojson?.coordinates;
                      if (!coords || coords.length < 2) return null;
                      const pathData = coords
                        .map(([lon, lat], i) => {
                          const p = projectToSvg(lon, lat);
                          return `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`;
                        })
                        .join(' ');

                      const isActive = activeRouteIndex === aIdx + 1;
                      return (
                        <path
                          key={alt.route_id}
                          d={pathData}
                          fill="none"
                          stroke="#F59E0B"
                          strokeWidth={isActive ? 4.5 : 2.5}
                          strokeDasharray={isActive ? 'none' : '4 4'}
                          strokeOpacity={isActive ? 1.0 : 0.6}
                          className="cursor-pointer"
                          onClick={() => setActiveRouteIndex(aIdx + 1)}
                        />
                      );
                    })}

                  {/* 4. Primary Route (Glowing Cyan / Green) */}
                  {showRouteOverlay && routePlan?.primary_route && (
                    (() => {
                      const coords = routePlan.primary_route.geometry_geojson?.coordinates;
                      if (!coords || coords.length < 2) return null;
                      const pathData = coords
                        .map(([lon, lat], i) => {
                          const p = projectToSvg(lon, lat);
                          return `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`;
                        })
                        .join(' ');
                      const isActive = activeRouteIndex === 0;

                      return (
                        <>
                          {/* Glow filter */}
                          <path
                            d={pathData}
                            fill="none"
                            stroke="#00F0FF"
                            strokeWidth={isActive ? 8 : 4}
                            strokeOpacity={0.3}
                          />
                          <path
                            d={pathData}
                            d-label="primary"
                            fill="none"
                            stroke="#10B981"
                            strokeWidth={isActive ? 4.5 : 3.0}
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeOpacity={isActive ? 1.0 : 0.7}
                            className="cursor-pointer"
                            onClick={() => setActiveRouteIndex(0)}
                          />
                        </>
                      );
                    })()
                  )}

                  {/* 5. Origin & Destination Markers */}
                  {(() => {
                    const pOrig = projectToSvg(originLon, originLat);
                    const pDest = projectToSvg(destLon, destLat);
                    return (
                      <>
                        <g transform={`translate(${pOrig.x}, ${pOrig.y})`} className="cursor-pointer">
                          <circle r="7" fill="#10B981" stroke="#FFFFFF" strokeWidth="2" />
                          <circle r="12" fill="#10B981" opacity="0.3" className="animate-ping" />
                          <text x="9" y="4" fill="#6EE7B7" fontSize="9" fontFamily="monospace" fontWeight="bold">
                            ORIGIN
                          </text>
                        </g>

                        <g transform={`translate(${pDest.x}, ${pDest.y})`} className="cursor-pointer">
                          <circle r="7" fill="#EF4444" stroke="#FFFFFF" strokeWidth="2" />
                          <circle r="12" fill="#EF4444" opacity="0.3" className="animate-ping" />
                          <text x="9" y="4" fill="#FCA5A5" fontSize="9" fontFamily="monospace" fontWeight="bold">
                            DEST
                          </text>
                        </g>
                      </>
                    );
                  })()}

                  {/* 6. Bridges and Submergence Status */}
                  {showBridges &&
                    infrastructure.map((b) => {
                      const p = projectToSvg(b.longitude, b.latitude);
                      const isSub = b.is_submerged_simulated || b.is_closed;
                      return (
                        <g key={b.id} className="cursor-pointer group">
                          <polygon
                            points={`${p.x},${p.y - 7} ${p.x + 7},${p.y} ${p.x},${p.y + 7} ${p.x - 7},${p.y}`}
                            fill={isSub ? '#EF4444' : '#F59E0B'}
                            stroke="#0D152A"
                            strokeWidth="1.5"
                          />
                          <text
                            x={p.x + 9}
                            y={p.y + 3}
                            fill={isSub ? '#FCA5A5' : '#FCD34D'}
                            fontSize="8"
                            fontFamily="monospace"
                            fontWeight="bold"
                            className="opacity-75 group-hover:opacity-100"
                          >
                            {b.name} {isSub && '(SUBMERGED)'}
                          </text>
                        </g>
                      );
                    })}
                </svg>

                {/* Map Floating Legend */}
                <div className="absolute top-3 left-3 bg-[#0A1022]/90 backdrop-blur-md border border-[#1C2D54] p-2.5 rounded-lg text-[10px] font-mono text-slate-300 space-y-1 shadow-lg">
                  <div className="font-bold text-cyan-300 uppercase">Routing Legend:</div>
                  <div className="flex items-center gap-1.5"><span className="w-3 h-1 bg-[#10B981] rounded" /> Primary Route (Safest)</div>
                  <div className="flex items-center gap-1.5"><span className="w-3 h-1 bg-[#F59E0B] border-dashed border-t" /> Alternative Route</div>
                  <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#10B981]" /> Evacuation Origin</div>
                  <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#EF4444]" /> Safe Destination</div>
                  <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rotate-45 bg-[#EF4444]" /> Submerged Bridge</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 2: CRITICAL BRIDGES & DAM DISCHARGE SIMULATION */}
      {/* ==================================================================== */}
      {activeTab === 'bridges' && (
        <div className="space-y-6">
          {/* Discharge Slider Control */}
          <div className="bg-[#0D152A] border border-[#1E325F]/70 rounded-2xl p-6 space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div>
                <h3 className="text-base font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Gauge className="w-5 h-5 text-amber-400" />
                  Khadakwasla Dam Release What-If Scenario Simulation (Not Live WRD Telemetry)
                </h3>
                <span className="text-xs text-slate-400 font-mono">
                  Simulate what-if spillway discharge scenarios to evaluate bridge submergence and causeway closures along the Mula-Mutha river. NOTE: What-if analytical simulation only; does NOT modify live databases or represent real-time WRD telemetry.
                </span>
              </div>

              <div className="flex items-center gap-2 font-mono">
                <span className="text-xs text-slate-400">Current Simulation:</span>
                <span className="text-xl font-bold text-amber-300">{simulatedDischarge.toLocaleString()} cfs</span>
              </div>
            </div>

            {/* Slider Input */}
            <div className="space-y-2">
              <input
                type="range"
                min="0"
                max="60000"
                step="2500"
                value={simulatedDischarge}
                onChange={(e) => handleSimulateDischarge(parseFloat(e.target.value))}
                className="w-full h-2.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-400"
              />
              <div className="flex justify-between text-[10px] font-mono text-slate-500">
                <span>0 cfs (Baseline - No Live Telemetry)</span>
                <span>15,000 cfs (Bhide Benchmark)</span>
                <span>35,000 cfs (Alert Margin)</span>
                <span>60,000 cfs (High Cloudburst)</span>
              </div>
            </div>

            {/* Benchmark Alert Note */}
            <div className="p-3 bg-amber-950/20 border border-amber-600/30 rounded-xl text-xs font-mono text-amber-200 flex items-start gap-2">
              <Info className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <span>
                <strong>Operational Simulation Benchmark:</strong> Baba Bhide Bridge is an unverified local operational reference (~15,000 cfs) derived from media reports during monsoon discharges; NOT an official CWC/WRD hydraulic rating curve. High-level bridges (Sambhaji, Bund Garden, Shivaji) lack calibrated submergence rating curves.
              </span>
            </div>
          </div>

          {/* Monitored Bridges Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {infrastructure.map((bridge) => {
              const isSubmerged = bridge.is_submerged_simulated || bridge.is_closed;
              return (
                <div
                  key={bridge.id}
                  className={`p-4 rounded-xl border font-mono space-y-2 transition-all ${isSubmerged
                      ? 'bg-rose-950/30 border-rose-600/70'
                      : 'bg-[#0D152A] border-[#1E325F]/70'
                    }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">{bridge.name}</span>
                    <span
                      className={`text-[9px] font-bold px-2 py-0.5 rounded ${isSubmerged
                          ? 'bg-rose-900 text-rose-200'
                          : bridge.status?.includes('DATA_INSUFFICIENT')
                          ? 'bg-slate-800 text-slate-300 border border-slate-600'
                          : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                        }`}
                    >
                      {bridge.status}
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-400 space-y-1">
                    <div className="flex justify-between">
                      <span>Structure Type:</span>
                      <strong className="text-slate-200">
                        {bridge.infrastructure_type} {bridge.osm_id ? `(OSM #${bridge.osm_id})` : ''}
                      </strong>
                    </div>
                    <div className="flex justify-between">
                      <span>Submergence Benchmark:</span>
                      <strong className="text-amber-400">
                        {bridge.unverified_operational_reference_cfs ? `${bridge.unverified_operational_reference_cfs.toLocaleString()} cfs (Unverified)` : 'No rating curve available'}
                      </strong>
                    </div>
                    <div className="flex justify-between">
                      <span>Coordinates:</span>
                      <span className="text-slate-400">{bridge.latitude.toFixed(4)}, {bridge.longitude.toFixed(4)}</span>
                    </div>
                  </div>

                  <p className="text-[10px] text-slate-400 pt-1 border-t border-slate-800 italic">
                    {bridge.status_reason}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 3: MUNICIPAL ROAD CLOSURES & BLOCKAGES */}
      {/* ==================================================================== */}
      {activeTab === 'closures' && (
        <div className="space-y-6">
          <div className="bg-[#0D152A] border border-[#1E325F]/70 rounded-2xl p-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1E325F]/60 pb-4">
              <div>
                <h3 className="text-base font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Lock className="w-5 h-5 text-rose-400" />
                  Active Municipal Road Closures & Police Barricades
                </h3>
                <span className="text-xs text-slate-400 font-mono">
                  Managed road closures dynamically penalize edges with infinite cost, strictly excluding them from evacuation routes.
                </span>
              </div>

              <button
                onClick={() => setShowClosureModal(true)}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-mono text-xs font-bold flex items-center gap-2 transition-all"
              >
                <AlertCircle className="w-4 h-4" />
                <span>Register Emergency Closure</span>
              </button>
            </div>

            {/* Authority Authentication Session Bar */}
            <div className="mt-4 bg-[#0A1022] border border-[#1E325F] rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4 text-amber-400" />
                <span className="text-slate-300 font-bold">Authority Authentication:</span>
                <span className="text-slate-400 text-[11px]">
                  {isTokenSaved ? "Session authenticated for administrative write operations." : "Token required for registering/clearing closures."}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="password"
                  value={authorityTokenInput}
                  onChange={(e) => {
                    setAuthorityTokenInput(e.target.value);
                    setIsTokenSaved(false);
                  }}
                  placeholder="Enter Authority Secret Token"
                  className="bg-[#050B18] border border-[#1C2D54] rounded px-2.5 py-1 text-slate-200 text-xs w-56"
                />
                <button
                  type="button"
                  onClick={() => {
                    apiService.setAuthorityToken(authorityTokenInput);
                    setIsTokenSaved(!!authorityTokenInput.trim());
                    alert(authorityTokenInput.trim() ? "Authority token saved to session." : "Authority token cleared.");
                  }}
                  className={`px-3 py-1 rounded text-white font-bold text-xs transition-all ${
                    isTokenSaved ? "bg-emerald-600 hover:bg-emerald-500" : "bg-indigo-600 hover:bg-indigo-500"
                  }`}
                >
                  {isTokenSaved ? "Authenticated" : "Authenticate"}
                </button>
              </div>
            </div>

            {/* Closures Table */}
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-[#1E325F] text-slate-400 text-[11px] uppercase">
                    <th className="py-2 px-3">Edge ID</th>
                    <th className="py-2 px-3">Road Name</th>
                    <th className="py-2 px-3">Closure Reason</th>
                    <th className="py-2 px-3">Reporting Authority</th>
                    <th className="py-2 px-3">Registered At</th>
                    <th className="py-2 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E325F]/40 text-slate-300">
                  {closures.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-slate-500 italic">
                        No active road closures registered. All graph edges are routable based on free-flow speeds.
                      </td>
                    </tr>
                  ) : (
                    closures.map((c) => (
                      <tr key={c.id} className="hover:bg-slate-800/20">
                        <td className="py-2.5 px-3 text-cyan-300 font-bold">{c.edge_id}</td>
                        <td className="py-2.5 px-3 text-white font-medium">{c.road_name}</td>
                        <td className="py-2.5 px-3 text-amber-300">{c.reason}</td>
                        <td className="py-2.5 px-3 text-slate-400">{c.reporting_authority}</td>
                        <td className="py-2.5 px-3 text-slate-500 text-[10px]">
                          {new Date(c.created_at).toLocaleString()}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={() => handleClearClosure(c.id)}
                            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-emerald-950 text-slate-300 hover:text-emerald-300 border border-slate-700 hover:border-emerald-600 text-[10px] font-bold transition-all"
                          >
                            Lift Closure
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 4: EMERGENCY SHELTERS & RELIEF CENTERS */}
      {/* ==================================================================== */}
      {activeTab === 'shelters' && (
        <div className="space-y-6">
          {/* Shelter Destination Recommendation Finder */}
          <div className="bg-[#0D152A] border border-[#1E325F]/70 rounded-2xl p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#1E325F]/60 pb-3">
              <div>
                <h3 className="text-base font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <LifeBuoy className="w-5 h-5 text-emerald-400" />
                  Shelter Suitability & Destination Optimizer
                </h3>
                <span className="text-xs text-slate-400 font-mono">
                  Ranks reachable relief centers based on travel time, road flood hazard avoidance, and municipal verification.
                </span>
              </div>

              <div className="flex items-center gap-3">
                <label className="flex items-center gap-1.5 text-xs font-mono text-slate-300">
                  <input
                    type="checkbox"
                    checked={recNeedMedical}
                    onChange={(e) => setRecNeedMedical(e.target.checked)}
                    className="rounded bg-[#0A1022] border-[#1C2D54] text-cyan-500"
                  />
                  <span>Needs Medical</span>
                </label>
                <label className="flex items-center gap-1.5 text-xs font-mono text-slate-300">
                  <input
                    type="checkbox"
                    checked={recNeedWheelchair}
                    onChange={(e) => setRecNeedWheelchair(e.target.checked)}
                    className="rounded bg-[#0A1022] border-[#1C2D54] text-cyan-500"
                  />
                  <span>Wheelchair Accessible</span>
                </label>
                <button
                  onClick={handleFindShelterRecommendations}
                  disabled={recsLoading}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold flex items-center gap-2 transition-all disabled:opacity-50"
                >
                  {recsLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Navigation className="w-4 h-4" />}
                  <span>Find Best Shelters</span>
                </button>
              </div>
            </div>

            {/* Recommendations Results */}
            {shelterRecs && (
              <div className="space-y-4 pt-2">
                {shelterRecs.status === 'NO_VERIFIED_SHELTER_AVAILABLE' && (
                  <div className="p-4 bg-amber-950/40 border border-amber-600/50 rounded-xl space-y-2 font-mono text-xs text-amber-200">
                    <div className="flex items-center gap-2 font-bold text-amber-300">
                      <AlertTriangle className="w-5 h-5 text-amber-400" />
                      <span>NO OFFICIALLY VERIFIED SHELTERS CURRENTLY CONFIRMED</span>
                    </div>
                    <p className="text-[11px] text-amber-200/90 leading-relaxed">
                      Municipal authorities have not yet signed off verified capacity or evidence documentation for emergency shelters in the database.
                      The candidate facilities below are listed for manual scout review and field verification by emergency teams.
                    </p>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {(shelterRecs.candidate_facilities_for_review && shelterRecs.candidate_facilities_for_review.length > 0
                    ? shelterRecs.candidate_facilities_for_review
                    : shelterRecs.recommendations
                  ).map((rec, rIdx) => (
                    <div
                      key={rIdx}
                      className="p-4 bg-[#0A1022] border border-[#1C2D54] rounded-xl font-mono text-xs space-y-2.5"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <strong className="text-white text-sm">{rec.shelter.name}</strong>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-950 text-cyan-300 border border-cyan-800">
                          Score: {rec.suitability_score}
                        </span>
                      </div>

                      <div className="space-y-1 text-[11px] text-slate-400">
                        <div className="flex justify-between">
                          <span>Verification Tier:</span>
                          <span className="text-amber-300 font-bold">{rec.shelter.verification_status}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Distance:</span>
                          <strong className="text-white">{(rec.distance_to_origin_m / 1000).toFixed(2)} km</strong>
                        </div>
                        <div className="flex justify-between">
                          <span>Est. Transit Time:</span>
                          <strong className="text-emerald-400">{(rec.estimated_travel_time_sec / 60).toFixed(1)} mins</strong>
                        </div>
                        <div className="flex justify-between">
                          <span>Capacity Status:</span>
                          <strong className="text-cyan-400">{rec.capacity_status}</strong>
                        </div>
                      </div>

                      <p className="text-[10px] text-slate-300 border-t border-[#1C2D54] pt-2 italic">
                        "{rec.ranking_rationale}"
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* All Registered Shelters Directory */}
          <div className="bg-[#0D152A] border border-[#1E325F]/70 rounded-2xl p-6">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-2 font-mono">
              <Users className="w-4 h-4 text-cyan-400" />
              Registered Relief Centers & Capacity Tracking
            </h3>

            {/* Verification Status Notice */}
            <div className="mb-4 p-3.5 bg-blue-950/30 border border-blue-600/40 rounded-xl text-xs font-mono text-blue-200 flex items-start gap-2.5">
              <Info className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
              <div className="space-y-1">
                <strong className="text-cyan-300 block">Field Verification Status: 0 Officially Verified Shelters on File</strong>
                <p className="text-[11px] text-slate-300 leading-relaxed">
                  All 64 facilities below are derived from OpenStreetMap community records and classified as <strong>CANDIDATE_SHELTER</strong> or <strong>UNVERIFIED_FACILITY</strong> with unknown capacities until official DDMA / PMC gazette documents are attached.
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-[#1E325F] text-slate-400 text-[11px] uppercase">
                    <th className="py-2 px-3">Facility Name</th>
                    <th className="py-2 px-3">Verification Tier</th>
                    <th className="py-2 px-3">Total Capacity</th>
                    <th className="py-2 px-3">Occupancy</th>
                    <th className="py-2 px-3">Available</th>
                    <th className="py-2 px-3">Amenities</th>
                    <th className="py-2 px-3">Evidence Doc</th>
                    <th className="py-2 px-3">Verified By</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E325F]/40 text-slate-300">
                  {shelters.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-800/20">
                      <td className="py-2.5 px-3 text-white font-medium">
                        {s.name} {s.osm_id ? <span className="text-slate-500 text-[10px]">(OSM #{s.osm_id})</span> : null}
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`text-[9px] font-bold px-2 py-0.5 rounded ${s.verification_status === 'VERIFIED_SHELTER'
                              ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                              : s.verification_status === 'CANDIDATE_SHELTER'
                              ? 'bg-amber-950 text-amber-300 border border-amber-800'
                              : 'bg-slate-800 text-slate-400 border border-slate-700'
                            }`}
                        >
                          {s.verification_status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-300">
                        {s.total_capacity !== null && s.total_capacity !== undefined ? s.total_capacity : 'Unknown / Not verified'}
                      </td>
                      <td className="py-2.5 px-3 text-slate-300">
                        {s.current_occupancy !== null && s.current_occupancy !== undefined ? s.current_occupancy : 'Unknown'}
                      </td>
                      <td className="py-2.5 px-3 text-cyan-300 font-bold">
                        {s.available_capacity !== null && s.available_capacity !== undefined ? s.available_capacity : 'Unknown'}
                      </td>
                      <td className="py-2.5 px-3 text-[10px] text-slate-400">
                        {s.has_medical_support && '🩺 Med '}
                        {s.is_wheelchair_accessible && '♿ Access '}
                        {s.has_generator_power && '⚡ Gen'}
                      </td>
                      <td className="py-2.5 px-3 text-[10px] text-slate-400">
                        {s.evidence_document || 'None on file'}
                      </td>
                      <td className="py-2.5 px-3 text-slate-500 text-[10px]">{s.verified_by || 'Unassigned'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 5: NETWORK TOPOLOGY (PHASE 3.1 VIEW) */}
      {/* ==================================================================== */}
      {activeTab === 'topology' && (
        <div className="space-y-6">
          {/* KPI Strip */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-4 rounded-xl bg-[#0D152A] border border-[#1E325F]/70 text-center">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Source Features</span>
              <div className="text-2xl font-bold font-mono text-white mt-1">{status?.source_features_count || 906}</div>
              <span className="text-[9px] font-mono text-cyan-400 mt-0.5 block">Arterials</span>
            </div>

            <div className="p-4 rounded-xl bg-[#0D152A] border border-[#1E325F]/70 text-center">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Graph Nodes</span>
              <div className="text-2xl font-bold font-mono text-cyan-300 mt-1">{status?.node_count || 1067}</div>
              <span className="text-[9px] font-mono text-slate-500 mt-0.5 block">{status?.graph_type || 'MultiDiGraph'}</span>
            </div>

            <div className="p-4 rounded-xl bg-[#0D152A] border border-[#1E325F]/70 text-center">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Directed Edges</span>
              <div className="text-2xl font-bold font-mono text-emerald-300 mt-1">{status?.edge_count || 1488}</div>
              <span className="text-[9px] font-mono text-cyan-400 mt-0.5 block">{status?.parallel_edges_count || 6} Parallel</span>
            </div>

            <div className="p-4 rounded-xl bg-[#0D152A] border border-[#1E325F]/70 text-center">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Mapped Length</span>
              <div className="text-2xl font-bold font-mono text-amber-300 mt-1">{status?.total_mapped_length_km || 159.8} km</div>
              <span className="text-[9px] font-mono text-slate-500 mt-0.5 block">Tolerance: 3.5m</span>
            </div>

            <div className="p-4 rounded-xl bg-[#0D152A] border border-[#1E325F]/70 text-center">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Connected Comps</span>
              <div className="text-2xl font-bold font-mono text-purple-300 mt-1">{status?.connected_components_count || 89}</div>
              <span className="text-[9px] font-mono text-slate-500 mt-0.5 block">Sub-networks</span>
            </div>

            <div className="p-4 rounded-xl bg-[#0D152A] border border-[#1E325F]/70 text-center">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Largest Comp</span>
              <div className="text-2xl font-bold font-mono text-cyan-400 mt-1">{status?.largest_component_percentage || 25.2}%</div>
              <span className="text-[9px] font-mono text-slate-500 mt-0.5 block">{status?.largest_component_nodes || 269} Nodes</span>
            </div>
          </div>

          {/* Rebuild & Topology Controls */}
          <div className="p-4 bg-[#0D152A] border border-[#1E325F]/70 rounded-2xl flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-xs font-bold text-white font-mono uppercase block">Graph Topology Integrity & Snapping Engine</span>
              <span className="text-[11px] text-slate-400 font-mono">
                Preserves layer-separated bridge crossings and rejects false median cross-links on arterial corridors.
              </span>
            </div>
            <button
              onClick={() => setShowRebuildModal(true)}
              className="px-3.5 py-1.5 rounded-xl bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-800 text-cyan-300 font-mono text-xs font-bold flex items-center gap-2"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Rebuild Graph</span>
            </button>
          </div>
        </div>
      )}

      {/* Emergency Road Closure Modal */}
      {showClosureModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0D152A] border border-[#1E325F] rounded-2xl p-6 max-w-md w-full space-y-4 font-mono">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Lock className="w-4 h-4 text-rose-400" />
              Register Municipal Road Closure
            </h3>
            <p className="text-xs text-slate-400">
              Enter the affected graph edge ID and closure reason. Active closures dynamically exclude edges from evacuation routes.
            </p>

            <form onSubmit={handleCreateClosure} className="space-y-3">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Road Graph Edge ID (e.g. edge_101):</label>
                <input
                  type="text"
                  required
                  value={newClosureEdgeId}
                  onChange={(e) => setNewClosureEdgeId(e.target.value)}
                  className="w-full bg-[#0A1022] border border-[#1C2D54] rounded px-3 py-1.5 text-xs text-slate-200"
                  placeholder="edge_123"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Road / Corridor Name:</label>
                <input
                  type="text"
                  required
                  value={newClosureRoadName}
                  onChange={(e) => setNewClosureRoadName(e.target.value)}
                  className="w-full bg-[#0A1022] border border-[#1C2D54] rounded px-3 py-1.5 text-xs text-slate-200"
                  placeholder="Sinhagad Road Submerged Sector"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Reason for Closure:</label>
                <input
                  type="text"
                  required
                  value={newClosureReason}
                  onChange={(e) => setNewClosureReason(e.target.value)}
                  className="w-full bg-[#0A1022] border border-[#1C2D54] rounded px-3 py-1.5 text-xs text-slate-200"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Reporting Authority:</label>
                <input
                  type="text"
                  required
                  value={newClosureAuthority}
                  onChange={(e) => setNewClosureAuthority(e.target.value)}
                  className="w-full bg-[#0A1022] border border-[#1C2D54] rounded px-3 py-1.5 text-xs text-slate-200"
                />
              </div>

              {!isTokenSaved && (
                <div>
                  <label className="text-[11px] text-amber-400 block mb-1 flex items-center gap-1">
                    <Key className="w-3 h-3" />
                    Authority Secret Token (Required):
                  </label>
                  <input
                    type="password"
                    required
                    value={authorityTokenInput}
                    onChange={(e) => setAuthorityTokenInput(e.target.value)}
                    className="w-full bg-[#0A1022] border border-amber-500/50 rounded px-3 py-1.5 text-xs text-amber-200"
                    placeholder="Enter Authority Secret"
                  />
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowClosureModal(false)}
                  className="px-3 py-1.5 rounded bg-slate-800 text-slate-400 text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold"
                >
                  Confirm Closure
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Graph Rebuild Modal */}
      {showRebuildModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0D152A] border border-[#1E325F] rounded-2xl p-6 max-w-md w-full space-y-4 font-mono">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Key className="w-4 h-4 text-cyan-400" />
              Rebuild NetworkX MultiDiGraph
            </h3>
            <p className="text-xs text-slate-400">
              Reconstructing the MultiDiGraph from raw OSM geometries requires an authorized administrator token.
            </p>

            <form onSubmit={handleRebuild} className="space-y-3">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Authorization Token:</label>
                <input
                  type="password"
                  required
                  value={rebuildToken}
                  onChange={(e) => setRebuildToken(e.target.value)}
                  className="w-full bg-[#0A1022] border border-[#1C2D54] rounded px-3 py-1.5 text-xs text-slate-200"
                  placeholder="floodx-road-network-rebuild-2026"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowRebuildModal(false)}
                  className="px-3 py-1.5 rounded bg-slate-800 text-slate-400 text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={rebuilding}
                  className="px-4 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold disabled:opacity-50"
                >
                  {rebuilding ? 'Rebuilding...' : 'Execute Rebuild'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default RoadNetworkPage;
