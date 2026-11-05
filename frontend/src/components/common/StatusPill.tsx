import React from 'react';

interface StatusPillProps {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'online' | 'offline' | 'operational' | 'foundation_ready' | 'planned' | 'not_configured';
  label?: string;
  showDot?: boolean;
  className?: string;
}

export const StatusPill: React.FC<StatusPillProps> = ({
  status,
  label,
  showDot = true,
  className = '',
}) => {
  const getDisplay = () => {
    switch (status) {
      case 'healthy':
      case 'online':
      case 'operational':
        return {
          text: label || (status === 'operational' ? 'Operational' : 'Online'),
          bg: 'bg-emerald-50 text-emerald-800 border-emerald-200 font-semibold',
          dot: 'bg-emerald-500 shadow-sm',
        };
      case 'foundation_ready':
        return {
          text: label || 'Operational',
          bg: 'bg-blue-50 text-blue-800 border-blue-200 font-semibold',
          dot: 'bg-blue-500 shadow-sm',
        };
      case 'degraded':
        return {
          text: label || 'Standby Mode',
          bg: 'bg-amber-50 text-amber-800 border-amber-200 font-semibold',
          dot: 'bg-amber-500 shadow-sm animate-pulse',
        };
      case 'not_configured':
        return {
          text: label || 'Standby',
          bg: 'bg-slate-100 text-slate-700 border-slate-200 font-semibold',
          dot: 'bg-slate-400',
        };
      case 'planned':
        return {
          text: label || 'Subsystem Ready',
          bg: 'bg-indigo-50 text-indigo-800 border-indigo-200 font-semibold',
          dot: 'bg-indigo-500',
        };
      case 'unhealthy':
      case 'offline':
      default:
        return {
          text: label || 'Offline / Unreachable',
          bg: 'bg-rose-50 text-rose-800 border-rose-200 font-semibold',
          dot: 'bg-rose-500 shadow-sm',
        };
    }
  };

  const display = getDisplay();

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border ${display.bg} ${className}`}
    >
      {showDot && (
        <span className="relative flex h-2 w-2">
          <span className={`h-2 w-2 rounded-full ${display.dot}`} />
        </span>
      )}
      <span>{display.text}</span>
    </span>
  );
};
