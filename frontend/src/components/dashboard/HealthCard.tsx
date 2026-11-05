import React from 'react';
import { Server, Database, Radio, Cpu } from 'lucide-react';
import { Card } from '../common/Card';
import { StatusPill } from '../common/StatusPill';
import { HealthResponse } from '../../types/api';

interface HealthCardProps {
  health: HealthResponse | null;
  isOnline: boolean;
  isLoading: boolean;
}

export const HealthCard: React.FC<HealthCardProps> = ({
  health,
  isOnline,
  isLoading,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Backend REST API */}
      <Card className="flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
              <Server className="w-5 h-5" />
            </div>
            <StatusPill
              status={isOnline ? 'online' : 'offline'}
              label={isOnline ? 'Online' : 'Unreachable'}
            />
          </div>
          <h3 className="text-sm font-bold text-slate-800">FastAPI Intelligence Engine</h3>
          <p className="text-xs text-slate-500 mt-0.5">REST API Gateway & Controllers</p>
        </div>
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-mono text-slate-500">
          <span>Uptime:</span>
          <span className="text-slate-800 font-semibold">
            {health?.uptime_seconds ? `${Math.floor(health.uptime_seconds)}s` : '—'}
          </span>
        </div>
      </Card>

      {/* 2. PostgreSQL + PostGIS Database */}
      <Card className="flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
              <Database className="w-5 h-5" />
            </div>
            <StatusPill
              status={
                health?.database?.status === 'connected'
                  ? 'healthy'
                  : 'degraded'
              }
              label={
                health?.database?.status === 'connected'
                  ? 'Connected'
                  : 'Disconnected'
              }
            />
          </div>
          <h3 className="text-sm font-bold text-slate-800">PostgreSQL + PostGIS</h3>
          <p className="text-xs text-slate-500 mt-0.5">Spatial Vector & Telemetry Store</p>
        </div>
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-mono text-slate-500">
          <span>Engine / Latency:</span>
          <span className="text-slate-800 font-semibold">
            {health?.database?.latency_ms !== undefined && health?.database?.latency_ms !== null
              ? `${health.database.latency_ms.toFixed(1)}ms`
              : 'PostGIS 3.4'}
          </span>
        </div>
      </Card>

      {/* 3. Real-Time Telemetry */}
      <Card className="flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600">
              <Radio className="w-5 h-5" />
            </div>
            <StatusPill
              status={isOnline ? 'operational' : 'offline'}
              label={isOnline ? 'Active' : 'Offline'}
            />
          </div>
          <h3 className="text-sm font-bold text-slate-800">Hydrological Telemetry</h3>
          <p className="text-xs text-slate-500 mt-0.5">Rainfall, River Stage & Dam Feed</p>
        </div>
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-mono text-slate-500">
          <span>Observed Reanalysis:</span>
          <span className="text-slate-800 font-semibold">50k+ Obs (CWPRS/CWC)</span>
        </div>
      </Card>

      {/* 4. AI/ML Inference */}
      <Card className="flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 rounded-xl bg-purple-50 border border-purple-200 flex items-center justify-center text-purple-600">
              <Cpu className="w-5 h-5" />
            </div>
            <StatusPill
              status={isOnline ? 'operational' : 'offline'}
              label={isOnline ? 'Active' : 'Offline'}
            />
          </div>
          <h3 className="text-sm font-bold text-slate-800">AI Risk Inference & Routing</h3>
          <p className="text-xs text-slate-500 mt-0.5">Prospective ML & Graph A*</p>
        </div>
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-mono text-slate-500">
          <span>Forward Window:</span>
          <span className="text-slate-800 font-semibold">6h / 12h / 24h / 48h</span>
        </div>
      </Card>
    </div>
  );
};
