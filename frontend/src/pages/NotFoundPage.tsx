import React from 'react';
import { Link } from 'react-router-dom';
import { Compass, ArrowLeft } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4 text-center">
      <div className="max-w-md">
        <div className="w-12 h-12 rounded-md bg-slate-900 border border-slate-800 text-brand-400 mx-auto flex items-center justify-center mb-4">
          <Compass className="w-6 h-6" />
        </div>
        <h1 className="text-2xl font-bold text-white">404: Page Not Found</h1>
        <p className="mt-2 text-xs text-slate-400">
          The requested page or resource could not be found.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-brand-600 hover:bg-brand-700 text-white text-xs font-medium transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to Home</span>
          </Link>
        </div>
      </div>
    </div>
  );
};
