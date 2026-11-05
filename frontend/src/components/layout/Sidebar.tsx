import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  AlertTriangle,
  Users,
  Navigation,
  Truck,
  Sliders,
  Shield,
  Waves,
  MapPin,
  HelpCircle,
} from 'lucide-react';

interface NavItem {
  name: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { name: 'Dashboard Overview', path: '/', icon: LayoutDashboard },
  { name: 'Environmental Telemetry', path: '/monitoring', icon: Activity },
  { name: 'Flood Risk Prediction', path: '/risk', icon: AlertTriangle },
  { name: 'Inundation & Impact', path: '/impact', icon: Users },
  { name: 'Evacuation & Routing', path: '/evacuation', icon: Navigation },
  { name: 'Dam Scenario Simulation', path: '/scenarios', icon: Sliders },
  { name: 'Resource Optimization', path: '/resources', icon: Truck },
  { name: 'Authority Command Center', path: '/command-center', icon: Shield },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-screen sticky top-0 shrink-0 shadow-xs select-none">
      {/* Brand Header */}
      <div className="h-16 px-5 flex items-center gap-3 border-b border-slate-200 bg-white">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-white shadow-sm shadow-blue-500/20">
          <Waves className="w-5 h-5 text-white stroke-[2.5]" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="font-extrabold text-base tracking-wider text-slate-900">FLOOD-X</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
              LIVE
            </span>
          </div>
          <p className="text-[10px] font-medium tracking-tight text-slate-500 font-mono">
            PUNE BASIN INTELLIGENCE
          </p>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        <div className="px-3 pb-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider font-mono">
          Command Subsystems
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `group flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-150 ${isActive
                  ? 'bg-blue-50 text-blue-700 font-bold border-l-4 border-blue-600 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 shrink-0 transition-colors group-hover:text-blue-600" />
                <span className="truncate">{item.name}</span>
              </div>
              {item.badge && (
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-semibold">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-200 bg-slate-50 text-xs text-slate-600 font-sans">
        <div className="flex items-center gap-2 mb-1.5 text-slate-700 font-medium">
          <MapPin className="w-3.5 h-3.5 text-blue-600 shrink-0" />
          <span className="truncate text-xs font-semibold">Pune Municipal Corp</span>
        </div>
        <div className="text-[11px] text-slate-500 flex items-center justify-between">
          <span>Authority Cockpit</span>
          <span className="inline-flex items-center gap-1 text-emerald-600 font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Online
          </span>
        </div>
      </div>
    </aside>
  );
};
