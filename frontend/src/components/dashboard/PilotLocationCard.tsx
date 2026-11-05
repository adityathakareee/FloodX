import React from 'react';
import { MapPin, Navigation, Droplets, Mountain } from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';

export const PilotLocationCard: React.FC = () => {
  return (
    <Card className="relative overflow-hidden">
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs font-mono text-blue-700 font-bold uppercase tracking-wide flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5" /> Target Hydrological Basin
            </span>
            <Badge variant="blue" size="sm">Pilot Geography</Badge>
          </div>
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">
            Pune / Mula-Mutha River Basin
          </h2>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
            The confluence of the Mula and Mutha rivers drains the Western Ghats catchment via upstream cascade reservoirs
            (Khadakwasla, Panshet, Varasgaon, Mulshi, and Pawana). Downstream metropolitan corridors face high inundation risks during monsoonal dam spillway releases.
          </p>
        </div>

        <div className="flex flex-wrap md:flex-col items-start md:items-end gap-2 shrink-0">
          <div className="text-right">
            <span className="text-[10px] uppercase font-mono text-slate-400 block font-semibold">Centroid Coordinates</span>
            <span className="text-xs font-mono font-bold text-slate-800">18.5204° N, 73.8567° E</span>
          </div>
          <div className="text-right">
            <span className="text-[10px] uppercase font-mono text-slate-400 block font-semibold">Elevation Datum</span>
            <span className="text-xs font-mono font-bold text-slate-800">560m MSL (Pune City)</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-3 border-t border-slate-100 text-xs">
        <div className="flex items-start gap-2.5 bg-slate-50 p-2.5 rounded-xl border border-slate-200">
          <Droplets className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-800 block">River Network</span>
            <span className="text-slate-500 text-[11px]">Mula, Mutha, Pavana, Indrayani Reaches</span>
          </div>
        </div>

        <div className="flex items-start gap-2.5 bg-slate-50 p-2.5 rounded-xl border border-slate-200">
          <Mountain className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-800 block">Upstream Dams</span>
            <span className="text-slate-500 text-[11px]">Khadakwasla, Mulshi, Panshet, Varasgaon</span>
          </div>
        </div>

        <div className="flex items-start gap-2.5 bg-slate-50 p-2.5 rounded-xl border border-slate-200 sm:col-span-2 lg:col-span-1">
          <Navigation className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-800 block">Vulnerability Focus</span>
            <span className="text-slate-500 text-[11px]">Bhide Causeway, Pulachi Wadi, Sinhagad Rd</span>
          </div>
        </div>
      </div>
    </Card>
  );
};
