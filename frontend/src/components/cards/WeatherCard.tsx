import React from 'react';
import { 
  CloudSun, 
  Wind, 
  Thermometer, 
  Droplets, 
  AlertTriangle, 
  Calendar, 
  Info 
} from 'lucide-react';

export interface WeatherForecastItem {
  date?: string;
  day?: string;
  temp_min?: number;
  temp_max?: number;
  temp_high_c?: number;
  temp_low_c?: number;
  condition: string;
}

export interface WeatherData {
  city: string;
  temperature_c?: number;
  condition?: string;
  air_quality?: {
    index?: number;
    scale?: string;
    label?: string;
    pm2_5_ug_m3?: number;
    source_url?: string;
    error?: string;
  };
  forecast?: WeatherForecastItem[];
  warnings?: string[];
  last_verified?: string;
}

interface WeatherCardProps {
  data: WeatherData;
  onSendMessage?: (message: string) => void;
}

export const WeatherCard: React.FC<WeatherCardProps> = ({ data, onSendMessage }) => {
  const getAqiBadge = (index?: number, label?: string) => {
    if (!index && !label) return null;
    let colorClass = 'bg-emerald-950 text-emerald-300 border-emerald-800';
    if (index === 3 || label === 'Moderate') {
      colorClass = 'bg-amber-950 text-amber-300 border-amber-800';
    } else if ((index && index >= 4) || label === 'Poor' || label === 'Very poor') {
      colorClass = 'bg-red-950 text-red-300 border-red-800';
    }
    return (
      <span className={`text-[11px] px-2 py-0.5 rounded border font-medium ${colorClass}`}>
        AQI: {label || `Level ${index}`}
      </span>
    );
  };

  return (
    <div className="w-full my-3 rounded-lg border border-slate-700 bg-slate-900 text-slate-100 shadow-lg overflow-hidden">
      {/* Card Header */}
      <div className="px-4 py-3 bg-slate-800/80 border-b border-slate-700 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-amber-500/20 text-amber-400 border border-amber-500/30">
            <CloudSun className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100">{data.city} Weather & AQI</h4>
            <p className="text-[11px] text-slate-400">Live conditions and multi-day forecast</p>
          </div>
        </div>
        {getAqiBadge(data.air_quality?.index, data.air_quality?.label)}
      </div>

      <div className="p-4 space-y-4">
        {/* Current Weather Highlight */}
        <div className="flex flex-wrap items-center justify-between p-3 rounded-md bg-slate-800/60 border border-slate-700/80 gap-3">
          <div className="flex items-center gap-3">
            <Thermometer className="w-8 h-8 text-amber-400" />
            <div>
              <div className="text-2xl font-bold text-slate-100">
                {data.temperature_c !== undefined ? `${data.temperature_c}°C` : 'Current temp'}
              </div>
              <div className="text-xs text-slate-300 capitalize">{data.condition || 'Clear conditions'}</div>
            </div>
          </div>

          {data.air_quality && !data.air_quality.error && (
            <div className="text-right text-xs space-y-0.5">
              <div className="text-slate-400">PM2.5 Index</div>
              <div className="font-semibold text-slate-200">
                {data.air_quality.pm2_5_ug_m3 ? `${data.air_quality.pm2_5_ug_m3} µg/m³` : data.air_quality.label || 'Moderate'}
              </div>
            </div>
          )}
        </div>

        {/* Multi-day Forecast */}
        {data.forecast && data.forecast.length > 0 && (
          <div>
            <span className="text-[11px] text-slate-400 uppercase tracking-wider block mb-2">Upcoming Days Forecast</span>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
              {data.forecast.map((f, idx) => {
                const high = f.temp_max ?? f.temp_high_c;
                const low = f.temp_min ?? f.temp_low_c;
                return (
                  <div key={idx} className="p-2.5 rounded bg-slate-800/40 border border-slate-800 text-center space-y-1">
                    <div className="text-[11px] text-slate-400 font-mono">{f.date || f.day || `Day ${idx + 1}`}</div>
                    <div className="text-xs font-semibold text-slate-200">
                      {high !== undefined && low !== undefined ? `${high}° / ${low}°` : f.condition}
                    </div>
                    <div className="text-[10px] text-slate-400 capitalize truncate">{f.condition}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Weather Warnings */}
        {data.warnings && data.warnings.length > 0 && (
          <div className="space-y-1.5">
            {data.warnings.map((w, idx) => (
              <div key={idx} className="p-2 rounded bg-amber-950/40 border border-amber-800/60 flex items-start gap-2 text-[11px] text-amber-200">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                <span>{w}</span>
              </div>
            ))}
          </div>
        )}

        {/* Sourced Tag */}
        <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-800">
          <span>Source: OpenWeather verified data</span>
          {data.last_verified && <span>Verified: {data.last_verified}</span>}
        </div>

        {/* Quick Follow-up Actions */}
        {onSendMessage && (
          <div className="pt-1 flex flex-wrap gap-2">
            <button
              onClick={() => onSendMessage(`What should I pack for ${data.city} given this weather?`)}
              className="px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
            >
              Packing suggestions
            </button>
            <button
              onClick={() => onSendMessage(`What are good indoor places or Plan B in ${data.city} if it rains?`)}
              className="px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
            >
              Indoor Plan B
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
