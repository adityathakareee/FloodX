import React, { useEffect, useState } from 'react';
import {
  Activity,
  Database,
  CloudRain,
  Waves,
  MapPin,
  AlertTriangle,
  RefreshCw,
  Play,
  Layers,
  CheckCircle,
  FileText,
  Clock,
  ShieldAlert,
  Cpu,
} from 'lucide-react';
import { apiService } from '../services/api';
import {
  IngestionOverview,
  DataSourceItem,
  IngestionLogItem,
  DataQualityIssueItem,
  RainfallObservationItem,
  WeatherObservationItem,
  RiverLevelObservationItem,
  SpatialFeatureItem,
  RainfallSummary,
  FeatureSummary,
  IntegratedSampleRecord,
} from '../types/api';
import { StatusPill } from '../components/common/StatusPill';

export const DataIntelligencePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'rainfall' | 'river' | 'weather' | 'gis' | 'quality' | 'features'>('overview');
  const [loading, setLoading] = useState<boolean>(true);
  const [runningIngestion, setRunningIngestion] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [overview, setOverview] = useState<IngestionOverview | null>(null);
  const [sources, setSources] = useState<DataSourceItem[]>([]);
  const [logs, setLogs] = useState<IngestionLogItem[]>([]);
  const [qualityIssues, setQualityIssues] = useState<DataQualityIssueItem[]>([]);
  const [rainfallSummary, setRainfallSummary] = useState<RainfallSummary | null>(null);
  const [rainfallSample, setRainfallSample] = useState<RainfallObservationItem[]>([]);
  const [riverSample, setRiverSample] = useState<RiverLevelObservationItem[]>([]);
  const [weatherSample, setWeatherSample] = useState<WeatherObservationItem[]>([]);
  const [gisSample, setGisSample] = useState<SpatialFeatureItem[]>([]);
  const [featuresSummary, setFeaturesSummary] = useState<FeatureSummary | null>(null);
  const [integratedSample, setIntegratedSample] = useState<IntegratedSampleRecord[]>([]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [ov, srcList, logList, qList, rainSum] = await Promise.all([
        apiService.getIngestionOverview(),
        apiService.getDataSources(),
        apiService.getIngestionLogs(10),
        apiService.getDataQualityIssues(),
        apiService.getRainfallSummary().catch(() => null),
      ]);

      setOverview(ov);
      setSources(srcList);
      setLogs(logList);
      setQualityIssues(qList);
      setRainfallSummary(rainSum);

      // Load sample tables and features in background
      apiService.getRainfallObservations({ limit: 10 }).then((res) => setRainfallSample(res.items)).catch(() => {});
      apiService.getRiverLevelObservations({ limit: 10 }).then((res) => setRiverSample(res.items)).catch(() => {});
      apiService.getWeatherObservations({ limit: 10 }).then((res) => setWeatherSample(res.items)).catch(() => {});
      apiService.getGISFeatures({ limit: 10 }).then((res) => setGisSample(res.items)).catch(() => {});
      apiService.getFeaturesSummary().then(setFeaturesSummary).catch(() => {});
      apiService.getIntegratedFeaturesSample(24, 0).then((res) => setIntegratedSample(res.records)).catch(() => {});
    } catch (err: any) {
      setError(err?.message || 'Failed to communicate with FLOOD-X Ingestion API');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunPipeline = async () => {
    try {
      setRunningIngestion(true);
      await apiService.triggerIngestion('all', true);
      await loadData();
    } catch (err: any) {
      alert(`Pipeline execution error: ${err?.message}`);
    } finally {
      setRunningIngestion(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1E325F]/60 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 uppercase font-semibold">
              PHASE 1 • STAGE 3 HYDROLOGICAL FEATURES
            </span>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/30">
              POSTGIS 3.4 ACTIVE
            </span>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-semibold">
              PARQUET + POSTGRES CATALOG
            </span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-wide">
            Data Intelligence & Monitoring Center
          </h1>
          <p className="text-sm text-slate-400 font-mono mt-0.5">
            Mula-Mutha Basin Multi-Source Telemetry, Spatial Ingestion & Semantic Integrity Engine
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-[#121F3D] hover:bg-[#1A2C56] text-slate-200 text-xs font-mono font-medium border border-[#1E325F] transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
            Refresh
          </button>
          <button
            onClick={handleRunPipeline}
            disabled={runningIngestion}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 text-xs font-mono font-bold shadow-[0_0_15px_rgba(0,240,255,0.3)] transition-all disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${runningIngestion ? 'animate-spin' : 'fill-slate-950'}`} />
            {runningIngestion ? 'Ingesting Feeds...' : 'Run Ingestion'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-4 rounded-xl bg-[#091024] border border-[#1E325F]/60 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-mono uppercase tracking-wider">Data Sources</span>
            <Database className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {overview?.counts.data_sources ?? 6}
          </div>
          <div className="text-[10px] text-cyan-400/80 font-mono mt-1">Multi-Source Feeds</div>
        </div>

        <div className="p-4 rounded-xl bg-[#091024] border border-[#1E325F]/60 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-mono uppercase tracking-wider">Rainfall Obs</span>
            <CloudRain className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {overview?.counts.rainfall_observations?.toLocaleString() ?? '50,735'}
          </div>
          <div className="text-[10px] text-emerald-400 font-mono mt-1">CWPRS + CHIRPS v3</div>
        </div>

        <div className="p-4 rounded-xl bg-[#091024] border border-[#1E325F]/60 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-mono uppercase tracking-wider">River Stages</span>
            <Waves className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {overview?.counts.river_level_observations?.toLocaleString() ?? '32,655'}
          </div>
          <div className="text-[10px] text-amber-400 font-mono mt-1">Regional Reference Only</div>
        </div>

        <div className="p-4 rounded-xl bg-[#091024] border border-[#1E325F]/60 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-mono uppercase tracking-wider">GIS Features</span>
            <MapPin className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {overview?.counts.spatial_features?.toLocaleString() ?? '1,307'}
          </div>
          <div className="text-[10px] text-emerald-400 font-mono mt-1">6 PostGIS Layers</div>
        </div>

        <div className="p-4 rounded-xl bg-[#091024] border border-[#1E325F]/60 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-mono uppercase tracking-wider">Weather NWP</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {overview?.counts.weather_observations?.toLocaleString() ?? '456'}
          </div>
          <div className="text-[10px] text-cyan-400 font-mono mt-1">Observed + Forecast</div>
        </div>

        <div className="p-4 rounded-xl bg-[#091024] border border-[#1E325F]/60 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-mono uppercase tracking-wider">Quality Audits</span>
            <ShieldAlert className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-amber-400 font-mono">
            {overview?.counts.data_quality_issues ?? 8}
          </div>
          <div className="text-[10px] text-amber-400 font-mono mt-1">Caveats Documented</div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-[#1E325F]/60 gap-1 overflow-x-auto pb-px">
        {[
          { id: 'overview', label: 'Sources & Ingestion Logs', icon: Database },
          { id: 'features', label: 'Hydrological Features & Master Table', icon: Cpu },
          { id: 'rainfall', label: 'Rainfall Telemetry & Resets', icon: CloudRain },
          { id: 'river', label: 'River Levels (Sangli Caveat)', icon: Waves },
          { id: 'weather', label: 'Numerical Weather & Soil', icon: Activity },
          { id: 'gis', label: 'PostGIS GIS Infrastructure', icon: Layers },
          { id: 'quality', label: 'Data Quality & Audit Rules', icon: ShieldAlert },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2.5 text-xs font-mono font-medium border-b-2 transition-all whitespace-nowrap ${
                isActive
                  ? 'border-cyan-400 text-cyan-300 bg-cyan-500/10'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-[#121F3D]/40'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* TAB CONTENT: FEATURES */}
      {activeTab === 'features' && (
        <div className="space-y-6">
          {/* Feature Engineering Overview Banner */}
          <div className="p-6 rounded-2xl bg-gradient-to-r from-[#0d1b3a] to-[#091024] border border-cyan-500/30">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[11px] font-mono px-2.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 uppercase font-bold">
                    STAGE 3 • HYDROLOGICAL FEATURE ENGINEERING
                  </span>
                  <span className="text-[11px] font-mono px-2.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    6 CATALOGED FEATURE DATASETS
                  </span>
                </div>
                <h2 className="text-xl font-black text-white">
                  Multi-Modal Hydrological & Topographic Feature Store
                </h2>
                <p className="text-xs text-slate-300 font-mono mt-1 max-w-3xl leading-relaxed">
                  Engineered predictors across multi-scale rainfall rolling windows, Tetens VPD, Deccan Vertisol soil saturation indices, Copernicus DSM local depression proxies, and PostGIS infrastructure distance vectors.
                </p>
              </div>

              <div className="grid grid-cols-3 gap-3 font-mono shrink-0">
                <div className="p-3 rounded-xl bg-[#070d1e] border border-[#1E325F] text-center">
                  <div className="text-[10px] text-slate-400 uppercase">Feature Sets</div>
                  <div className="text-lg font-black text-cyan-400">{featuresSummary?.total_feature_sets ?? 6}</div>
                </div>
                <div className="p-3 rounded-xl bg-[#070d1e] border border-[#1E325F] text-center">
                  <div className="text-[10px] text-slate-400 uppercase">Total Records</div>
                  <div className="text-lg font-black text-emerald-400">
                    {(featuresSummary?.total_records ?? 25307).toLocaleString()}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-[#070d1e] border border-[#1E325F] text-center">
                  <div className="text-[10px] text-slate-400 uppercase">Aligned Period</div>
                  <div className="text-lg font-black text-amber-400">288 Hrs</div>
                </div>
              </div>
            </div>
          </div>

          {/* Catalog of Feature Datasets */}
          <div className="p-5 rounded-2xl bg-[#091024] border border-[#1E325F]/60">
            <h3 className="text-base font-bold text-white mb-1">Cataloged Feature Store Datasets</h3>
            <p className="text-xs text-slate-400 font-mono mb-4">
              Stored as Apache Parquet (compressed snappy) and CSV in data/features/ with SHA-256 provenance tracking
            </p>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#1E325F] text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-2.5 px-3">ID</th>
                    <th className="py-2.5 px-3">Dataset Name</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3 text-right">Records</th>
                    <th className="py-2.5 px-3">Temporal Bound</th>
                    <th className="py-2.5 px-3">Format & Hash</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E325F]/40 text-slate-300">
                  {featuresSummary?.feature_sets?.map((ds) => (
                    <tr key={ds.id} className="hover:bg-[#121F3D]/50 transition-colors">
                      <td className="py-3 px-3 text-slate-400 font-bold">#{ds.id}</td>
                      <td className="py-3 px-3 font-semibold text-white">
                        <div>{ds.feature_set_name}</div>
                        <div className="text-[10px] text-slate-400 font-sans mt-0.5 line-clamp-1">{ds.quality_notes}</div>
                      </td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          ds.category === 'RAINFALL' ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30' :
                          ds.category === 'WEATHER' ? 'bg-blue-500/15 text-blue-300 border border-blue-500/30' :
                          ds.category === 'TERRAIN' ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' :
                          ds.category === 'GEOSPATIAL' ? 'bg-purple-500/15 text-purple-300 border border-purple-500/30' :
                          'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                        }`}>
                          {ds.category}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right font-bold text-white">
                        {ds.total_records.toLocaleString()}
                      </td>
                      <td className="py-3 px-3 text-slate-400 text-[11px]">{ds.temporal_range}</td>
                      <td className="py-3 px-3">
                        <span className="text-[10px] text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800">
                          PARQUET ({ds.provenance_manifest?.parquet_sha256 ? ds.provenance_manifest.parquet_sha256.substring(0, 10) + '...' : 'OK'})
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 4 Feature Domains Highlights Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 1. Rainfall Rolling Windows */}
            <div className="p-4 rounded-xl bg-[#091024] border border-[#1E325F]/60 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-mono text-cyan-400 font-bold uppercase">CWPRS Rolling Windows</span>
                  <CloudRain className="w-4 h-4 text-cyan-400" />
                </div>
                <div className="text-xl font-black text-white font-mono">7 Multi-Scale Sums</div>
                <p className="text-[11px] text-slate-400 font-sans mt-1">
                  15m, 30m, 1h, 3h, 6h, 12h, 24h rolling sums and intensity rates (mm/h).
                </p>
                <div className="mt-3 space-y-1 text-xs font-mono">
                  <div className="flex justify-between text-slate-300">
                    <span>Peak 1h Intensity:</span>
                    <span className="text-cyan-300 font-bold">38.8 mm/h</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Peak 24h Cloudburst:</span>
                    <span className="text-cyan-300 font-bold">145.6 mm</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Incomplete Tracking:</span>
                    <span className="text-emerald-400 font-bold">Fraction &lt; 0.8 Flag</span>
                  </div>
                </div>
              </div>
            </div>

            {/* 2. Meteorological & Soil Saturation */}
            <div className="p-4 rounded-xl bg-[#091024] border border-[#1E325F]/60 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-mono text-blue-400 font-bold uppercase">Weather & Soil Saturation</span>
                  <Activity className="w-4 h-4 text-blue-400" />
                </div>
                <div className="text-xl font-black text-white font-mono">Physical Predictors</div>
                <p className="text-[11px] text-slate-400 font-sans mt-1">
                  Tetens Vapor Pressure Deficit (VPD in kPa), wind u/v vectors, and Vertisol topsoil saturation index.
                </p>
                <div className="mt-3 space-y-1 text-xs font-mono">
                  <div className="flex justify-between text-slate-300">
                    <span>Soil Saturation Limit:</span>
                    <span className="text-blue-300 font-bold">0.45 m³/m³</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Peak Soil Saturation:</span>
                    <span className="text-emerald-400 font-bold">100% (Saturated)</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Forecast Isolation:</span>
                    <span className="text-cyan-400 font-bold">168h NWP Isolated</span>
                  </div>
                </div>
              </div>
            </div>

            {/* 3. Copernicus DSM Terrain Depression */}
            <div className="p-4 rounded-xl bg-[#091024] border border-[#1E325F]/60 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-mono text-emerald-400 font-bold uppercase">Copernicus DSM Terrain</span>
                  <Layers className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="text-xl font-black text-white font-mono">228 Sampled Points</div>
                <p className="text-[11px] text-slate-400 font-sans mt-1">
                  5x5 focal neighborhood (~450m). Relative elevation Z_rel = Z - Z_min and focal slope roughness.
                </p>
                <div className="mt-3 space-y-1 text-xs font-mono">
                  <div className="flex justify-between text-slate-300">
                    <span>Depression Zones:</span>
                    <span className="text-amber-300 font-bold">Z_rel &le; 5m &amp; Slope &le; 3°</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Depression Ratio:</span>
                    <span className="text-emerald-400 font-bold">25.4% of Sampled Core</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Elevation Range:</span>
                    <span className="text-slate-300 font-bold">534m – 832m</span>
                  </div>
                </div>
              </div>
            </div>

            {/* 4. PostGIS Infrastructure Proximity */}
            <div className="p-4 rounded-xl bg-[#091024] border border-[#1E325F]/60 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-mono text-purple-400 font-bold uppercase">PostGIS Proximity</span>
                  <MapPin className="w-4 h-4 text-purple-400" />
                </div>
                <div className="text-xl font-black text-white font-mono">99 Exposure Vectors</div>
                <p className="text-[11px] text-slate-400 font-sans mt-1">
                  Exact geography ST_Distance to waterways, bridges, hospitals, schools, and arterial roads.
                </p>
                <div className="mt-3 space-y-1 text-xs font-mono">
                  <div className="flex justify-between text-slate-300">
                    <span>100m River Buffer:</span>
                    <span className="text-rose-400 font-bold">High Hazard Zone</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Direct Arterial Access:</span>
                    <span className="text-emerald-400 font-bold">&le; 150m Egress</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Medical Access:</span>
                    <span className="text-purple-300 font-bold">&lt; 2km Hospital Radius</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Master Integrated Table: July 2024 Flood Sequence */}
          <div className="p-5 rounded-2xl bg-[#091024] border border-[#1E325F]/60">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
              <div>
                <h3 className="text-base font-bold text-white">
                  Master Integrated Feature Table: July 2024 Catastrophic Flood Event
                </h3>
                <p className="text-xs text-slate-400 font-mono">
                  Continuous 288-hour multi-modal fusion across CWPRS Khadakwasla, Open-Meteo reanalysis, and CHIRPS v3 peak satellite stats
                </p>
              </div>
              <span className="text-xs font-mono text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded border border-rose-500/20">
                Local River Gauge: Excluded (Sangli 205km Away)
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#1E325F] text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-2.5 px-3">Hour (UTC)</th>
                    <th className="py-2.5 px-3 text-right">CWPRS 1h Rain</th>
                    <th className="py-2.5 px-3 text-right">CWPRS 6h Roll</th>
                    <th className="py-2.5 px-3 text-right">CWPRS 24h Roll</th>
                    <th className="py-2.5 px-3 text-right">Peak 5m Rate</th>
                    <th className="py-2.5 px-3 text-right">Soil Sat. Index</th>
                    <th className="py-2.5 px-3 text-right">VPD (kPa)</th>
                    <th className="py-2.5 px-3 text-right">CHIRPS Peak Day</th>
                    <th className="py-2.5 px-3 text-center">Cloudburst Flag</th>
                    <th className="py-2.5 px-3 text-right">Runoff Stress</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E325F]/40 text-slate-300">
                  {integratedSample.map((row, idx) => (
                    <tr key={idx} className="hover:bg-[#121F3D]/50 transition-colors">
                      <td className="py-2.5 px-3 font-semibold text-white">
                        {row.observation_time?.replace('T', ' ')?.replace(':00Z', '')}
                      </td>
                      <td className="py-2.5 px-3 text-right font-bold text-cyan-300">
                        {row.cwprs_rainfall_1h_sum_mm != null ? `${row.cwprs_rainfall_1h_sum_mm.toFixed(1)} mm` : '-'}
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-300">
                        {row.cwprs_rolling_6h_mm != null ? `${row.cwprs_rolling_6h_mm.toFixed(1)} mm` : '-'}
                      </td>
                      <td className="py-2.5 px-3 text-right font-bold text-cyan-400">
                        {row.cwprs_rolling_24h_mm != null ? `${row.cwprs_rolling_24h_mm.toFixed(1)} mm` : '-'}
                      </td>
                      <td className="py-2.5 px-3 text-right text-amber-300">
                        {row.cwprs_peak_5min_intensity_mmh != null ? `${row.cwprs_peak_5min_intensity_mmh.toFixed(1)} mm/h` : '-'}
                      </td>
                      <td className="py-2.5 px-3 text-right text-emerald-400 font-bold">
                        {row.weather_soil_saturation_index != null ? `${(row.weather_soil_saturation_index * 100).toFixed(0)}%` : '-'}
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-400">
                        {row.weather_vpd_kpa != null ? `${row.weather_vpd_kpa.toFixed(2)}` : '-'}
                      </td>
                      <td className="py-2.5 px-3 text-right text-blue-300 font-bold">
                        {row.has_chirps_daily && row.chirps_basin_max_mm_day != null
                          ? `${row.chirps_basin_max_mm_day.toFixed(0)} mm`
                          : '-'}
                      </td>
                      <td className="py-2.5 px-3 text-center">
                        {row.cloudburst_trigger_flag ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                            TRIGGER
                          </span>
                        ) : (
                          <span className="text-slate-600 text-[10px] font-mono">NORMAL</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-right font-bold text-amber-400">
                        {row.runoff_susceptibility_score != null ? row.runoff_susceptibility_score.toFixed(2) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Data Sources Catalog */}
          <div className="p-5 rounded-2xl bg-[#091024] border border-[#1E325F]/60">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-white">Registered Multi-Source Environmental Catalog</h3>
                <p className="text-xs text-slate-400 font-mono">Integrated sources powering FLOOD-X analytics</p>
              </div>
              <span className="text-xs font-mono text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded border border-cyan-500/20">
                {sources.length} Catalogued
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#1E325F] text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-2.5 px-3">Source Name</th>
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3">Provider</th>
                    <th className="py-2.5 px-3">Format</th>
                    <th className="py-2.5 px-3">Resolution / Cadence</th>
                    <th className="py-2.5 px-3">Units</th>
                    <th className="py-2.5 px-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E325F]/40 text-slate-300">
                  {sources.map((src) => (
                    <tr key={src.id} className="hover:bg-[#121F3D]/30 transition-colors">
                      <td className="py-3 px-3 font-semibold text-white">
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(0,240,255,0.6)]"></span>
                          {src.source_name}
                        </div>
                      </td>
                      <td className="py-3 px-3 text-cyan-300">{src.source_type}</td>
                      <td className="py-3 px-3 text-slate-400">{src.provider}</td>
                      <td className="py-3 px-3">{src.data_format}</td>
                      <td className="py-3 px-3 text-slate-400">{src.temporal_resolution || src.spatial_resolution || 'N/A'}</td>
                      <td className="py-3 px-3 text-slate-400">{src.units || 'Metric'}</td>
                      <td className="py-3 px-3 text-right">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                          ACTIVE
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Ingestion Execution Logs */}
          <div className="p-5 rounded-2xl bg-[#091024] border border-[#1E325F]/60">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-white">Recent Ingestion Audit Logs</h3>
                <p className="text-xs text-slate-400 font-mono">Transactional execution tracking with record insertion counters</p>
              </div>
              <span className="text-xs font-mono text-slate-400">Total Runs: {logs.length}</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#1E325F] text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-2.5 px-3">Run ID</th>
                    <th className="py-2.5 px-3">Target File / Feed</th>
                    <th className="py-2.5 px-3">Started</th>
                    <th className="py-2.5 px-3">Completed</th>
                    <th className="py-2.5 px-3 text-right">Records Read</th>
                    <th className="py-2.5 px-3 text-right">Inserted</th>
                    <th className="py-2.5 px-3 text-right">Skipped</th>
                    <th className="py-2.5 px-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E325F]/40 text-slate-300">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-[#121F3D]/30 transition-colors">
                      <td className="py-2.5 px-3 text-slate-400">#{log.id}</td>
                      <td className="py-2.5 px-3 text-white font-medium">{log.file_name || 'Multi-source stream'}</td>
                      <td className="py-2.5 px-3 text-slate-400">{new Date(log.started_at).toLocaleTimeString()}</td>
                      <td className="py-2.5 px-3 text-slate-400">{log.completed_at ? new Date(log.completed_at).toLocaleTimeString() : 'In-flight'}</td>
                      <td className="py-2.5 px-3 text-right font-semibold text-slate-300">{log.records_read.toLocaleString()}</td>
                      <td className="py-2.5 px-3 text-right font-semibold text-emerald-400">{log.records_inserted.toLocaleString()}</td>
                      <td className="py-2.5 px-3 text-right text-slate-400">{log.records_skipped.toLocaleString()}</td>
                      <td className="py-2.5 px-3 text-right">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            log.status === 'COMPLETED'
                              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                              : log.status === 'RUNNING'
                              ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 animate-pulse'
                              : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                          }`}
                        >
                          {log.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: RAINFALL */}
      {activeTab === 'rainfall' && (
        <div className="space-y-6">
          {/* Key Findings Card */}
          <div className="p-5 rounded-2xl bg-gradient-to-r from-blue-950/40 via-[#091024] to-[#091024] border border-blue-500/40">
            <div className="flex items-start gap-4">
              <div className="p-2.5 rounded-xl bg-blue-500/20 text-blue-400 border border-blue-500/30">
                <CloudRain className="w-6 h-6" />
              </div>
              <div className="space-y-2">
                <h3 className="text-base font-bold text-white">
                  Ground Telemetry & Satellite Ingestion Intelligence
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  • <strong className="text-cyan-300">CWPRS Khadakwasla Telemetry:</strong> 24,211 raw observations ingested at 5-minute sampling cadence.
                  The reported peak of <strong className="text-amber-300">145.6 mm</strong> on July 25, 2024 at 08:25 IST represents a <strong>24-hour cumulative daily rainfall total</strong> with an authoritative 08:30 IST bucket reset, <em>not an hourly intensity rate</em>. FLOOD-X computes derived increments and hourly accumulations.
                </p>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  • <strong className="text-cyan-300">CHIRPS v3 Satellite Sequence:</strong> Captures Pune basin-wide daily precipitation across 2020–2024 monsoon peaks, registering a peak daily basin aggregate of <strong className="text-emerald-300">162.69 mm/day</strong> on July 25, 2024 (and 344.0 mm/day single-cell maximum).
                </p>
              </div>
            </div>
          </div>

          {/* Sample Observations Table */}
          <div className="p-5 rounded-2xl bg-[#091024] border border-[#1E325F]/60">
            <h3 className="text-base font-bold text-white mb-3">Recent Rainfall Observations Feed</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#1E325F] text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-2 px-3">Station</th>
                    <th className="py-2 px-3">Time (UTC)</th>
                    <th className="py-2 px-3">Measurement Type</th>
                    <th className="py-2 px-3 text-right">Value</th>
                    <th className="py-2 px-3">Unit</th>
                    <th className="py-2 px-3 text-right">Quality Flag</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E325F]/40 text-slate-300">
                  {rainfallSample.map((r) => (
                    <tr key={r.id} className="hover:bg-[#121F3D]/30 transition-colors">
                      <td className="py-2.5 px-3 text-white font-medium">{r.station_name}</td>
                      <td className="py-2.5 px-3 text-slate-400">{new Date(r.observation_time).toLocaleString()}</td>
                      <td className="py-2.5 px-3 text-cyan-300">{r.measurement_type}</td>
                      <td className="py-2.5 px-3 text-right font-bold text-white">{r.rainfall_value.toFixed(2)}</td>
                      <td className="py-2.5 px-3 text-slate-400">{r.rainfall_unit}</td>
                      <td className="py-2.5 px-3 text-right">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] ${
                            r.quality_flag === 'VALID'
                              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                              : 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30'
                          }`}
                        >
                          {r.quality_flag}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: RIVER LEVELS */}
      {activeTab === 'river' && (
        <div className="space-y-6">
          {/* Critical Geographic Caveat Alert */}
          <div className="p-5 rounded-2xl bg-amber-500/10 border border-amber-500/40">
            <div className="flex items-start gap-4">
              <div className="p-2.5 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-white">Geographic Displacement Invariant</h3>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                    REGIONAL_REFERENCE_ONLY
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  The CWC station <strong>Ankali Bridge</strong> is situated in <strong>Sangli district</strong> on the mainstem <strong>Krishna River</strong> (16.8028° N, 74.5664° E), exactly <strong>205.3 km south</strong> of Pune.
                </p>
                <p className="text-xs text-amber-200/90 leading-relaxed font-sans bg-amber-950/40 p-3 rounded-lg border border-amber-500/20">
                  ⚠️ <strong>Architectural Rule:</strong> This telemetry is strictly maintained for regional hydrological comparison and baseline verification. <strong>Under no circumstances will it be assimilated as a local stage trigger for the Pune / Mula-Mutha river basin.</strong>
                </p>
              </div>
            </div>
          </div>

          {/* CWC Telemetry Feed Table */}
          <div className="p-5 rounded-2xl bg-[#091024] border border-[#1E325F]/60">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-white">Ankali Bridge (Sangli) Telemetry Stream</h3>
              <span className="text-xs font-mono text-slate-400">Total Ingested: 32,655 Records</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#1E325F] text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-2 px-3">Station</th>
                    <th className="py-2 px-3">River</th>
                    <th className="py-2 px-3">Timestamp (UTC)</th>
                    <th className="py-2 px-3 text-right">Water Level (m MSL)</th>
                    <th className="py-2 px-3 text-right">Geographic Relevance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E325F]/40 text-slate-300">
                  {riverSample.map((r) => (
                    <tr key={r.id} className="hover:bg-[#121F3D]/30 transition-colors">
                      <td className="py-2.5 px-3 text-white font-medium">{r.station_name}</td>
                      <td className="py-2.5 px-3 text-cyan-300">{r.river_name}</td>
                      <td className="py-2.5 px-3 text-slate-400">{new Date(r.observation_time).toLocaleString()}</td>
                      <td className="py-2.5 px-3 text-right font-bold text-white">{r.water_level.toFixed(2)} m</td>
                      <td className="py-2.5 px-3 text-right">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/15 text-amber-300 border border-amber-500/30">
                          {r.geographic_relevance}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: WEATHER */}
      {activeTab === 'weather' && (
        <div className="space-y-6">
          <div className="p-5 rounded-2xl bg-[#091024] border border-[#1E325F]/60">
            <h3 className="text-base font-bold text-white mb-2">Open-Meteo NWP Reanalysis & Forecast (Pune Basin)</h3>
            <p className="text-xs text-slate-400 font-mono mb-4">Captures 2m Temperature, Relative Humidity, Hourly Precipitation, Wind & Soil Moisture (0-7cm)</p>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#1E325F] text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-2 px-3">Category</th>
                    <th className="py-2 px-3">Time (UTC)</th>
                    <th className="py-2 px-3 text-right">Temp (°C)</th>
                    <th className="py-2 px-3 text-right">Humidity (%)</th>
                    <th className="py-2 px-3 text-right">Precip (mm)</th>
                    <th className="py-2 px-3 text-right">Wind (km/h)</th>
                    <th className="py-2 px-3 text-right">Soil Moisture (m³/m³)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E325F]/40 text-slate-300">
                  {weatherSample.map((w) => (
                    <tr key={w.id} className="hover:bg-[#121F3D]/30 transition-colors">
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            w.data_category === 'OBSERVED'
                              ? 'bg-blue-500/15 text-blue-300 border border-blue-500/30'
                              : 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30'
                          }`}
                        >
                          {w.data_category}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">{new Date(w.observation_time).toLocaleString()}</td>
                      <td className="py-2.5 px-3 text-right font-medium text-white">{w.temperature ?? '-'}</td>
                      <td className="py-2.5 px-3 text-right text-slate-300">{w.relative_humidity ?? '-'}%</td>
                      <td className="py-2.5 px-3 text-right text-cyan-300 font-bold">{w.precipitation ?? 0.0}</td>
                      <td className="py-2.5 px-3 text-right text-slate-400">{w.wind_speed ?? '-'}</td>
                      <td className="py-2.5 px-3 text-right text-emerald-400">{w.soil_moisture ?? '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: GIS INFRASTRUCTURE */}
      {activeTab === 'gis' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { type: 'EVACUATION_ROAD', count: 906, label: 'Evacuation Corridors', color: 'text-amber-400' },
              { type: 'HEALTHCARE', count: 185, label: 'Hospitals & Clinics', color: 'text-rose-400' },
              { type: 'BRIDGE', count: 158, label: 'River Bridges', color: 'text-cyan-400' },
              { type: 'EDUCATION', count: 30, label: 'Schools / Colleges', color: 'text-blue-400' },
              { type: 'WATERWAY', count: 21, label: 'Rivers & Streams', color: 'text-indigo-400' },
              { type: 'COMMUNITY_CIVIC', count: 7, label: 'Civic Shelters', color: 'text-emerald-400' },
            ].map((lyr) => (
              <div key={lyr.type} className="p-3.5 rounded-xl bg-[#091024] border border-[#1E325F]/60 text-center">
                <div className={`text-xl font-bold font-mono ${lyr.color}`}>{lyr.count}</div>
                <div className="text-[11px] font-semibold text-white mt-0.5">{lyr.label}</div>
                <div className="text-[9px] font-mono text-slate-500 uppercase tracking-wider">{lyr.type}</div>
              </div>
            ))}
          </div>

          <div className="p-5 rounded-2xl bg-[#091024] border border-[#1E325F]/60">
            <h3 className="text-base font-bold text-white mb-3">PostGIS Vector Entities Sample</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#1E325F] text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-2 px-3">Feature Type</th>
                    <th className="py-2 px-3">Name</th>
                    <th className="py-2 px-3">OSM ID</th>
                    <th className="py-2 px-3">Geometry Type</th>
                    <th className="py-2 px-3">Coordinates Preview</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E325F]/40 text-slate-300">
                  {gisSample.map((g) => (
                    <tr key={g.id} className="hover:bg-[#121F3D]/30 transition-colors">
                      <td className="py-2.5 px-3 text-cyan-300 font-semibold">{g.feature_type}</td>
                      <td className="py-2.5 px-3 text-white">{g.name || 'Unnamed Feature'}</td>
                      <td className="py-2.5 px-3 text-slate-400">{g.osm_id || '-'}</td>
                      <td className="py-2.5 px-3 text-emerald-400 font-medium">{g.geojson?.type || 'Geometry'}</td>
                      <td className="py-2.5 px-3 text-slate-500 truncate max-w-xs">
                        {JSON.stringify(g.geojson?.coordinates)?.slice(0, 40)}...
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: QUALITY & AUDIT */}
      {activeTab === 'quality' && (
        <div className="space-y-6">
          <div className="p-5 rounded-2xl bg-[#091024] border border-[#1E325F]/60">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-white">Documented Data Integrity Register & Caveats</h3>
                <p className="text-xs text-slate-400 font-mono">Strict semantic caveats captured and enforced across environmental pipelines</p>
              </div>
              <span className="text-xs font-mono px-3 py-1 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                {qualityIssues.length} Invariants Logged
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#1E325F] text-slate-400 uppercase tracking-wider text-[10px]">
                    <th className="py-2.5 px-3">Severity</th>
                    <th className="py-2.5 px-3">Issue Identifier</th>
                    <th className="py-2.5 px-3">Description & Operational Directive</th>
                    <th className="py-2.5 px-3 text-right">Affected Records</th>
                    <th className="py-2.5 px-3 text-right">Resolution</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E325F]/40 text-slate-300">
                  {qualityIssues.map((q) => (
                    <tr key={q.id} className="hover:bg-[#121F3D]/30 transition-colors">
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            q.severity === 'HIGH'
                              ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                              : q.severity === 'MEDIUM'
                              ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                              : q.severity === 'INFO'
                              ? 'bg-blue-500/15 text-blue-300 border border-blue-500/30'
                              : 'bg-slate-700/40 text-slate-300 border border-slate-600'
                          }`}
                        >
                          {q.severity}
                        </span>
                      </td>
                      <td className="py-3 px-3 font-semibold text-white">{q.issue_type}</td>
                      <td className="py-3 px-3 text-slate-300 max-w-xl font-sans text-xs leading-relaxed">{q.description}</td>
                      <td className="py-3 px-3 text-right font-mono text-cyan-400 font-semibold">
                        {q.affected_record_count.toLocaleString()}
                      </td>
                      <td className="py-3 px-3 text-right text-emerald-400 font-semibold">
                        {q.resolution_status}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataIntelligencePage;

