import React, { useState, useEffect } from 'react';
import {
  Brain,
  AlertTriangle,
  Shield,
  Activity,
  CheckCircle2,
  TrendingUp,
  Cpu,
  Layers,
  MapPin,
  Play,
  RotateCcw,
  Info,
  Sliders,
  BarChart3,
  Calendar,
  AlertCircle,
  Clock,
  Compass,
  Droplets,
  CloudRain,
  Waves,
  Radio,
  FileCheck2,
  HelpCircle
} from 'lucide-react';
import { apiService } from '../services/api';
import {
  MLStatusResponse,
  MLEvaluationResponse,
  MLExplainabilityResponse,
  SpatialSusceptibilityResponse,
  MLPredictionResponse,
  ProspectiveStatusResponse,
  ProspectiveAssessmentResponse,
  ProspectiveForecastResponse,
  ProspectiveSourcesResponse,
  ScenarioAssessmentResponse,
  HorizonProspectiveAssessment
} from '../types/api';

export const FloodRiskPage: React.FC = () => {
  // Navigation Tabs
  const [activeTab, setActiveTab] = useState<'prospective' | 'scenario' | 'retrospective'>('prospective');

  // Loading & Error State
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Phase 2.3 Prospective State
  const [prospectiveStatus, setProspectiveStatus] = useState<ProspectiveStatusResponse | null>(null);
  const [prospectiveAssessment, setProspectiveAssessment] = useState<ProspectiveAssessmentResponse | null>(null);
  const [prospectiveForecast, setProspectiveForecast] = useState<ProspectiveForecastResponse | null>(null);
  const [prospectiveSources, setProspectiveSources] = useState<ProspectiveSourcesResponse | null>(null);
  const [selectedHorizon, setSelectedHorizon] = useState<'6h' | '12h' | '24h' | '48h'>('6h');

  // Phase 2.3 Scenario Analysis State
  const [scenarioName, setScenarioName] = useState<string>('Custom Heavy Monsoon Outlook');
  const [scenarioRainMultiplier, setScenarioRainMultiplier] = useState<number>(1.5);
  const [scenarioPeak1h, setScenarioPeak1h] = useState<number>(35.0);
  const [scenarioDamDischarge, setScenarioDamDischarge] = useState<number>(15000.0);
  const [scenarioSoilMoisture, setScenarioSoilMoisture] = useState<number>(0.42);
  const [scenarioResult, setScenarioResult] = useState<ScenarioAssessmentResponse | null>(null);
  const [scenarioRunning, setScenarioRunning] = useState<boolean>(false);

  // Phase 2.2 / 2.2.1 Retrospective State
  const [mlStatus, setMlStatus] = useState<MLStatusResponse | null>(null);
  const [evaluation, setEvaluation] = useState<MLEvaluationResponse | null>(null);
  const [explainability, setExplainability] = useState<MLExplainabilityResponse | null>(null);
  const [susceptibility, setSusceptibility] = useState<SpatialSusceptibilityResponse | null>(null);
  const [precip24h, setPrecip24h] = useState<number>(35.0);
  const [antecedent3d, setAntecedent3d] = useState<number>(45.0);
  const [soilMoisture, setSoilMoisture] = useState<number>(0.42);
  const [humidity, setHumidity] = useState<number>(88.0);
  const [pressureDrop, setPressureDrop] = useState<number>(2.5);
  const [isMonsoon, setIsMonsoon] = useState<number>(1);
  const [retroPrediction, setRetroPrediction] = useState<MLPredictionResponse | null>(null);
  const [retroPredicting, setRetroPredicting] = useState<boolean>(false);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Concurrent fetch of Prospective and Retrospective endpoints
      const [
        pStatus,
        pAssess,
        pForecast,
        pSources,
        mStatus,
        mEval,
        mExplain,
        mSusp
      ] = await Promise.all([
        apiService.getProspectiveStatus().catch(() => null),
        apiService.assessProspectiveRisk().catch(() => null),
        apiService.getProspectiveForecast(48).catch(() => null),
        apiService.getProspectiveSources().catch(() => null),
        apiService.getMLStatus().catch(() => null),
        apiService.getMLEvaluation().catch(() => null),
        apiService.getMLExplainability().catch(() => null),
        apiService.getSpatialSusceptibility().catch(() => null),
      ]);

      setProspectiveStatus(pStatus);
      setProspectiveAssessment(pAssess);
      setProspectiveForecast(pForecast);
      setProspectiveSources(pSources);
      setMlStatus(mStatus);
      setEvaluation(mEval);
      setExplainability(mExplain);
      setSusceptibility(mSusp);

      // Initial scenario run
      runScenario(1.5, 35.0, 15000.0, 0.42, 'Initial What-If Scenario');

      // Initial retrospective run
      runRetroPrediction(35.0, 45.0, 0.42, 88.0, 2.5, 1);
    } catch (err: any) {
      console.error('Failed to load FLOOD-X flood risk data:', err);
      setError(err.message || 'Failed to connect to backend flood intelligence endpoints.');
    } finally {
      setLoading(false);
    }
  };

  const runScenario = async (
    mult: number,
    peak1h: number,
    discharge: number,
    sm: number,
    name: string
  ) => {
    try {
      setScenarioRunning(true);
      const res = await apiService.assessWhatIfScenario({
        scenario_name: name,
        rainfall_multiplier: mult,
        override_peak_1h_mmh: peak1h,
        simulated_dam_discharge_cfs: discharge,
        override_soil_moisture: sm,
        override_antecedent_3d_mm: 50.0
      });
      setScenarioResult(res);
    } catch (err: any) {
      console.error('Scenario run failed:', err);
    } finally {
      setScenarioRunning(false);
    }
  };

  const loadScenarioPreset = (preset: 'normal' | 'cloudburst' | 'spill' | 'compound') => {
    if (preset === 'normal') {
      setScenarioName('Baseline Monsoon Outlook');
      setScenarioRainMultiplier(1.0);
      setScenarioPeak1h(15.0);
      setScenarioDamDischarge(5000.0);
      setScenarioSoilMoisture(0.35);
      runScenario(1.0, 15.0, 5000.0, 0.35, 'Baseline Monsoon Outlook');
    } else if (preset === 'cloudburst') {
      setScenarioName('Urban Pluvial Cloudburst (Ambil Odha 2019 Analog)');
      setScenarioRainMultiplier(2.5);
      setScenarioPeak1h(55.0);
      setScenarioDamDischarge(8000.0);
      setScenarioSoilMoisture(0.48);
      runScenario(2.5, 55.0, 8000.0, 0.48, 'Urban Pluvial Cloudburst (Ambil Odha 2019 Analog)');
    } else if (preset === 'spill') {
      setScenarioName('Khadakwasla Dam Spill (Bhide Causeway Submergence)');
      setScenarioRainMultiplier(1.2);
      setScenarioPeak1h(20.0);
      setScenarioDamDischarge(15000.0);
      setScenarioSoilMoisture(0.40);
      runScenario(1.2, 20.0, 15000.0, 0.40, 'Khadakwasla Dam Spill (Bhide Causeway Submergence)');
    } else if (preset === 'compound') {
      setScenarioName('Compound Catastrophic Disaster (July 25, 2024 Benchmark)');
      setScenarioRainMultiplier(2.8);
      setScenarioPeak1h(45.0);
      setScenarioDamDischarge(35574.0);
      setScenarioSoilMoisture(0.51);
      runScenario(2.8, 45.0, 35574.0, 0.51, 'Compound Catastrophic Disaster (July 25, 2024 Benchmark)');
    }
  };

  const runRetroPrediction = async (
    p24: number,
    ant3d: number,
    sm: number,
    rh: number,
    pDrop: number,
    monsoon: number
  ) => {
    try {
      setRetroPredicting(true);
      const res = await apiService.predictFloodRisk({
        precip_total_24h: p24,
        antecedent_precip_3d: ant3d,
        soil_moisture_0_7cm_mean: sm,
        soil_moisture_0_7cm_max: Math.min(sm + 0.05, 0.52),
        soil_moisture_7_28cm_mean: sm,
        relative_humidity_mean: rh,
        pressure_drop_24h: pDrop,
        surface_pressure_mean: 948.0 - pDrop,
        vpd_mean_kpa: Math.max(0.1, 1.2 - (rh / 100) * 1.0),
        is_monsoon: monsoon,
      });
      setRetroPrediction(res);
    } catch (err: any) {
      console.error('Retrospective prediction failed:', err);
    } finally {
      setRetroPredicting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-slate-400">
        <Activity className="w-10 h-10 animate-spin text-cyan-400 mb-3" />
        <p className="font-mono text-sm">Initializing FLOOD-X Prospective Intelligence & Forecast Feeds...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-950/30 border border-red-500/40 rounded-xl text-red-200">
        <div className="flex items-center gap-2 mb-2 font-semibold">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <span>Flood Intelligence Connection Error</span>
        </div>
        <p className="text-sm font-mono">{error}</p>
        <button
          onClick={fetchAllData}
          className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-xs font-semibold"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const activeAssessment: HorizonProspectiveAssessment | undefined =
    prospectiveAssessment?.horizons[selectedHorizon];

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header Card */}
      <div className="bg-[#0D152A] border border-[#1E325F]/70 rounded-xl p-5 shadow-lg relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-[0_0_15px_rgba(0,240,255,0.2)]">
                <Brain className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2 flex-wrap">
                  Flood Risk Intelligence & Decision Support Platform
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-semibold">
                    PROSPECTIVE RISK ASSESSMENT
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 font-semibold">
                    EXPERIMENTAL RULE ENGINE
                  </span>
                  {prospectiveStatus?.forecast_freshness_status && (
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-semibold ${prospectiveStatus.forecast_freshness_status === 'LIVE_FRESH'
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                        : prospectiveStatus.forecast_freshness_status === 'CACHED_VALID'
                          ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
                          : prospectiveStatus.forecast_freshness_status === 'STALE'
                            ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                            : 'bg-red-500/20 text-red-300 border-red-500/30'
                      }`}>
                      NWP FRESHNESS: {prospectiveStatus.forecast_freshness_status}
                    </span>
                  )}
                </h1>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Pilot Basin: Pune / Mula-Mutha River Basin (18.40°N–18.65°N, 73.70°E–74.05°E) | Feed: {prospectiveStatus?.forecast_source}
                </p>
                {prospectiveStatus?.freshness_warning && (
                  <p className="text-[11px] text-amber-300 font-mono mt-1 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                    <span>{prospectiveStatus.freshness_warning}</span>
                  </p>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono px-3 py-1.5 rounded-lg bg-[#14234B] border border-[#27407D] text-slate-300 flex items-center gap-2">
              <Shield className="w-3.5 h-3.5 text-cyan-400" />
              Human-in-the-Loop Verification: ENFORCED
            </span>
          </div>
        </div>
      </div>

      {/* Tabbed Navigation Bar */}
      <div className="flex items-center gap-2 border-b border-[#1E325F] pb-2 text-xs font-mono">
        <button
          onClick={() => setActiveTab('prospective')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all ${activeTab === 'prospective'
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_15px_rgba(0,240,255,0.15)]'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
        >
          <Compass className="w-4 h-4 text-cyan-400" />
          <span>Prospective Forecast Intelligence (Live Outlook)</span>
        </button>

        <button
          onClick={() => setActiveTab('scenario')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all ${activeTab === 'scenario'
              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-[0_0_15px_rgba(245,158,11,0.15)]'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
        >
          <Sliders className="w-4 h-4 text-amber-400" />
          <span>What-If Emergency Scenario Simulator</span>
        </button>

        <button
          onClick={() => setActiveTab('retrospective')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all ${activeTab === 'retrospective'
              ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40 shadow-[0_0_15px_rgba(59,130,246,0.15)]'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
        >
          <Cpu className="w-4 h-4 text-blue-400" />
          <span>Retrospective Diagnostic Benchmark (Phase 2.2 / 2.2.1)</span>
        </button>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: PROSPECTIVE FORECAST INTELLIGENCE (LIVE OUTLOOK)                     */}
      {/* ========================================================================= */}
      {activeTab === 'prospective' && (
        <div className="space-y-6">
          {/* Horizon Selection Buttons & Issue Time */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#0D152A] border border-[#1E325F]/70 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-cyan-400" />
              <div>
                <span className="text-xs font-mono text-slate-400 block">Forecast Prediction Horizon:</span>
                <span className="text-sm font-bold text-white">Select Lead Window for Hydrometeorological Outlook</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {(['6h', '12h', '24h', '48h'] as const).map((h) => {
                const isSelected = selectedHorizon === h;
                const hData = prospectiveAssessment?.horizons[h];
                return (
                  <button
                    key={h}
                    onClick={() => setSelectedHorizon(h)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all flex items-center gap-1.5 ${isSelected
                        ? 'bg-cyan-500 text-slate-950 shadow-[0_0_12px_rgba(0,240,255,0.4)]'
                        : 'bg-[#14234B] text-slate-300 border border-[#27407D] hover:bg-[#1C3168]'
                      }`}
                  >
                    <span>{h.toUpperCase()}</span>
                    {hData && (
                      <span className={`w-2 h-2 rounded-full ${hData.overall_alert_level.includes('EMERGENCY')
                          ? 'bg-red-400'
                          : hData.overall_alert_level.includes('WARNING')
                            ? 'bg-orange-400'
                            : hData.overall_alert_level.includes('WATCH')
                              ? 'bg-amber-400'
                              : 'bg-emerald-400'
                        }`} />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Horizon Outlook Cards Grid */}
          {activeAssessment && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Separated Mechanisms (7 cols) */}
              <div className="lg:col-span-7 space-y-4">
                {/* Pluvial Risk Card */}
                <div className={`p-5 rounded-xl border transition-all ${activeAssessment.pluvial_risk.risk_tier === 'EMERGENCY'
                    ? 'bg-red-950/40 border-red-500/50'
                    : activeAssessment.pluvial_risk.risk_tier === 'WARNING'
                      ? 'bg-orange-950/40 border-orange-500/50'
                      : activeAssessment.pluvial_risk.risk_tier === 'WATCH'
                        ? 'bg-amber-950/40 border-amber-500/50'
                        : 'bg-[#0D152A] border-[#1E325F]/70'
                  }`}>
                  <div className="flex items-center justify-between border-b border-slate-700/50 pb-3">
                    <div className="flex items-center gap-2">
                      <CloudRain className="w-5 h-5 text-cyan-400" />
                      <div>
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                          Urban Pluvial Flood & Drainage Choke Risk
                        </h3>
                        <span className="text-[10px] font-mono text-slate-400">
                          Rainfall intensity vs Assumed storm drainage capacity proxy ({activeAssessment.pluvial_risk.drainage_threshold_mmh} mm/h CPHEEO proxy)
                          <span className="ml-1 text-amber-300 font-semibold">[UNVALIDATED PROXY]</span>
                        </span>
                      </div>
                    </div>
                    <span className={`text-xs font-mono font-black px-2.5 py-1 rounded ${activeAssessment.pluvial_risk.risk_tier === 'EMERGENCY'
                        ? 'bg-red-500 text-white'
                        : activeAssessment.pluvial_risk.risk_tier === 'WARNING'
                          ? 'bg-orange-500 text-white'
                          : activeAssessment.pluvial_risk.risk_tier === 'WATCH'
                            ? 'bg-amber-500 text-slate-950'
                            : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      }`}>
                      TIER: {activeAssessment.pluvial_risk.risk_tier}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-3 my-3 text-xs font-mono">
                    <div className="p-2.5 rounded bg-[#0A1022] border border-[#1C2D54]">
                      <span className="text-slate-400 block text-[10px]">Peak 1h Intensity:</span>
                      <strong className="text-cyan-300 text-sm">
                        {activeAssessment.pluvial_risk.peak_forecast_intensity_mmh} mm/h
                      </strong>
                    </div>
                    <div className="p-2.5 rounded bg-[#0A1022] border border-[#1C2D54]">
                      <span className="text-slate-400 block text-[10px]">Horizon Accumulation:</span>
                      <strong className="text-white text-sm">
                        {activeAssessment.pluvial_risk.forecast_accumulation_mm} mm
                      </strong>
                    </div>
                    <div className="p-2.5 rounded bg-[#0A1022] border border-[#1C2D54]">
                      <span className="text-slate-400 block text-[10px]">Soil Wetness Proxy:</span>
                      <strong className="text-amber-300 text-sm">
                        {(activeAssessment.pluvial_risk.antecedent_soil_saturation_ratio * 100).toFixed(0)}%
                      </strong>
                    </div>
                  </div>

                  <p className="text-xs text-slate-200 leading-relaxed font-sans mb-3">
                    <strong>Physical Reasoning: </strong>{activeAssessment.pluvial_risk.physical_reasoning}
                  </p>

                  <div className="text-[11px] font-mono text-slate-400">
                    <span className="text-slate-300 font-bold block mb-1">Contributing Factors:</span>
                    <ul className="list-disc pl-4 space-y-0.5">
                      {activeAssessment.pluvial_risk.contributing_factors.map((f, idx) => (
                        <li key={idx}>{f}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Riverine Risk Card */}
                <div className="bg-[#0D152A] border border-[#1E325F]/70 rounded-xl p-5 space-y-3">
                  <div className="flex items-center justify-between border-b border-[#1E325F]/60 pb-3">
                    <div className="flex items-center gap-2">
                      <Waves className="w-5 h-5 text-blue-400" />
                      <div>
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                          Mula-Mutha Riverine Overbank & Dam Release Risk
                        </h3>
                        <span className="text-[10px] font-mono text-slate-400">
                          Controlled by Khadakwasla Dam spillway release & upstream Western Ghats inflow
                        </span>
                      </div>
                    </div>
                    <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-blue-900/40 text-blue-300 border border-blue-500/40">
                      STATUS: {activeAssessment.riverine_risk.dam_telemetry_status}
                    </span>
                  </div>

                  {/* Dam Telemetry Notice Box */}
                  <div className="p-3 bg-[#0A1022] border border-[#1C2D54] rounded-lg text-xs font-mono space-y-2">
                    <div className="flex items-center gap-2 text-amber-300 font-bold">
                      <AlertCircle className="w-4 h-4 text-amber-400" />
                      <span>Live Khadakwasla Dam Discharge Feed: UNAVAILABLE</span>
                    </div>
                    <p className="text-[11px] text-slate-300 font-sans leading-relaxed">
                      {activeAssessment.riverine_risk.physical_reasoning}
                    </p>
                    <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px]">
                      <span className="text-slate-400">Baba Bhide Causeway Submergence:</span>
                      <span className="text-amber-300 font-bold font-mono">15,000 cfs <span className="text-[10px] text-slate-400">(Verified Municipal)</span></span>
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-slate-400">July 25, 2024 Observed Disaster Peak:</span>
                      <span className="text-red-400 font-bold font-mono">35,574 cfs <span className="text-[10px] text-slate-400">(Historical Event Benchmark)</span></span>
                    </div>
                    <div className="pt-2">
                      <button
                        onClick={() => setActiveTab('scenario')}
                        className="w-full py-1.5 rounded bg-[#162B57] hover:bg-[#203D7A] text-cyan-300 text-xs font-mono font-bold border border-[#2B4E9A]"
                      >
                        Open What-If Simulator to Test Dam Discharge Scenarios →
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column: Composite Action Guidance & Data Provenance (5 cols) */}
              <div className="lg:col-span-5 space-y-4">
                <div className="bg-[#0D152A] border border-[#1E325F]/70 rounded-xl p-5 space-y-4">
                  <div className="flex items-center gap-2 border-b border-[#1E325F]/60 pb-3">
                    <Radio className="w-5 h-5 text-cyan-400" />
                    <div>
                      <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                        Prospective Alert & Action Guidance ({selectedHorizon.toUpperCase()})
                      </h2>
                      <span className="text-[10px] font-mono text-slate-400">
                        Synthesized municipal response recommendation
                      </span>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-[#0A1022] border border-[#1C2D54] space-y-2">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
                      COMPOSITE ALERT LEVEL
                    </span>
                    <div className="text-lg font-black font-mono text-cyan-300">
                      {activeAssessment.overall_alert_level}
                    </div>
                    <p className="text-xs text-slate-200 leading-relaxed font-sans pt-1">
                      {activeAssessment.operational_action_guidance}
                    </p>
                  </div>

                  {/* Human Verification Warning */}
                  <div className="p-3 bg-amber-950/30 border border-amber-500/40 rounded-lg text-xs font-mono text-amber-200/90 space-y-1">
                    <div className="flex items-center gap-1.5 text-amber-300 font-bold">
                      <Shield className="w-4 h-4 text-amber-400" />
                      <span>Mandatory Verification Notice</span>
                    </div>
                    <p className="text-[11px] leading-relaxed">
                      Prospective risk scores represent automated decision intelligence. All siren activations,
                      road closures, and mandatory evacuation orders require human-in-the-loop authorization by the
                      Municipal Disaster Management Authority.
                    </p>
                  </div>

                  {/* Forecast Metadata */}
                  <div className="p-3 bg-[#111A35] border border-[#233A6D] rounded-lg text-[11px] font-mono text-slate-300 space-y-1.5">
                    <span className="text-cyan-300 font-bold block mb-1">Forecast Feed Provenance:</span>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Provider:</span>
                      <span>Open-Meteo High-Resolution NWP</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Valid Window:</span>
                      <span>{activeAssessment.valid_from_utc.slice(11, 16)} to {activeAssessment.valid_to_utc.slice(11, 16)} UTC</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Precip Probability:</span>
                      <span className="text-cyan-400 font-bold">{activeAssessment.mean_precipitation_probability_pct}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Antecedent 3d Rain:</span>
                      <span>{activeAssessment.antecedent_3d_rain_mm} mm</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 48-Hour Forecast Timeline Strip */}
          {prospectiveForecast && (
            <div className="bg-[#0D152A] border border-[#1E325F]/70 rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-[#1E325F]/60 pb-3">
                <div className="flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-cyan-400" />
                  <h3 className="text-sm font-bold text-white">48-Hour Numerical Weather Prediction Hourly Forecast Timeline</h3>
                </div>
                <span className="text-xs font-mono text-slate-400">Continuous Hourly Intervals (Pune Pilot Basin)</span>
              </div>

              <div className="overflow-x-auto">
                <div className="flex gap-2 pb-2 min-w-[900px]">
                  {prospectiveForecast.forecast_points.slice(0, 24).map((pt, idx) => (
                    <div
                      key={idx}
                      className={`flex-1 p-2 rounded-lg border text-center font-mono text-[10px] min-w-[70px] ${pt.precipitation_mm >= 15.0
                          ? 'bg-red-950/40 border-red-500/50 text-red-200'
                          : pt.precipitation_mm > 0
                            ? 'bg-cyan-950/30 border-cyan-500/40 text-cyan-200'
                            : 'bg-[#0A1022] border-[#1C2D54] text-slate-400'
                        }`}
                    >
                      <span className="block font-bold text-slate-300">+{pt.lead_hours}h</span>
                      <span className="block text-[9px] text-slate-500">{pt.valid_time_iso.slice(11, 16)}</span>
                      <div className="my-1.5 font-black text-xs text-white">
                        {pt.precipitation_mm} <span className="text-[9px]">mm</span>
                      </div>
                      <span className="block text-[9px] text-cyan-400">{pt.precipitation_probability_pct}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: WHAT-IF EMERGENCY SCENARIO SIMULATOR                               */}
      {/* ========================================================================= */}
      {activeTab === 'scenario' && (
        <div className="space-y-6">
          <div className="bg-[#121B33] border-l-4 border-amber-400 border-y border-r border-[#24396B] rounded-r-xl p-4 text-xs space-y-2">
            <div className="flex items-center gap-2 text-amber-300 font-bold font-mono uppercase tracking-wide">
              <Sliders className="w-4 h-4 text-amber-400" />
              <span>What-If Scenario Analysis Explorer (Simulated Conditions)</span>
            </div>
            <p className="text-slate-300 font-sans leading-relaxed text-[11px]">
              Explore catchment response to combined meteorological cloudbursts and upstream Khadakwasla Dam spillway discharges.
              All outputs in this mode are strictly marked <strong className="text-amber-300 font-mono">SIMULATED_SCENARIO</strong> and must never be confused with live field telemetry.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left: Interactive Controls (6 cols) */}
            <div className="lg:col-span-6 bg-[#0D152A] border border-[#1E325F]/70 rounded-xl p-5 space-y-5">
              <div className="flex items-center justify-between border-b border-[#1E325F]/60 pb-3">
                <h3 className="text-sm font-bold text-white">Hydrometeorological Simulation Parameters</h3>
                <div className="flex gap-1.5 flex-wrap">
                  <span className="text-[11px] text-slate-400 mr-1 font-mono">Presets:</span>
                  <button
                    onClick={() => loadScenarioPreset('normal')}
                    className="px-2 py-0.5 rounded bg-[#14234B] text-[10px] font-mono text-slate-300 border border-[#27407D]"
                  >
                    Normal
                  </button>
                  <button
                    onClick={() => loadScenarioPreset('cloudburst')}
                    className="px-2 py-0.5 rounded bg-amber-950/60 text-[10px] font-mono text-amber-300 border border-amber-500/40"
                  >
                    Cloudburst
                  </button>
                  <button
                    onClick={() => loadScenarioPreset('spill')}
                    className="px-2 py-0.5 rounded bg-blue-950/60 text-[10px] font-mono text-blue-300 border border-blue-500/40"
                  >
                    15k Dam Spill
                  </button>
                  <button
                    onClick={() => loadScenarioPreset('compound')}
                    className="px-2 py-0.5 rounded bg-red-950/60 text-[10px] font-mono text-red-300 border border-red-500/40 font-bold"
                  >
                    July 2024 Compound
                  </button>
                </div>
              </div>

              {/* Sliders */}
              <div className="space-y-4 text-xs font-mono">
                <div>
                  <div className="flex justify-between text-slate-300 mb-1">
                    <span>Forecast Rainfall Multiplier:</span>
                    <span className="font-bold text-cyan-300">{scenarioRainMultiplier}x</span>
                  </div>
                  <input
                    type="range"
                    min="0.5"
                    max="4.0"
                    step="0.1"
                    value={scenarioRainMultiplier}
                    onChange={(e) => {
                      const v = parseFloat(e.target.value);
                      setScenarioRainMultiplier(v);
                      runScenario(v, scenarioPeak1h, scenarioDamDischarge, scenarioSoilMoisture, scenarioName);
                    }}
                    className="w-full accent-cyan-400 bg-slate-800"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-slate-300 mb-1">
                    <span>Forced Peak 1-Hour Rain Intensity:</span>
                    <span className="font-bold text-cyan-300">{scenarioPeak1h} mm/h</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="80"
                    step="5"
                    value={scenarioPeak1h}
                    onChange={(e) => {
                      const v = parseFloat(e.target.value);
                      setScenarioPeak1h(v);
                      runScenario(scenarioRainMultiplier, v, scenarioDamDischarge, scenarioSoilMoisture, scenarioName);
                    }}
                    className="w-full accent-cyan-400 bg-slate-800"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-slate-300 mb-1">
                    <span>Simulated Khadakwasla Dam Release:</span>
                    <span className="font-bold text-amber-300">{scenarioDamDischarge.toLocaleString()} cfs</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="60000"
                    step="2500"
                    value={scenarioDamDischarge}
                    onChange={(e) => {
                      const v = parseFloat(e.target.value);
                      setScenarioDamDischarge(v);
                      runScenario(scenarioRainMultiplier, scenarioPeak1h, v, scenarioSoilMoisture, scenarioName);
                    }}
                    className="w-full accent-amber-400 bg-slate-800"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                    <span>0 cfs</span>
                    <span className="text-amber-400">15k (Bhide Submergence)</span>
                    <span className="text-red-400">35.5k (July 2024 Peak)</span>
                    <span>60k cfs</span>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-slate-300 mb-1">
                    <span>Surface Soil Moisture (0-7cm):</span>
                    <span className="font-bold text-cyan-300">{scenarioSoilMoisture} m³/m³</span>
                  </div>
                  <input
                    type="range"
                    min="0.15"
                    max="0.52"
                    step="0.02"
                    value={scenarioSoilMoisture}
                    onChange={(e) => {
                      const v = parseFloat(e.target.value);
                      setScenarioSoilMoisture(v);
                      runScenario(scenarioRainMultiplier, scenarioPeak1h, scenarioDamDischarge, v, scenarioName);
                    }}
                    className="w-full accent-cyan-400 bg-slate-800"
                  />
                </div>
              </div>
            </div>

            {/* Right: Simulation Assessment Output (6 cols) */}
            <div className="lg:col-span-6 bg-[#0D152A] border border-[#1E325F]/70 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#1E325F]/60 pb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-ping" />
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                    Simulated Catchment Impact ({scenarioResult?.scenario_name})
                  </h3>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-500/40 font-bold">
                  SIMULATED_SCENARIO
                </span>
              </div>

              {scenarioResult && (
                <div className="space-y-4">
                  {/* Horizon 6h & 24h Scenario Comparison */}
                  <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                    <div className="p-3 rounded-lg bg-[#0A1022] border border-[#1C2D54]">
                      <span className="text-slate-400 block text-[10px]">6-Hour Forward Outlook:</span>
                      <strong className={`text-base font-bold block mt-0.5 ${scenarioResult.horizons['6h'].overall_alert_level.includes('EMERGENCY')
                          ? 'text-red-400'
                          : scenarioResult.horizons['6h'].overall_alert_level.includes('WARNING')
                            ? 'text-orange-400'
                            : 'text-amber-400'
                        }`}>
                        {scenarioResult.horizons['6h'].overall_alert_level}
                      </strong>
                      <span className="text-[11px] text-slate-300 mt-1 block">
                        Pluvial: {scenarioResult.horizons['6h'].pluvial_risk.risk_tier} | Riverine: {scenarioResult.horizons['6h'].riverine_risk.risk_tier}
                      </span>
                    </div>

                    <div className="p-3 rounded-lg bg-[#0A1022] border border-[#1C2D54]">
                      <span className="text-slate-400 block text-[10px]">24-Hour Forward Outlook:</span>
                      <strong className={`text-base font-bold block mt-0.5 ${scenarioResult.horizons['24h'].overall_alert_level.includes('EMERGENCY')
                          ? 'text-red-400'
                          : scenarioResult.horizons['24h'].overall_alert_level.includes('WARNING')
                            ? 'text-orange-400'
                            : 'text-amber-400'
                        }`}>
                        {scenarioResult.horizons['24h'].overall_alert_level}
                      </strong>
                      <span className="text-[11px] text-slate-300 mt-1 block">
                        Pluvial: {scenarioResult.horizons['24h'].pluvial_risk.risk_tier} | Riverine: {scenarioResult.horizons['24h'].riverine_risk.risk_tier}
                      </span>
                    </div>
                  </div>

                  {/* Physical Riverine Simulation Summary */}
                  <div className="p-4 rounded-xl bg-[#111A35] border border-[#233A6D] text-xs font-mono space-y-2">
                    <span className="text-amber-300 font-bold block">Physical Corridor Impact Assessment:</span>
                    <p className="text-slate-200 font-sans leading-relaxed">
                      {scenarioResult.horizons['24h'].riverine_risk.physical_reasoning}
                    </p>
                    <p className="text-slate-300 font-sans leading-relaxed pt-1">
                      {scenarioResult.horizons['24h'].pluvial_risk.physical_reasoning}
                    </p>
                  </div>

                  {/* Operational Disclaimer */}
                  <div className="p-3 bg-red-950/30 border border-red-500/30 rounded-lg text-[10px] font-mono text-red-300">
                    <strong>DISCLAIMER: </strong>{scenarioResult.operational_disclaimer}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: RETROSPECTIVE DIAGNOSTIC BENCHMARK (PHASE 2.2 / 2.2.1)             */}
      {/* ========================================================================= */}
      {activeTab === 'retrospective' && (
        <div className="space-y-6">
          {/* Prominent Scientific Audit & Limitations Banner */}
          <div className="bg-[#121B33] border-l-4 border-amber-400 border-y border-r border-[#24396B] rounded-r-xl p-4 text-xs space-y-2">
            <div className="flex items-center gap-2 text-amber-300 font-bold font-mono uppercase tracking-wide">
              <AlertCircle className="w-4 h-4 text-amber-400" />
              <span>Retrospective Model Scientific Audit Findings (Phase 2.2.1)</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-slate-300 font-mono text-[11px] pt-1">
              <div className="p-2.5 rounded bg-[#0A1022] border border-[#1C2D54]">
                <strong className="text-cyan-300 block mb-1">1. Retrospective Diagnostic:</strong>
                Evaluates completed 24h meteorological & soil conditions (00:00–23:59 UTC). This is a diagnostic classifier, NOT an operational early warning.
              </div>
              <div className="p-2.5 rounded bg-[#0A1022] border border-[#1C2D54]">
                <strong className="text-cyan-300 block mb-1">2. Single Held-Out Test Event:</strong>
                Held-out 2024 test partition contains exactly 1 flood event (July 24–26, 2024 Khadakwasla discharge, 3 days). 2023 had 0 positive events.
              </div>
              <div className="p-2.5 rounded bg-[#0A1022] border border-[#1C2D54]">
                <strong className="text-cyan-300 block mb-1">3. Decision Threshold Transparency:</strong>
                At default uncalibrated θ = 0.50, Random Forest achieves 100% test disaster recall (3/3 days). XGBoost produces 0% recall and required post-hoc tuning (θ = 0.25).
              </div>
              <div className="p-2.5 rounded bg-[#0A1022] border border-[#1C2D54]">
                <strong className="text-cyan-300 block mb-1">4. Non-Circular SFSI & DSM Bias:</strong>
                Terrain index uses pure geomorphology (River 40%, Slope 30%, Elev 30%). Copernicus 90m DSM tree canopy causes 2–8m upward bias in urban/riparian zones.
              </div>
            </div>
          </div>

          {/* Model Benchmark Comparison Table */}
          <div className="bg-[#0D152A] border border-[#1E325F]/70 rounded-xl p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#1E325F]/60 pb-3 gap-2">
              <div className="flex items-center gap-2">
                <Cpu className="w-5 h-5 text-cyan-400" />
                <div>
                  <h2 className="text-base font-bold text-white">Chronological Model Benchmark (2024 Held-Out Test Year)</h2>
                  <span className="text-[10px] font-mono text-slate-400">
                    Evaluating 1 independent historical event (July 24–26, 2024 Khadakwasla dam spill, 3 positive days)
                  </span>
                </div>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-[#162955] text-cyan-300 border border-[#2B4E9A]">
                Zero Data Leakage Validation
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs font-mono text-left text-slate-300">
                <thead className="bg-[#070D1E] text-slate-400 uppercase text-[10px] tracking-wider border-b border-[#1E325F]">
                  <tr>
                    <th className="py-2.5 px-3">Model Architecture</th>
                    <th className="py-2.5 px-3">Threshold (θ)</th>
                    <th className="py-2.5 px-3">July 2024 Event Detection</th>
                    <th className="py-2.5 px-3">Accuracy</th>
                    <th className="py-2.5 px-3">Precision</th>
                    <th className="py-2.5 px-3">Recall</th>
                    <th className="py-2.5 px-3">F1-Score</th>
                    <th className="py-2.5 px-3">ROC-AUC</th>
                    <th className="py-2.5 px-3">Confusion (TN/FP/FN/TP)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E325F]/50">
                  {evaluation?.models_evaluated.map((m, idx) => {
                    const isRf = m.model_name.includes('Random Forest');
                    const isXgbTuned = m.model_name.includes('Post-Hoc');
                    const isXgbDefault = m.model_name.includes('Default θ=0.50');
                    return (
                      <tr
                        key={idx}
                        className={
                          isRf
                            ? 'bg-emerald-950/20 font-semibold text-white'
                            : isXgbTuned
                              ? 'bg-amber-950/20 text-slate-200'
                              : isXgbDefault
                                ? 'bg-cyan-950/20 text-slate-300'
                                : 'hover:bg-[#121F3D]/50'
                        }
                      >
                        <td className="py-2.5 px-3 flex items-center gap-2">
                          {isRf && <span className="w-2 h-2 rounded-full bg-emerald-400" />}
                          {isXgbDefault && <span className="w-2 h-2 rounded-full bg-cyan-400" />}
                          {isXgbTuned && <span className="w-2 h-2 rounded-full bg-amber-400" />}
                          {m.model_name}
                        </td>
                        <td className="py-2.5 px-3">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${m.threshold_type.includes('test_tuned')
                              ? 'bg-amber-900/60 text-amber-300 border border-amber-500/40'
                              : 'bg-slate-800 text-slate-300'
                            }`}>
                            θ = {m.decision_threshold.toFixed(2)}
                          </span>
                        </td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${m.recall === 1.0
                              ? 'bg-emerald-900/50 text-emerald-300 border border-emerald-500/40'
                              : m.recall > 0
                                ? 'bg-amber-900/50 text-amber-300 border border-amber-500/40'
                                : 'bg-red-900/50 text-red-300 border border-red-500/40'
                            }`}>
                            {m.test_events_detected || (m.recall === 1.0 ? '1/1 event (3/3 days)' : '0/1 event (0/3 days)')}
                          </span>
                        </td>
                        <td className="py-2.5 px-3">{(m.accuracy * 100).toFixed(2)}%</td>
                        <td className="py-2.5 px-3">{m.precision.toFixed(3)}</td>
                        <td className="py-2.5 px-3 font-bold text-white">{m.recall.toFixed(3)}</td>
                        <td className="py-2.5 px-3">{m.f1_score.toFixed(3)}</td>
                        <td className="py-2.5 px-3 text-cyan-400">{m.roc_auc ? m.roc_auc.toFixed(4) : 'N/A'}</td>
                        <td className="py-2.5 px-3 text-slate-400">
                          {m.confusion_matrix.true_negatives} / {m.confusion_matrix.false_positives} / {m.confusion_matrix.false_negatives} / {m.confusion_matrix.true_positives}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Audit Callout Box */}
            {evaluation?.threshold_audit_note && (
              <div className="p-3 bg-[#111A35] border border-amber-500/30 rounded-lg text-[11px] text-amber-200/90 font-mono leading-relaxed">
                <strong className="text-amber-300 block mb-0.5">Threshold Audit Finding:</strong>
                {evaluation.threshold_audit_note}
              </div>
            )}
          </div>

          {/* Geospatial Susceptibility Hotspot Registry (SFSI) */}
          <div className="bg-[#0D152A] border border-[#1E325F]/70 rounded-xl p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#1E325F]/60 pb-3 gap-2">
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-cyan-400" />
                <div>
                  <h2 className="text-base font-bold text-white">Pune Basin Spatial Flood Susceptibility Index (SFSI) Hotspots</h2>
                  <span className="text-[10px] font-mono text-slate-400">
                    Non-Circular Multi-Criteria Physical Geomorphic Index (River 40%, Slope 30%, Rel Elev 30%)
                  </span>
                </div>
              </div>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-900/40 text-emerald-300 border border-emerald-500/30">
                Independent Benchmark Evaluation
              </span>
            </div>

            {susceptibility?.surface_canopy_bias_note && (
              <div className="p-3 bg-[#0A1022] border border-[#1D305C] rounded-lg text-[11px] font-mono text-slate-300">
                <strong className="text-cyan-300 block mb-0.5">Copernicus GLO-90 DSM Surface Canopy Disclosure:</strong>
                {susceptibility.surface_canopy_bias_note}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {susceptibility?.chronic_hotspots.map((spot, idx) => (
                <div key={idx} className="bg-[#111A35] border border-[#233A6D] rounded-xl p-4 space-y-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5 text-cyan-400" />
                        {spot.name}
                      </h3>
                      <span className="text-[10px] font-mono text-slate-400">
                        {spot.latitude.toFixed(4)}°N, {spot.longitude.toFixed(4)}°E
                      </span>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-950 text-red-300 border border-red-500/40 font-bold">
                      SFSI: {spot.sfsi_score.toFixed(2)}
                    </span>
                  </div>

                  <div className="text-xs text-slate-300 font-sans leading-relaxed">
                    {spot.description}
                  </div>

                  <div className="pt-2 border-t border-slate-700/60 flex items-center justify-between text-[11px] font-mono">
                    <span className="text-slate-400">Verified Depth:</span>
                    <span className="text-amber-300 font-semibold">{spot.verified_inundation_depth_m}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
