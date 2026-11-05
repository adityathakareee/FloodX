import React, { useState } from 'react';
import { Layers, CheckCircle2, Clock, HelpCircle } from 'lucide-react';
import { Card } from '../common/Card';
import { StatusPill } from '../common/StatusPill';
import { ModuleReadiness } from '../../types/api';

interface ModuleReadinessCardProps {
  modules: ModuleReadiness[];
  currentPhase: string;
}

export const ModuleReadinessCard: React.FC<ModuleReadinessCardProps> = ({
  modules,
  currentPhase,
}) => {
  const [selectedPhaseFilter, setSelectedPhaseFilter] = useState<number | 'all'>('all');

  const filteredModules = selectedPhaseFilter === 'all'
    ? modules
    : modules.filter((m) => m.target_phase === selectedPhaseFilter);

  const phaseButtons: Array<{ label: string; value: number | 'all' }> = [
    { label: 'All Modules', value: 'all' },
    { label: 'Phase 0 (Foundation)', value: 0 },
    { label: 'Phase 1 (Data & GIS)', value: 1 },
    { label: 'Phase 2 (AI/ML)', value: 2 },
    { label: 'Phase 3 (Routing)', value: 3 },
    { label: 'Phase 4 (Resources/AI)', value: 4 },
  ];

  return (
    <Card className="flex flex-col">
      {/* Header with Title and Current Phase indicator */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-4 border-b border-[#1E325F]/60">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h3 className="text-base font-bold text-white">
              System Architecture & Module Readiness Matrix
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time status of all 12 FLOOD-X platform subsystems across the 6-phase development roadmap.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <span className="text-[11px] font-mono text-slate-400">Current Milestone:</span>
          <span className="px-2.5 py-1 rounded-md text-xs font-mono font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
            {currentPhase}
          </span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto py-3 border-b border-[#1E325F]/40 scrollbar-none">
        {phaseButtons.map((btn) => (
          <button
            key={String(btn.value)}
            onClick={() => setSelectedPhaseFilter(btn.value)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
              selectedPhaseFilter === btn.value
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                : 'text-slate-400 hover:text-slate-200 hover:bg-[#121F3D]/50 border border-transparent'
            }`}
          >
            {btn.label}
          </button>
        ))}
      </div>

      {/* Modules List / Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-4">
        {filteredModules.map((mod) => (
          <div
            key={mod.id}
            className="bg-[#091024]/70 border border-[#1E325F]/60 rounded-xl p-4 flex flex-col justify-between hover:border-cyan-500/30 transition-colors"
          >
            <div>
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="text-[10px] font-mono text-cyan-400/80 uppercase font-semibold">
                  {mod.phase_title}
                </span>
                <StatusPill status={mod.status} />
              </div>
              <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                {mod.is_operational ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : (
                  <Clock className="w-4 h-4 text-slate-400 shrink-0" />
                )}
                <span>{mod.name}</span>
              </h4>
              <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                {mod.description}
              </p>
            </div>

            {mod.implementation_notes && (
              <div className="mt-3 pt-2.5 border-t border-[#1E325F]/40 flex items-start gap-1.5 text-[11px] text-slate-400 font-mono">
                <HelpCircle className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                <span>{mod.implementation_notes}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};

