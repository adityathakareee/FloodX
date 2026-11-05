import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  AlertCircle,
  RefreshCw,
  Activity,
  AlertTriangle,
  Users,
  Navigation,
  Sliders,
  Shield,
  ArrowRight,
  Waves,
  MapPin,
  Building2,
  Radio,
  FileCheck2,
  Clock,
  PhoneCall,
} from 'lucide-react';
import { HealthCard } from '../components/dashboard/HealthCard';
import { BasinLeafletMap } from '../components/map/BasinLeafletMap';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { useSystemHealth } from '../hooks/useSystemHealth';

export const OverviewPage: React.FC = () => {
  const { health, isLoading: healthLoading, isOnline, refresh: refreshHealth } = useSystemHealth(10000);

  if (healthLoading && !health) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner size="lg" label="Connecting to FLOOD-X Intelligence Engine..." />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12 font-sans select-none">
      {/* 1. Platform Hero Banner — Modern Light Gradient */}
      <div className="bg-gradient-to-r from-blue-700 via-indigo-700 to-sky-700 text-white rounded-2xl p-6 md:p-8 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-80 h-80 bg-white/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/15 border border-white/20 text-white text-xs font-mono font-semibold tracking-wide uppercase mb-3 backdrop-blur-sm">
              <ShieldCheck className="w-3.5 h-3.5 text-sky-200" />
              <span>Real-Time Flood Intelligence & Decision Support</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              FLOOD-X Intelligence Platform
            </h1>
            <p className="text-sky-200 font-mono text-xs md:text-sm tracking-wide font-semibold mt-1">
              PREDICT &nbsp;|&nbsp; PRIORITIZE &nbsp;|&nbsp; PROTECT
            </p>
            <p className="text-blue-100 text-xs md:text-sm mt-2 max-w-3xl leading-relaxed">
              AI-powered flood intelligence and emergency response decision-support platform for the{' '}
              <span className="text-white font-bold underline decoration-sky-300">
                Pune / Mula-Mutha River Basin
              </span>
              . Connecting real-time environmental telemetry, machine learning risk forecasting, dynamic evacuation routing, and resource optimization for municipal authorities and emergency response forces.
            </p>
          </div>

          <div className="shrink-0 flex flex-col sm:flex-row lg:flex-col gap-2.5 font-mono text-xs">
            <div className="bg-black/20 backdrop-blur-md border border-white/15 rounded-xl px-4 py-2.5 text-white">
              <span className="text-sky-200 block text-[10px] uppercase tracking-wider font-semibold">
                Controlling Basin
              </span>
              <span className="text-white font-bold">Mula-Mutha Catchment</span>
            </div>
            <div className="bg-black/20 backdrop-blur-md border border-white/15 rounded-xl px-4 py-2.5 text-white">
              <span className="text-sky-200 block text-[10px] uppercase tracking-wider font-semibold">
                Operational Status
              </span>
              <span className="text-emerald-300 font-bold flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                Active Monitoring
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Connection Notice if Backend is Offline */}
      {!isOnline && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 flex items-center justify-between text-rose-800 text-xs">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <div>
              <span className="font-bold block">Backend Service Offline</span>
              <span className="text-rose-600">
                FastAPI backend is currently offline. Ensure uvicorn is running on port 8000.
              </span>
            </div>
          </div>
          <button
            onClick={() => refreshHealth()}
            className="px-3 py-1.5 rounded-lg bg-rose-100 hover:bg-rose-200 border border-rose-300 text-rose-800 font-semibold flex items-center gap-1.5 shrink-0 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Retry Connection
          </button>
        </div>
      )}

      {/* 2. Core Health Indicators */}
      <HealthCard health={health} isOnline={isOnline} isLoading={healthLoading} />

      {/* 3. Real Interactive Leaflet Spatial Map */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">
              Mula-Mutha Catchment Spatial Intelligence
            </h2>
            <p className="text-xs text-slate-500">
              Interactive Leaflet GIS map with July 2024 flood footprint, critical river crossings & high-ground shelters.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
              <Radio className="w-3.5 h-3.5 text-blue-600 animate-pulse" />
              Live Interactive Map
            </span>
          </div>
        </div>

        <BasinLeafletMap />
      </div>

      {/* 4. Active Command Subsystems Grid */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">
              Command Subsystems & Decision Modules
            </h2>
            <p className="text-xs text-slate-500">
              Direct access to all 6 operational flood intelligence engines.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Module 1: Data & Telemetry */}
          <Link
            to="/monitoring"
            className="group bg-white hover:bg-slate-50/80 border border-slate-200/90 hover:border-blue-300 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 group-hover:scale-105 transition-transform">
                  <Activity className="w-5 h-5" />
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                  LIVE TELEMETRY
                </span>
              </div>
              <h3 className="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
                Environmental Telemetry
              </h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                IMD rainfall, NWIC river stages, Copernicus DEM & Vertisol soil saturation index across 25 peak dates.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-blue-600">
              <span>View Data Cockpit</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          {/* Module 2: Flood Risk Prediction */}
          <Link
            to="/risk"
            className="group bg-white hover:bg-slate-50/80 border border-slate-200/90 hover:border-amber-300 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 group-hover:scale-105 transition-transform">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-bold">
                  48H FORECAST
                </span>
              </div>
              <h3 className="text-sm font-bold text-slate-900 group-hover:text-amber-600 transition-colors">
                Flood Risk Prediction
              </h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Multi-horizon prospective rainfall forecasting (6h–48h), convective intensity watches & ML susceptibility models.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-amber-600">
              <span>View Risk Forecast</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          {/* Module 3: Flood Impact & Inundation */}
          <Link
            to="/impact"
            className="group bg-white hover:bg-slate-50/80 border border-slate-200/90 hover:border-sky-300 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600 group-hover:scale-105 transition-transform">
                  <Users className="w-5 h-5" />
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200 font-bold">
                  GIS OVERLAY
                </span>
              </div>
              <h3 className="text-sm font-bold text-slate-900 group-hover:text-sky-600 transition-colors">
                Inundation & Impact
              </h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Spatial overlay with July 2024 flood footprint, 185 healthcare units, 30 schools & bridge submersion ratings.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-sky-600">
              <span>Inspect Impact Overlay</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          {/* Module 4: Evacuation & Routing */}
          <Link
            to="/evacuation"
            className="group bg-white hover:bg-slate-50/80 border border-slate-200/90 hover:border-emerald-300 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 group-hover:scale-105 transition-transform">
                  <Navigation className="w-5 h-5" />
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                  906 ROAD EDGES
                </span>
              </div>
              <h3 className="text-sm font-bold text-slate-900 group-hover:text-emerald-600 transition-colors">
                Evacuation & Safe Routing
              </h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                MultiDiGraph network pathfinding dynamically routing around closed causeways and inundated riverbanks.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-emerald-600">
              <span>Plan Evacuation Routes</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          {/* Module 5: Dam Scenario Simulation */}
          <Link
            to="/scenarios"
            className="group bg-white hover:bg-slate-50/80 border border-slate-200/90 hover:border-indigo-300 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600 group-hover:scale-105 transition-transform">
                  <Sliders className="w-5 h-5" />
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 font-bold">
                  WHAT-IF ENGINE
                </span>
              </div>
              <h3 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                Dam Release Simulation
              </h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Controlled Khadakwasla spillway simulation (5,000 to 55,000 cfs) previewing downstream bridge inundation hours ahead.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-indigo-600">
              <span>Simulate Dam Releases</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          {/* Module 6: Resource Optimization */}
          <Link
            to="/command-center"
            className="group bg-white hover:bg-slate-50/80 border border-slate-200/90 hover:border-purple-300 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-purple-50 border border-purple-200 flex items-center justify-center text-purple-600 group-hover:scale-105 transition-transform">
                  <Shield className="w-5 h-5" />
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200 font-bold">
                  OR-TOOLS MIP
                </span>
              </div>
              <h3 className="text-sm font-bold text-slate-900 group-hover:text-purple-600 transition-colors">
                Resource Optimization Cockpit
              </h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Google OR-Tools constrained dispatch for rescue boats, ambulances & dewatering pumps with tactical NDMA SOP guidance.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-purple-600">
              <span>Launch Command Cockpit</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>
        </div>
      </div>

      {/* 5. Key Hydraulic Benchmarks & Emergency Contacts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 pt-2">
        {/* Benchmarks Quick Reference */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs lg:col-span-2">
          <div className="flex items-center gap-2 mb-3">
            <Waves className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-bold text-slate-900">
              Khadakwasla Spillway Threshold Reference
            </h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
              <span className="text-slate-400 block text-[10px] font-mono font-bold uppercase">
                Normal Flow
              </span>
              <span className="text-base font-black text-slate-800 font-mono">&lt; 5,000 cfs</span>
              <p className="text-[11px] text-slate-500 mt-1">Water safely confined within low-flow channel.</p>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3">
              <span className="text-amber-700 block text-[10px] font-mono font-bold uppercase">
                Bhide Watch
              </span>
              <span className="text-base font-black text-amber-900 font-mono">15,000 cfs</span>
              <p className="text-[11px] text-amber-700 mt-1">Baba Bhide low causeway precautionary closure.</p>
            </div>

            <div className="bg-rose-50 border border-rose-200 rounded-xl p-3">
              <span className="text-rose-700 block text-[10px] font-mono font-bold uppercase">
                July 2024 Disaster
              </span>
              <span className="text-base font-black text-rose-900 font-mono">35,574 cfs</span>
              <p className="text-[11px] text-rose-700 mt-1">Observed peak spill: 1.5–2.5m inundation along Sinhagad Rd.</p>
            </div>

            <div className="bg-purple-50 border border-purple-200 rounded-xl p-3">
              <span className="text-purple-700 block text-[10px] font-mono font-bold uppercase">
                Extreme Drill
              </span>
              <span className="text-base font-black text-purple-900 font-mono">50,000+ cfs</span>
              <p className="text-[11px] text-purple-700 mt-1">Level-4 catchment disaster drill scenario.</p>
            </div>
          </div>
        </div>

        {/* Emergency Contacts */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <PhoneCall className="w-4 h-4 text-emerald-600" />
              <h3 className="text-sm font-bold text-slate-900">Emergency Hotlines</h3>
            </div>
            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between items-center py-1.5 border-b border-slate-100">
                <span className="text-slate-600">PMC Disaster Cell:</span>
                <span className="font-mono font-bold text-slate-900">020-25501269</span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-slate-100">
                <span className="text-slate-600">PMC Flood Control:</span>
                <span className="font-mono font-bold text-slate-900">020-25506800</span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-slate-100">
                <span className="text-slate-600">National Emergency:</span>
                <span className="font-mono font-bold text-blue-600">112</span>
              </div>
              <div className="flex justify-between items-center py-1.5">
                <span className="text-slate-600">District Collectorate:</span>
                <span className="font-mono font-bold text-slate-900">1077</span>
              </div>
            </div>
          </div>
          <div className="mt-3 pt-2 text-[10px] text-slate-400 font-mono text-center">
            Statutory Directives by PMC & District Disaster Cell
          </div>
        </div>
      </div>
    </div>
  );
};
