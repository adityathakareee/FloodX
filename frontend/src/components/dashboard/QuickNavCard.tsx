import React from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  Navigation,
  Brain,
  Sliders,
  ArrowRight,
} from 'lucide-react';
import { Card } from '../common/Card';

export const QuickNavCard: React.FC = () => {
  const quickLinks = [
    {
      title: 'Live Telemetry & Sensors',
      desc: 'IMD rainfall, CWC river stages, Khadakwasla dam discharge.',
      path: '/monitoring',
      phase: 'Phase 1',
      icon: Activity,
    },
    {
      title: 'AI Flood Risk Prediction',
      desc: 'Inundation extent ML models & time-to-impact calculations.',
      path: '/risk',
      phase: 'Phase 2',
      icon: AlertTriangle,
    },
    {
      title: 'Safe Evacuation Routing',
      desc: 'Topography-aware pathfinding avoiding submerged bridges.',
      path: '/evacuation',
      phase: 'Phase 3',
      icon: Navigation,
    },
    {
      title: 'Nugen AI Decision Support',
      desc: 'Explainable disaster action advisories aligned with NDMA SOPs.',
      path: '/decision',
      phase: 'Phase 4',
      icon: Brain,
    },
    {
      title: 'Dam Release What-If Simulator',
      desc: 'Simulate Khadakwasla spillway releases from 20k to 90k cusecs.',
      path: '/scenarios',
      phase: 'Phase 4',
      icon: Sliders,
    },
  ];

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
            Upcoming Modules Preview
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Architecture and specifications for upcoming development milestones.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {quickLinks.map((link) => {
          const Icon = link.icon;
          return (
            <Link
              key={link.path}
              to={link.path}
              className="group bg-[#091024]/60 hover:bg-[#121F3D]/80 border border-[#1E325F]/60 hover:border-cyan-500/40 rounded-xl p-3.5 flex flex-col justify-between transition-all duration-150"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 group-hover:bg-cyan-500/20 transition-colors">
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                    {link.phase}
                  </span>
                </div>
                <h4 className="text-sm font-semibold text-slate-200 group-hover:text-cyan-300 transition-colors">
                  {link.title}
                </h4>
                <p className="text-xs text-slate-400 mt-1 leading-snug">
                  {link.desc}
                </p>
              </div>

              <div className="mt-3 pt-2 border-t border-[#1E325F]/40 flex items-center justify-between text-xs text-cyan-400/80 font-mono group-hover:text-cyan-300">
                <span>View Spec</span>
                <ArrowRight className="w-3.5 h-3.5 transform group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          );
        })}
      </div>
    </Card>
  );
};

