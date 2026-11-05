import React from 'react';
import { Layers, Crosshair, Compass, ShieldAlert, Maximize2 } from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';

export const MapPlaceholder: React.FC = () => {
  return (
    <Card className="flex flex-col p-0 overflow-hidden border-[#1E325F]/80">
      {/* Map Control Bar */}
      <div className="h-12 px-4 bg-[#091024] border-b border-[#1E325F]/60 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs font-mono font-semibold text-slate-300">
            <Crosshair className="w-4 h-4 text-cyan-400" />
            <span>GIS SPATIAL VIEWPORT</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400 border border-slate-700 px-2 py-0.5 rounded bg-slate-800">
            EPSG:4326 / EPSG:32643
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="amber" size="sm">
            Phase 1 Integration Pending
          </Badge>
          <button
            type="button"
            className="p-1 text-slate-400 hover:text-slate-200 transition-colors"
            title="Full Screen (Phase 1)"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Map Viewport Placeholder */}
      <div className="relative h-[380px] bg-[#060B18] overflow-hidden flex flex-col items-center justify-center p-6 text-center select-none">
        {/* Subtle GIS Coordinate Grid Lines */}
        <div
          className="absolute inset-0 opacity-15 pointer-events-none"
          style={{
            backgroundImage: `
              linear-gradient(to right, #00F0FF 1px, transparent 1px),
              linear-gradient(to bottom, #00F0FF 1px, transparent 1px)
            `,
            backgroundSize: '40px 40px',
          }}
        />

        {/* Central Geographic Crosshair & Pune Centroid Pin */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20">
          <div className="w-64 h-64 border border-cyan-400 rounded-full" />
          <div className="w-96 h-96 border border-cyan-400/40 rounded-full" />
          <div className="w-full h-px bg-cyan-400/30 absolute" />
          <div className="h-full w-px bg-cyan-400/30 absolute" />
        </div>

        {/* Top-Right Compass Rose */}
        <div className="absolute top-4 right-4 bg-[#091024]/80 backdrop-blur-sm border border-[#1E325F] p-2 rounded-lg text-slate-400 flex flex-col items-center shadow-lg">
          <Compass className="w-5 h-5 text-cyan-400 animate-spin-slow" />
          <span className="text-[9px] font-mono font-bold text-slate-300 mt-0.5">N</span>
        </div>

        {/* Bottom-Left Coordinate & Scale HUD */}
        <div className="absolute bottom-4 left-4 bg-[#091024]/90 backdrop-blur-sm border border-[#1E325F] px-3 py-1.5 rounded-lg text-left font-mono text-[11px] space-y-0.5 shadow-lg">
          <div className="text-slate-400 flex items-center gap-1.5">
            <span className="text-cyan-400">LAT:</span> 18.5204° N &nbsp;|&nbsp;
            <span className="text-cyan-400">LON:</span> 73.8567° E
          </div>
          <div className="text-[10px] text-slate-400 flex items-center gap-2">
            <span>SCALE: 1:50,000</span>
            <div className="w-12 h-1 bg-cyan-400/80 rounded-sm" />
            <span>2.5 km</span>
          </div>
        </div>

        {/* Top-Left Planned GIS Layers Placeholder */}
        <div className="hidden sm:flex absolute top-4 left-4 bg-[#091024]/90 backdrop-blur-sm border border-[#1E325F] p-2.5 rounded-lg text-left font-mono text-xs flex-col gap-1.5 shadow-lg">
          <div className="flex items-center gap-1.5 text-slate-300 font-semibold text-[11px]">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span>PLANNED GIS LAYERS</span>
          </div>
          <div className="text-[10px] text-slate-400 space-y-1">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-slate-600" />
              <span>Mula-Mutha River Reaches (P1)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-slate-600" />
              <span>Catchment Contours (P1)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-slate-600" />
              <span>Live River Gauges (P1)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-slate-600" />
              <span>Inundation Polygons (P2)</span>
            </div>
          </div>
        </div>

        {/* Center Notice: Strict Phase Boundary */}
        <div className="relative z-10 max-w-md bg-[#0D162B]/95 border border-[#1E325F] rounded-xl p-6 shadow-2xl backdrop-blur-md">
          <div className="w-12 h-12 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mx-auto mb-3">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-white">
            GIS Map Engine & Sensor Overlay
          </h3>
          <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
            In compliance with strict Phase 0 boundaries, simulated flood heatmaps and fabricated telemetry layers are intentionally suppressed.
          </p>
          <div className="mt-4 pt-3 border-t border-[#1E325F]/70 flex items-center justify-center gap-2">
            <span className="text-[11px] font-mono text-slate-400">Scheduled for Integration in</span>
            <Badge variant="cyan" size="sm">Phase 1: Real-Time GIS</Badge>
          </div>
        </div>
      </div>
    </Card>
  );
};

