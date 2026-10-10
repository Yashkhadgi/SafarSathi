import React, { useState } from 'react';
import { 
  Navigation, 
  Plane, 
  Train, 
  Bus, 
  MapPin, 
  AlertCircle, 
  CheckCircle2, 
  Car, 
  Loader2 
} from 'lucide-react';
import { apiGet } from '../api/client';

interface ReachOption {
  mode: string;
  duration_text?: string;
  approx_fare_inr?: string;
  notes?: string;
  warnings?: string;
  hub_name?: string;
}

interface ReachData {
  destination: string;
  origin?: string;
  options: ReachOption[];
  nearest_airport?: { name: string; distance_km: number };
  nearest_railway?: { name: string; distance_km: number };
  recommendation?: string;
}

interface LocalTransitOption {
  mode: string;
  fare_range: string;
  comfort: string;
  tips: string;
}

interface LocalData {
  city: string;
  options: LocalTransitOption[];
  recommendation?: string;
}

export const TransportPage: React.FC = () => {
  const [destination, setDestination] = useState('Jaipur');
  const [origin, setOrigin] = useState('Delhi');
  const [reachData, setReachData] = useState<ReachData | null>(null);
  const [localData, setLocalData] = useState<LocalData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const [reachRes, localRes] = await Promise.all([
        apiGet<ReachData>(`/tools/transport/reach?destination=${encodeURIComponent(destination)}&origin=${encodeURIComponent(origin)}`),
        apiGet<LocalData>(`/tools/transport/local?destination=${encodeURIComponent(destination)}`),
      ]);

      if ('error' in reachRes) {
        setError(String(reachRes.error));
      } else {
        setReachData(reachRes);
      }

      if ('error' in localRes) {
        // Soft error for local
      } else {
        setLocalData(localRes);
      }
    } catch {
      setError('Could not retrieve transport information');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">How to Reach & Local Transport</h1>
        <p className="mt-1 text-xs text-slate-400">
          Grounded transit options, nearest airport/station distances, and ranked intra-city commute benchmarks.
        </p>
      </div>

      {error && (
        <div className="p-3.5 rounded-md bg-red-950/60 border border-red-900 text-red-200 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Query Form */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800">
        <form onSubmit={handleLookup} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="trans-origin">
              Origin City
            </label>
            <input
              id="trans-origin"
              type="text"
              required
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
              placeholder="e.g. Delhi, Mumbai"
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="trans-dest">
              Destination City
            </label>
            <input
              id="trans-dest"
              type="text"
              required
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="e.g. Jaipur, Agra, Varanasi"
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white font-medium text-xs flex items-center justify-center gap-2 cursor-pointer transition-colors"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Looking up...</span>
                </>
              ) : (
                <>
                  <Navigation className="w-4 h-4" />
                  <span>Get Transit Guide</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Inter-City Transit Options */}
      {reachData && (
        <div className="space-y-6">
          <div>
            <h2 className="text-base font-semibold text-white mb-3 flex items-center gap-2">
              <Navigation className="w-4 h-4 text-brand-400" />
              <span>Inter-City Routes: {origin} to {destination}</span>
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {reachData.options?.map((opt, idx) => (
                <div key={idx} className="p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <span className="font-semibold text-sm text-white">{opt.mode}</span>
                    <span className="text-xs text-brand-300 font-medium">{opt.approx_fare_inr || 'Fare varies'}</span>
                  </div>
                  <div className="space-y-1.5 text-xs text-slate-300">
                    {opt.duration_text && (
                      <p className="text-slate-400">Duration: {opt.duration_text}</p>
                    )}
                    {opt.notes && <p className="text-slate-300 leading-relaxed">{opt.notes}</p>}
                    {opt.warnings && (
                      <p className="text-amber-300/90 text-[11px] font-medium pt-1">
                        Notice: {opt.warnings}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Local Intra-City Transit Guide */}
          {localData && localData.options && localData.options.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Car className="w-4 h-4 text-brand-400" />
                <span>Local Intra-City Transport in {destination}</span>
              </h2>

              <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-900">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950 border-b border-slate-800 text-slate-400">
                    <tr>
                      <th className="p-3 font-medium">Mode</th>
                      <th className="p-3 font-medium">Approx Fare Range</th>
                      <th className="p-3 font-medium">Comfort / Conditions</th>
                      <th className="p-3 font-medium">Local Commuter Advice</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {localData.options.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40">
                        <td className="p-3 font-semibold text-white">{row.mode}</td>
                        <td className="p-3 text-brand-300 font-medium">{row.fare_range}</td>
                        <td className="p-3 text-slate-400">{row.comfort}</td>
                        <td className="p-3 text-slate-300 leading-relaxed">{row.tips}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
