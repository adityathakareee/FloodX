import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'cyan' | 'blue' | 'emerald' | 'amber' | 'rose' | 'slate';
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'blue',
  size = 'sm',
  className = '',
}) => {
  const variantStyles = {
    cyan: 'bg-cyan-50 text-cyan-800 border-cyan-200 font-semibold',
    blue: 'bg-blue-50 text-blue-800 border-blue-200 font-semibold',
    emerald: 'bg-emerald-50 text-emerald-800 border-emerald-200 font-semibold',
    amber: 'bg-amber-50 text-amber-800 border-amber-200 font-semibold',
    rose: 'bg-rose-50 text-rose-800 border-rose-200 font-semibold',
    slate: 'bg-slate-100 text-slate-700 border-slate-200 font-semibold',
  };

  const sizeStyles = {
    sm: 'text-xs px-2.5 py-0.5',
    md: 'text-sm px-3 py-1',
  };

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </span>
  );
};
