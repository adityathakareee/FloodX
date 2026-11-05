import React, { useState, useEffect } from 'react';
import { RefreshCw, MapPin, Activity, Bell } from 'lucide-react';
import { StatusPill } from '../common/StatusPill';
import { useSystemHealth } from '../../hooks/useSystemHealth';

export const Topbar: React.FC = () => {
  const { health, isLoading, isOnline, refresh } = useSystemHealth(10000);
  const [currentTime, setCurrentTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleDateString('en-IN', {
          weekday: 'short',
          day: '2-digit',
          month: 'short',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        })
      );
    };

    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const getSystemStatus = () => {
    if (!isOnline) return 'offline';
    if (health?.status === 'degraded') return 'degraded';
    if (health?.status === 'healthy') return 'healthy';
    return 'degraded';
  };

  return (
    <header className="h-16 bg-white/95 backdrop-blur-md border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-20 shadow-xs select-none">
      {/* Left: Pilot Region & Coordinates */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-xs font-mono bg-blue-50 border border-blue-200/80 px-3 py-1.5 rounded-lg text-blue-700">
          <MapPin className="w-3.5 h-3.5 text-blue-600" />
          <span className="font-bold">PILOT BASIN:</span>
          <span className="font-semibold">Pune / Mula-Mutha</span>
        </div>

        <div className="hidden lg:flex items-center gap-2 text-xs font-mono text-slate-500">
          <span>CENTER:</span>
          <span className="text-slate-700 font-semibold">18.5204° N, 73.8567° E</span>
        </div>
      </div>

      {/* Right: Health status, Live Clock, Refresh */}
      <div className="flex items-center gap-4">
        {/* Backend Connectivity Status */}
        <div className="flex items-center gap-2">
          <StatusPill
            status={getSystemStatus()}
            label={
              !isOnline
                ? 'Backend Offline'
                : health?.status === 'degraded'
                  ? 'API Online (DB Degraded)'
                  : 'Systems Healthy'
            }
          />
          <button
            onClick={() => refresh()}
            title="Refresh connectivity health"
            className="p-1.5 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-slate-100 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-blue-600' : ''}`} />
          </button>
        </div>

        <div className="h-4 w-px bg-slate-200" />

        {/* Live Clock */}
        <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-slate-600 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg">
          <Activity className="w-3.5 h-3.5 text-blue-600" />
          <span>{currentTime || 'Synchronizing...'}</span>
          <span className="text-[10px] text-slate-400 font-bold ml-0.5">IST</span>
        </div>
      </div>
    </header>
  );
};
