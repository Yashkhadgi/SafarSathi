import React from 'react';
import { 
  Milestone, 
  MapPin, 
  Calendar, 
  ArrowRight, 
  Info, 
  Sparkles 
} from 'lucide-react';

export interface MultiCityStop {
  city: string;
  recommended_days: number;
  travel_from_prev?: string;
  key_highlights?: string[];
}

export interface MultiCityLeg {
  from: string;
  to: string;
  distance_km_approx: number;
  note?: string;
}

export interface MultiCityData {
  origin: string;
  ordered_cities: MultiCityStop[];
  inter_city_legs?: MultiCityLeg[];
  total_days: number;
  total_km_approx: number;
  disclaimer?: string;
  warnings?: string[];
}

interface MultiCityCardProps {
  data: MultiCityData;
  onSendMessage?: (message: string) => void;
}

export const MultiCityCard: React.FC<MultiCityCardProps> = ({ data, onSendMessage }) => {
  return (
    <div className="w-full my-3 rounded-lg border border-slate-700 bg-slate-900 text-slate-100 shadow-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-slate-800/80 border-b border-slate-700 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
            <Milestone className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100">
              Multi-City Route Optimizer (TSP)
            </h4>
            <p className="text-[11px] text-slate-400">
              {data.ordered_cities?.length || 0} Cities starting from {data.origin}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
            {data.total_days} Total Days
          </span>
          <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-emerald-400">
            ~{data.total_km_approx} km
          </span>
        </div>
      </div>

      {/* Optimized Stops Sequence */}
      <div className="p-4 space-y-4">
        <div>
          <span className="text-[11px] text-slate-400 uppercase tracking-wider block mb-2">
            Recommended Tour Sequence & Day Allocation
          </span>
          <div className="space-y-2">
            {data.ordered_cities?.map((stop, idx) => (
              <div 
                key={idx}
                className="p-3 rounded-md bg-slate-800/50 border border-slate-700/70 hover:border-slate-600 transition-colors flex items-center justify-between gap-3"
              >
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-full bg-brand-600 text-white flex items-center justify-center text-xs font-bold shrink-0">
                    {idx + 1}
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-slate-200">{stop.city}</span>
                    <span className="text-[11px] text-slate-400 block">{stop.travel_from_prev}</span>
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <span className="text-xs font-mono font-medium text-indigo-300 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800">
                    {stop.recommended_days} {stop.recommended_days === 1 ? 'Day' : 'Days'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Inter-City Legs Details */}
        {data.inter_city_legs && data.inter_city_legs.length > 0 && (
          <div>
            <span className="text-[11px] text-slate-400 uppercase tracking-wider block mb-2">
              Inter-City Legs (Haversine Distance)
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              {data.inter_city_legs.map((leg, idx) => (
                <div key={idx} className="p-2 rounded bg-slate-800/30 border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-slate-300">
                    <span>{leg.from}</span>
                    <ArrowRight className="w-3 h-3 text-slate-500" />
                    <span>{leg.to}</span>
                  </div>
                  <span className="font-mono text-emerald-400">~{leg.distance_km_approx} km</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Disclaimer */}
        {data.disclaimer && (
          <div className="p-2.5 rounded-md bg-slate-800/50 border border-slate-700/60 flex items-start gap-2 text-[11px] text-slate-400">
            <Info className="w-3.5 h-3.5 text-brand-400 shrink-0 mt-0.5" />
            <span>{data.disclaimer}</span>
          </div>
        )}

        {/* Follow-up Prompts */}
        {onSendMessage && data.ordered_cities && data.ordered_cities.length > 0 && (
          <div className="pt-2 flex flex-wrap gap-2">
            <button
              onClick={() => onSendMessage(`Build a full day-by-day itinerary for this ${data.ordered_cities.map(c => c.city).join(', ')} trip`)}
              className="px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
            >
              Build full itinerary for this route
            </button>
            <button
              onClick={() => onSendMessage(`Compare budget tiers for this multi-city trip`)}
              className="px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
            >
              Estimate budget
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
