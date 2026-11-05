import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, ArrowLeft } from 'lucide-react';
import { Card } from '../components/common/Card';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Card className="max-w-md text-center p-8 border-rose-500/30">
        <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 mx-auto mb-4">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h1 className="text-xl font-bold text-white mb-1">404: Route Not Found</h1>
        <p className="text-xs text-slate-400 mb-6">
          The requested command view is not recognized in the FLOOD-X Authority Dashboard.
        </p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold transition-colors font-mono"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>RETURN TO OVERVIEW</span>
        </Link>
      </Card>
    </div>
  );
};

