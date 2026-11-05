import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  glow = false,
}) => {
  return (
    <div
      className={`bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all duration-200 text-slate-900 ${
        glow ? 'border-blue-400/50 shadow-md ring-1 ring-blue-500/20' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
};
