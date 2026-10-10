import React from 'react';
import { 
  Train, 
  Plane, 
  Car, 
  Bus, 
  Navigation, 
  Clock, 
  Banknote, 
  Info, 
  ExternalLink 
} from 'lucide-react';

export interface RouteOption {
  mode: string;
  duration: string;
  distance: string;
  approx_cost: string;
  notes?: string;
  source?: string;
}

export interface RouteOptionsData {
  origin: string;
  destination: string;
  options: RouteOption[];
  nearest_airport?: string;
  nearest_railway_station?: string;
  recommendation?: string;
  verify_line?: string;
  sources?: Array<{ source_name: string; source_url: string }>;
}

interface RouteCardProps {
  data: RouteOptionsData;
  onSendMessage?: (message: string) => void;
}

export const RouteCard: React.FC<RouteCardProps> = ({ data, onSendMessage }) => {
  const getModeIcon = (mode: string) => {
    const m = mode.toLowerCase();
    if (m.includes('flight') || m.includes('air') || m.includes('plane')) {
      return <Plane className="w-4 h-4 text-sky-400" />;
    }
    if (m.includes('train') || m.includes('rail')) {
      return <Train className="w-4 h-4 text-emerald-400" />;
    }
    if (m.includes('bus')) {
      return <Bus className="w-4 h-4 text-amber-400" />;
    }
    return <Car className="w-4 h-4 text-indigo-400" />;
  };

  return (
    <div className="w-full my-3 rounded-lg border border-slate-700 bg-slate-900 text-slate-100 shadow-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-slate-800/80 border-b border-slate-700 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-brand-600/20 text-brand-400 border border-brand-500/30">
            <Navigation className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
              <span>{data.origin}</span>
              <span className="text-slate-400">to</span>
              <span>{data.destination}</span>
            </h4>
            <p className="text-[11px] text-slate-400">Transit & Route Options Comparison</p>
          </div>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
          {data.options?.length || 0} Modes
        </span>
      </div>

      {/* Transit Options Table */}
      <div className="p-4 space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {data.options?.map((opt, idx) => (
            <div 
              key={idx}
              className="p-3 rounded-md bg-slate-800/60 border border-slate-700/80 hover:border-slate-600 transition-colors flex flex-col justify-between space-y-2"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-md bg-slate-800 border border-slate-700">
                    {getModeIcon(opt.mode)}
                  </div>
                  <span className="text-xs font-semibold text-slate-200">{opt.mode}</span>
                </div>
                <span className="text-[11px] font-mono text-emerald-400 font-medium">
                  {opt.approx_cost}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400">
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3 text-slate-500" />
                  <span>Duration: <strong className="text-slate-300">{opt.duration}</strong></span>
                </div>
                <div className="flex items-center gap-1">
                  <Banknote className="w-3 h-3 text-slate-500" />
                  <span>Distance: <strong className="text-slate-300">{opt.distance}</strong></span>
                </div>
              </div>

              {opt.notes && (
                <p className="text-[11px] text-slate-400 line-clamp-2 bg-slate-900/60 p-2 rounded border border-slate-800">
                  {opt.notes}
                </p>
              )}
            </div>
          ))}
        </div>

        {/* Airport & Station Facilities */}
        {(data.nearest_airport || data.nearest_railway_station) && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-xs">
            {data.nearest_airport && data.nearest_airport !== 'verify' && (
              <div className="p-2.5 rounded bg-slate-800/40 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Nearest Airport</span>
                <span className="text-slate-200 font-medium">{data.nearest_airport}</span>
              </div>
            )}
            {data.nearest_railway_station && data.nearest_railway_station !== 'verify' && (
              <div className="p-2.5 rounded bg-slate-800/40 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Nearest Railway</span>
                <span className="text-slate-200 font-medium">{data.nearest_railway_station}</span>
              </div>
            )}
          </div>
        )}

        {/* Verification & Disclaimer Note */}
        {data.verify_line && (
          <div className="p-2.5 rounded-md bg-slate-800/50 border border-slate-700/60 flex items-start gap-2 text-[11px] text-slate-400">
            <Info className="w-3.5 h-3.5 text-brand-400 shrink-0 mt-0.5" />
            <span>{data.verify_line}</span>
          </div>
        )}

        {/* Quick Follow-up Actions */}
        {onSendMessage && (
          <div className="pt-2 flex flex-wrap gap-2">
            <button
              onClick={() => onSendMessage(`Show train timings and schedule from ${data.origin} to ${data.destination}`)}
              className="px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
            >
              Check train routes
            </button>
            <button
              onClick={() => onSendMessage(`Where to stay near arrival station in ${data.destination}?`)}
              className="px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
            >
              Where to stay
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
