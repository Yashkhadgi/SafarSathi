import React, { useState } from 'react';
import { 
  Train, 
  Bus, 
  MapPin, 
  Building, 
  Search, 
  AlertCircle, 
  CheckCircle2, 
  Loader2 
} from 'lucide-react';
import { apiGet } from '../api/client';

export const TransportStayPage: React.FC = () => {
  // Train / Bus State
  const [origin, setOrigin] = useState('Delhi');
  const [destination, setDestination] = useState('Jaipur');
  const [transitData, setTransitData] = useState<{
    trains_summary?: string;
    buses_summary?: string;
    travel_time_hours?: string;
    irctc_notice?: string;
  } | null>(null);
  const [transitLoading, setTransitLoading] = useState(false);

  // Stay Areas State
  const [stayCity, setStayCity] = useState('Jaipur');
  const [stayData, setStayData] = useState<{
    city?: string;
    areas?: Array<{ name: string; best_for: string; vibe: string; pros: string; cons: string }>;
  } | null>(null);
  const [stayLoading, setStayLoading] = useState(false);

  const handleTransit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTransitLoading(true);
    try {
      const res = await apiGet<unknown>(
        `/tools/transport/train-bus?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}`
      );
      setTransitData(res as typeof transitData);
    } catch {
      setTransitData(null);
    } finally {
      setTransitLoading(false);
    }
  };

  const handleStay = async (e: React.FormEvent) => {
    e.preventDefault();
    setStayLoading(true);
    try {
      const res = await apiGet<unknown>(`/tools/stay/areas?city=${encodeURIComponent(stayCity)}`);
      setStayData(res as typeof stayData);
    } catch {
      setStayData(null);
    } finally {
      setStayLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Train/Bus Routes & Neighborhood Stay Guide</h1>
        <p className="mt-1 text-xs text-slate-400">
          Intercity train and bus connectivity (informational only) and area-wise neighborhood stay recommendations.
        </p>
      </div>

      {/* 1. Train & Bus Route Information */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Train className="w-4 h-4 text-brand-400" />
          <span>Train & Bus Route Connectivity</span>
        </h2>

        <form onSubmit={handleTransit} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <input
            type="text"
            required
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            placeholder="Origin (e.g. Delhi)"
            className="px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
          <input
            type="text"
            required
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="Destination (e.g. Jaipur)"
            className="px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
          <button
            type="submit"
            disabled={transitLoading}
            className="py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            {transitLoading ? 'Loading...' : 'Find Routes'}
          </button>
        </form>

        {transitData && (
          <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs space-y-3">
            <div className="p-2.5 rounded bg-brand-950/40 border border-brand-800/60 text-brand-200 text-[11px]">
              <strong className="block mb-0.5">IRCTC Verification Notice:</strong>
              {transitData.irctc_notice || 'Train schedules and seat availability change dynamically. Verify on official IRCTC or state transport portals.'}
            </div>

            <div className="space-y-2 text-slate-300">
              {transitData.trains_summary && (
                <div>
                  <strong className="text-white block mb-0.5">Train Services:</strong>
                  <p className="text-slate-400 leading-relaxed">{transitData.trains_summary}</p>
                </div>
              )}

              {transitData.buses_summary && (
                <div>
                  <strong className="text-white block mb-0.5">Bus Services:</strong>
                  <p className="text-slate-400 leading-relaxed">{transitData.buses_summary}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 2. Neighborhood Stay Areas */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Building className="w-4 h-4 text-brand-400" />
          <span>Neighborhood Stay Advice</span>
        </h2>

        <form onSubmit={handleStay} className="flex gap-3 max-w-md">
          <input
            type="text"
            required
            value={stayCity}
            onChange={(e) => setStayCity(e.target.value)}
            placeholder="City (e.g. Jaipur, Goa, Udaipur)"
            className="flex-1 px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
          <button
            type="submit"
            disabled={stayLoading}
            className="py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            {stayLoading ? 'Loading...' : 'Find Stay Areas'}
          </button>
        </form>

        {stayData && stayData.areas && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {stayData.areas.map((area, idx) => (
              <div key={idx} className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-sm">{area.name}</span>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-brand-300 text-[10px]">
                    {area.best_for}
                  </span>
                </div>
                <p className="text-slate-400 italic">Vibe: {area.vibe}</p>
                <div className="space-y-1 pt-1 border-t border-slate-900">
                  <p className="text-emerald-400 text-[11px]"><strong>Pros:</strong> {area.pros}</p>
                  <p className="text-slate-400 text-[11px]"><strong>Cons:</strong> {area.cons}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
