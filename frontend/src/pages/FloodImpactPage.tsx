import React, { useEffect, useState } from 'react';
import {
  Users,
  AlertTriangle,
  Building2,
  Navigation,
  ShieldAlert,
  Satellite,
  Layers,
  History,
  Info,
  CheckCircle2,
  Clock,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { apiService } from '../services/api';
import {
  ImpactAssessmentResponse,
  ImpactScenariosResponse,
  ExposedFacility,
  ExposedBridge,
} from '../types/api';

export const FloodImpactPage: React.FC = () => {
  const [assessment, setAssessment] = useState<ImpactAssessmentResponse | null>(null);
  const [scenarios, setScenarios] = useState<ImpactScenariosResponse | null>(null);
  const [hazardSource, setHazardSource] = useState<'OBSERVED_SAR_EXTENT' | 'SIMULATED_SCENARIO'>('OBSERVED_SAR_EXTENT');
  const [simulatedDischarge, setSimulatedDischarge] = useState<number>(35574);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'hospitals' | 'bridges' | 'historical'>('hospitals');

  const fetchAssessment = async (source: string, discharge?: number) => {
    setLoading(true);
    setError(null);
    try {
      if (source === 'SIMULATED_SCENARIO') {
        const res = await apiService.assessImpactScenario({
          hazard_source: 'SIMULATED_SCENARIO',
          simulated_discharge_cfs: discharge || simulatedDischarge,
          scenario_name: `Khadakwasla Dam Release (${discharge || simulatedDischarge} cfs)`,
        });
        setAssessment(res);
      } else {
        const res = await apiService.getImpactLatest('OBSERVED_SAR_EXTENT');
        setAssessment(res);
      }
      const scn = await apiService.getImpactScenarios();
      setScenarios(scn);
    } catch (err: any) {
      console.error('Failed to load impact assessment:', err);
      setError(err?.message || 'Failed to communicate with Flood Impact Assessment engine');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssessment(hazardSource, simulatedDischarge);
  }, []);

  const handleSourceChange = (newSource: 'OBSERVED_SAR_EXTENT' | 'SIMULATED_SCENARIO') => {
    setHazardSource(newSource);
    fetchAssessment(newSource, simulatedDischarge);
  };

  const handleDischargeChange = (val: number) => {
    setSimulatedDischarge(val);
    if (hazardSource === 'SIMULATED_SCENARIO') {
      fetchAssessment('SIMULATED_SCENARIO', val);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
              <Users className="w-6 h-6 text-cyan-400" />
              Flood Impact & Multi-Sector Vulnerability
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
              PHASE 5 INTELLIGENCE
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Spatial overlay of Sentinel-1 C-band SAR satellite observations, hydraulic river routing, and PostGIS municipal assets across Pune.
          </p>
        </div>

        {/* Hazard Mode Selector */}
        <div className="flex items-center gap-2 bg-slate-900/80 p-1.5 rounded-xl border border-slate-800">
          <button
            onClick={() => handleSourceChange('OBSERVED_SAR_EXTENT')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${hazardSource === 'OBSERVED_SAR_EXTENT'
              ? 'bg-cyan-500 text-slate-950 shadow-md font-bold'
              : 'text-slate-400 hover:text-slate-200'
              }`}
          >
            <Satellite className="w-3.5 h-3.5" />
            Illustrative July 2024 Extent (PMC Report Analog - Unverified SAR)
          </button>
          <button
            onClick={() => handleSourceChange('SIMULATED_SCENARIO')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${hazardSource === 'SIMULATED_SCENARIO'
              ? 'bg-blue-600 text-white shadow-md font-bold'
              : 'text-slate-400 hover:text-slate-200'
              }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Hydraulic Dam Simulation
          </button>
          <button
            onClick={() => fetchAssessment(hazardSource, simulatedDischarge)}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
            title="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Dam Release Slider if in Simulation Mode */}
      {hazardSource === 'SIMULATED_SCENARIO' && (
        <div className="bg-slate-900/90 border border-blue-500/30 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-300 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
              Simulated Khadakwasla Dam Spillway Discharge
            </span>
            <span className="font-mono font-bold text-blue-400 text-sm">
              {simulatedDischarge.toLocaleString()} cfs
            </span>
          </div>
          <input
            type="range"
            min={5000}
            max={55000}
            step={2500}
            value={simulatedDischarge}
            onChange={(e) => handleDischargeChange(Number(e.target.value))}
            className="w-full accent-blue-500 h-2 bg-slate-800 rounded-lg cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-slate-400 font-mono">
            <span>5,000 cfs (Normal Flow)</span>
            <span>15,000 cfs (Baba Bhide Causeway Submerges)</span>
            <span>35,500 cfs (July 2024 Disaster)</span>
            <span>45,400 cfs (Aug 2019 Mega Flood)</span>
          </div>
        </div>
      )}

      {/* Mandatory Scientific Boundary & Provenance Disclosure Banner */}
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3.5 flex items-start gap-3">
        <Info className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-xs text-amber-200/90 leading-relaxed space-y-1">
          <div>
            <strong className="text-amber-300 font-semibold">Provenance Disclosure:</strong> The July 2024 flood footprint shown is an illustrative spatial polygon digitized from municipal flood reports (analog), NOT directly processed from raw Sentinel-1 Level-1 GRD SAR raster backscatter. No raw SAR raster data exists in the repository.
          </div>
          <div>
            <span className="text-amber-100 font-medium">Depth Limitation:</span> Radar backscatter detects surface specular reflection only; it CANNOT measure flood depth. Never infer flood depth from satellite SAR alone.
          </div>
          <div>
            <span className="text-amber-100 font-medium">Demographic Limitation:</span> Numerical population exposure is withheld (DATA INSUFFICIENT). The repository does not contain official Census of India 2011 ward polygons or gridded population rasters (WorldPop/LandScan). Hardcoded density multipliers have been removed to maintain scientific integrity.
          </div>
          <div>
            <span className="text-amber-100 font-medium">Hydraulic Thresholds:</span> Bridge submersion figures (e.g. Baba Bhide ~15,000 cfs, SM Joshi ~48,000 cfs) are operational scenario references based on informal traffic barricading or hydraulic simulation, NOT statutory WRD/PMC engineering rating curves.
          </div>
          <div>
            <span className="text-amber-100 font-medium">Infrastructure Exposure:</span> Road and facility counts represent proximity-based spatial hazard buffer evaluations, not field-verified road washouts or structural closures.
          </div>
        </div>
      </div>

      {/* Impact Summary Ribbon */}
      {assessment && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Population Exposed */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Population Exposure</span>
              <Users className="w-4 h-4 text-purple-400" />
            </div>
            {assessment.population_exposure.estimated_exposed_population !== null && assessment.population_exposure.estimated_exposed_population !== undefined ? (
              <>
                <div className="my-2">
                  <span className="text-2xl font-black text-white font-mono">
                    {assessment.population_exposure.estimated_exposed_population.toLocaleString()}
                  </span>
                  <span className="text-xs text-purple-300 ml-1 font-mono">citizens</span>
                </div>
                <div className="text-[11px] text-slate-400 font-mono mb-2">
                  Confidence: {assessment.population_exposure.lower_bound_estimate?.toLocaleString() ?? 'N/A'} – {assessment.population_exposure.upper_bound_estimate?.toLocaleString() ?? 'N/A'}
                </div>
              </>
            ) : (
              <div className="my-3 space-y-1.5">
                <div className="text-xs font-bold text-amber-400 font-mono flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                  POPULATION EXPOSURE: DATA INSUFFICIENT
                </div>
                <p className="text-[11px] text-slate-400 leading-snug">
                  Census 2011 ward polygons & gridded population rasters (WorldPop) not ingested. Numerical values withheld.
                </p>
              </div>
            )}
            <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono font-semibold border border-amber-500/40 text-center">
              STATUS: {assessment.population_exposure.data_status}
            </span>
          </div>

          {/* Road Network Disrupted */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Road Segments Evaluated</span>
              <Navigation className="w-4 h-4 text-rose-400" />
            </div>
            <div className="my-2">
              <span className="text-2xl font-black text-white font-mono">
                {assessment.road_network_impact.inundated_road_km.toFixed(1)}
              </span>
              <span className="text-xs text-rose-300 ml-1 font-mono">km ({assessment.road_network_impact.inundated_percentage}%)</span>
            </div>
            <div className="text-[11px] text-slate-400">
              {assessment.road_network_impact.closed_or_blocked_segments_count} segments proximity-exposed
            </div>
            <div className="text-[9px] text-amber-300/80 font-mono mt-0.5">
              (Proximity spatial model; not confirmed closures)
            </div>
          </div>

          {/* Healthcare Facilities at Risk */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Healthcare Units Exposed</span>
              <Building2 className="w-4 h-4 text-amber-400" />
            </div>
            <div className="my-2">
              <span className="text-2xl font-black text-white font-mono">
                {assessment.healthcare_impact.length}
              </span>
              <span className="text-xs text-amber-300 ml-1 font-mono">
                ({assessment.healthcare_impact.filter(h => h.exposure_tier === 'CRITICAL').length} Critical)
              </span>
            </div>
            <div className="text-[11px] text-slate-400">
              Buffer proximity evaluation
            </div>
          </div>

          {/* Submerged Bridges */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>River Bridges Submerged</span>
              <ShieldAlert className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="my-2">
              <span className="text-2xl font-black text-white font-mono">
                {assessment.bridges_impact.filter(b => b.submerged).length}
              </span>
              <span className="text-xs text-cyan-300 ml-1 font-mono">
                / {assessment.bridges_impact.length} Crossings
              </span>
            </div>
            <div className="text-[11px] text-slate-400">
              Severity: <span className="font-bold text-rose-400">{assessment.overall_severity}</span>
            </div>
          </div>
        </div>
      )}

      {/* Tabs Selector */}
      <div className="flex border-b border-slate-800 space-x-6 text-sm font-semibold">
        <button
          onClick={() => setActiveTab('hospitals')}
          className={`pb-3 flex items-center gap-2 transition-all ${activeTab === 'hospitals'
            ? 'border-b-2 border-cyan-400 text-cyan-300 font-bold'
            : 'text-slate-400 hover:text-slate-200'
            }`}
        >
          <Building2 className="w-4 h-4" />
          Exposed Healthcare & Schools ({assessment ? assessment.healthcare_impact.length + assessment.education_impact.length : 0})
        </button>
        <button
          onClick={() => setActiveTab('bridges')}
          className={`pb-3 flex items-center gap-2 transition-all ${activeTab === 'bridges'
            ? 'border-b-2 border-cyan-400 text-cyan-300 font-bold'
            : 'text-slate-400 hover:text-slate-200'
            }`}
        >
          <ShieldAlert className="w-4 h-4" />
          Critical River Bridges ({assessment ? assessment.bridges_impact.length : 0})
        </button>
        <button
          onClick={() => setActiveTab('historical')}
          className={`pb-3 flex items-center gap-2 transition-all ${activeTab === 'historical'
            ? 'border-b-2 border-cyan-400 text-cyan-300 font-bold'
            : 'text-slate-400 hover:text-slate-200'
            }`}
        >
          <History className="w-4 h-4" />
          Historical Disaster Scenarios
        </button>
      </div>

      {/* Tab 1: Healthcare & Schools Table */}
      {activeTab === 'hospitals' && assessment && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex justify-between items-center">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Building2 className="w-4 h-4 text-cyan-400" />
              Infrastructure Assets Exposed to Flood Extent
            </h3>
            <span className="text-xs text-slate-400 font-mono">
              Source: PostGIS OSM Pune Vector Layer
            </span>
          </div>
          <div className="overflow-x-auto max-h-[420px] overflow-y-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 sticky top-0 border-b border-slate-800 font-mono">
                <tr>
                  <th className="py-2.5 px-4">Facility Name</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Distance to Hazard</th>
                  <th className="py-2.5 px-3">Exposure Tier</th>
                  <th className="py-2.5 px-3">Access Status</th>
                  <th className="py-2.5 px-4">Operational Impact</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {assessment.healthcare_impact.map((f, i) => (
                  <tr key={`h-${i}`} className="hover:bg-slate-800/40">
                    <td className="py-2.5 px-4 font-semibold text-white">{f.name}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20 font-mono text-[10px]">
                        HEALTHCARE
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono font-bold text-cyan-400">
                      {f.distance_to_hazard_m.toFixed(1)} m
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`px-2 py-0.5 rounded font-mono font-bold text-[10px] ${f.exposure_tier === 'CRITICAL'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : f.exposure_tier === 'HIGH'
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            : 'bg-slate-700/50 text-slate-300'
                          }`}
                      >
                        {f.exposure_tier}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      {f.access_threatened ? (
                        <span className="text-rose-400 font-semibold flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3" /> THREATENED
                        </span>
                      ) : (
                        <span className="text-emerald-400 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" /> CLEAR
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-slate-400 text-[11px]">{f.operational_impact}</td>
                  </tr>
                ))}
                {assessment.education_impact.map((e, i) => (
                  <tr key={`e-${i}`} className="hover:bg-slate-800/40 bg-slate-900/40">
                    <td className="py-2.5 px-4 font-semibold text-white">{e.name}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20 font-mono text-[10px]">
                        EDUCATION
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-cyan-400">
                      {e.distance_to_hazard_m.toFixed(1)} m
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-amber-500/20 text-amber-300">
                        {e.exposure_tier}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="text-amber-400 text-[10px] font-mono">BUFFER OVERLAP</span>
                    </td>
                    <td className="py-2.5 px-4 text-slate-400 text-[11px]">{e.operational_impact}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Critical River Bridges Table */}
      {activeTab === 'bridges' && assessment && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex justify-between items-center">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-cyan-400" />
              Mula-Mutha River Crossings & Hydraulic Submersion Thresholds
            </h3>
            <span className="text-xs text-slate-400 font-mono">
              Operational Threshold References & Scenarios
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-mono">
                <tr>
                  <th className="py-2.5 px-4">Bridge Name</th>
                  <th className="py-2.5 px-3">Waterway</th>
                  <th className="py-2.5 px-3">Submersion Threshold</th>
                  <th className="py-2.5 px-3">Classification</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-4">Operational Directive</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {assessment.bridges_impact.map((b, i) => (
                  <tr key={`b-${i}`} className="hover:bg-slate-800/40">
                    <td className="py-3 px-4 font-bold text-white">{b.name}</td>
                    <td className="py-3 px-3 font-mono text-cyan-300">{b.waterway}</td>
                    <td className="py-3 px-3 font-mono text-slate-200">
                      {b.critical_threshold_cfs.toLocaleString()} cfs
                    </td>
                    <td className="py-3 px-3">
                      {b.threshold_classification === 'UNVERIFIED_OPERATIONAL_REFERENCE' ? (
                        <span className="px-2 py-0.5 rounded font-mono font-bold text-[9px] bg-amber-500/20 text-amber-300 border border-amber-500/30">
                          UNVERIFIED OP REF
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded font-mono font-medium text-[9px] bg-cyan-500/10 text-cyan-300/80 border border-cyan-500/20">
                          ILLUSTRATIVE SCENARIO
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      {b.submerged ? (
                        <span className="px-2.5 py-1 rounded-full font-mono font-black text-[10px] bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
                          SUBMERGED
                        </span>
                      ) : b.inundation_risk === 'HIGH_RISK' ? (
                        <span className="px-2.5 py-1 rounded-full font-mono font-bold text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/40">
                          HIGH RISK
                        </span>
                      ) : (
                        <span className="px-2.5 py-1 rounded-full font-mono font-bold text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                          PASSABLE
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[11px]">{b.operational_status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Historical Scenarios Table */}
      {activeTab === 'historical' && scenarios && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {scenarios.historical_scenarios.map((scn, idx) => (
              <div
                key={scn.scenario_id}
                className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 flex flex-col justify-between hover:border-slate-700 transition-all"
              >
                <div>
                  <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-2">
                    <span className="text-cyan-400 font-bold">{scn.event_date}</span>
                    <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 font-bold">
                      {scn.severity_level}
                    </span>
                  </div>
                  <h4 className="text-base font-bold text-white mb-2">{scn.scenario_name}</h4>
                  <p className="text-xs text-slate-400 leading-relaxed mb-4">{scn.description}</p>
                </div>
                <div className="border-t border-slate-800 pt-3 space-y-1.5 text-xs font-mono">
                  <div className="flex justify-between text-slate-300">
                    <span className="text-slate-400">Dam Discharge:</span>
                    <span className="font-bold text-white">{scn.khadakwasla_discharge_cfs.toLocaleString()} cfs</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span className="text-slate-400">Exposed Population:</span>
                    <span className="font-bold text-purple-400">{scn.estimated_exposed_population.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span className="text-slate-400">Inundated Roads:</span>
                    <span className="font-bold text-rose-400">{scn.inundated_road_km.toFixed(1)} km</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span className="text-slate-400">Submerged Bridges:</span>
                    <span className="font-bold text-cyan-400">{scn.affected_bridges_count}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Operational Directives & NDMA SOP Checklist */}
      {assessment && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-3">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            Authority Action Directives (NDMA 2008 / PMC DMP SOP Protocols)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {assessment.key_recommendations.map((rec, i) => (
              <div key={i} className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 flex items-center justify-center text-[10px] font-bold font-mono shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">{rec}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
