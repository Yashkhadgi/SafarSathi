import React, { useState } from 'react';
import { 
  CloudSun, 
  Wind, 
  Clock, 
  MapPin, 
  Search, 
  AlertCircle, 
  CheckCircle2, 
  Utensils, 
  Loader2 
} from 'lucide-react';
import { apiGet } from '../api/client';

export const WeatherHoursNearMePage: React.FC = () => {
  // Weather State
  const [weatherCity, setWeatherCity] = useState('Jaipur');
  const [weatherData, setWeatherData] = useState<{
    place?: string;
    forecast?: Array<{ date: string; temp_min: number; temp_max: number; condition: string }>;
    air_quality?: { index: number; label: string; pm2_5_ug_m3?: number };
    warnings?: string[];
  } | null>(null);
  const [weatherLoading, setWeatherLoading] = useState(false);

  // Hours State
  const [monument, setMonument] = useState('Taj Mahal');
  const [monumentCity, setMonumentCity] = useState('Agra');
  const [hoursData, setHoursData] = useState<{
    place?: string;
    hours?: string;
    closed?: boolean;
    warnings?: string[];
    source_name?: string;
  } | null>(null);
  const [hoursLoading, setHoursLoading] = useState(false);

  // Near Me State
  const [nearCity, setNearCity] = useState('Jaipur');
  const [nearCategory, setNearCategory] = useState('attractions');
  const [vegOnly, setVegOnly] = useState(false);
  const [nearData, setNearData] = useState<{
    results?: Array<{ name: string; distance_km: number; address?: string; rating?: number }>;
  } | null>(null);
  const [nearLoading, setNearLoading] = useState(false);

  const handleWeather = async (e: React.FormEvent) => {
    e.preventDefault();
    setWeatherLoading(true);
    try {
      const res = await apiGet<unknown>(`/tools/weather?destination=${encodeURIComponent(weatherCity)}&days=3`);
      setWeatherData(res as typeof weatherData);
    } catch {
      setWeatherData(null);
    } finally {
      setWeatherLoading(false);
    }
  };

  const handleHours = async (e: React.FormEvent) => {
    e.preventDefault();
    setHoursLoading(true);
    try {
      const res = await apiGet<unknown>(
        `/tools/hours?place=${encodeURIComponent(monument)}&city=${encodeURIComponent(monumentCity)}`
      );
      setHoursData(res as typeof hoursData);
    } catch {
      setHoursData(null);
    } finally {
      setHoursLoading(false);
    }
  };

  const handleNearMe = async (e: React.FormEvent) => {
    e.preventDefault();
    setNearLoading(true);
    try {
      const res = await apiGet<unknown>(
        `/tools/near-me?city=${encodeURIComponent(nearCity)}&category=${nearCategory}&veg=${vegOnly}&consent=true`
      );
      setNearData(res as typeof nearData);
    } catch {
      setNearData(null);
    } finally {
      setNearLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Weather, Opening Hours & Near Me</h1>
        <p className="mt-1 text-xs text-slate-400">
          Real-time weather forecast, air quality indices, verified monument schedules, and nearby amenities.
        </p>
      </div>

      {/* 1. Weather and AQI Card */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <CloudSun className="w-4 h-4 text-brand-400" />
          <span>Live Weather & Air Quality Index (AQI)</span>
        </h2>

        <form onSubmit={handleWeather} className="flex gap-3 max-w-md">
          <input
            type="text"
            required
            value={weatherCity}
            onChange={(e) => setWeatherCity(e.target.value)}
            placeholder="Enter city (e.g. Jaipur, Leh)"
            className="flex-1 px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
          <button
            type="submit"
            disabled={weatherLoading}
            className="py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            {weatherLoading ? 'Checking...' : 'Check Weather'}
          </button>
        </form>

        {weatherData && (
          <div className="space-y-3 pt-2">
            {/* AQI Badge */}
            {weatherData.air_quality && (
              <div className="p-3 rounded-md bg-slate-950 border border-slate-800 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <Wind className="w-4 h-4 text-brand-400" />
                  <span className="text-slate-300">Air Quality Level:</span>
                  <strong className="text-white">{weatherData.air_quality.label || 'Moderate'}</strong>
                </div>
                {weatherData.air_quality.pm2_5_ug_m3 && (
                  <span className="text-slate-400 text-[11px]">
                    PM2.5: {weatherData.air_quality.pm2_5_ug_m3} µg/m³
                  </span>
                )}
              </div>
            )}

            {/* Forecast Days */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {weatherData.forecast?.map((f, idx) => (
                <div key={idx} className="p-3.5 rounded-md bg-slate-950 border border-slate-800 text-xs space-y-1">
                  <div className="font-semibold text-slate-200">{f.date}</div>
                  <div className="text-brand-300 font-medium">
                    {f.temp_min}°C to {f.temp_max}°C
                  </div>
                  <div className="text-slate-400 text-[11px] capitalize">{f.condition}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 2. Opening Hours and Closed Day Warning Card */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Clock className="w-4 h-4 text-brand-400" />
          <span>Opening Hours & Closed-Day Verification</span>
        </h2>

        <form onSubmit={handleHours} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <input
            type="text"
            required
            value={monument}
            onChange={(e) => setMonument(e.target.value)}
            placeholder="Attraction name (e.g. Taj Mahal)"
            className="px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
          <input
            type="text"
            required
            value={monumentCity}
            onChange={(e) => setMonumentCity(e.target.value)}
            placeholder="City (e.g. Agra)"
            className="px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
          <button
            type="submit"
            disabled={hoursLoading}
            className="py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            {hoursLoading ? 'Verifying...' : 'Verify Hours'}
          </button>
        </form>

        {hoursData && (
          <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-white text-sm">{hoursData.place || monument}</span>
              {hoursData.closed ? (
                <span className="px-2 py-0.5 rounded bg-red-950 border border-red-800 text-red-300 text-[10px] font-semibold">
                  Closed
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-300 text-[10px] font-semibold">
                  Open
                </span>
              )}
            </div>
            <p className="text-slate-300">Schedule: {hoursData.hours || 'Verify locally'}</p>
            {hoursData.warnings && hoursData.warnings.length > 0 && (
              <p className="text-amber-300 text-[11px] pt-1">{hoursData.warnings.join('. ')}</p>
            )}
          </div>
        )}
      </div>

      {/* 3. Near Me Finder */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <MapPin className="w-4 h-4 text-brand-400" />
          <span>Near Me Finder</span>
        </h2>

        <form onSubmit={handleNearMe} className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="nm-city">
              City / Base Area
            </label>
            <input
              id="nm-city"
              type="text"
              required
              value={nearCity}
              onChange={(e) => setNearCity(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="nm-cat">
              Category
            </label>
            <select
              id="nm-cat"
              value={nearCategory}
              onChange={(e) => setNearCategory(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            >
              <option value="attractions">Attractions & Sights</option>
              <option value="restaurants">Restaurants & Food</option>
              <option value="atm">Banks & ATMs</option>
              <option value="pharmacy">Pharmacies & Clinics</option>
              <option value="petrol">Petrol / Fuel Stations</option>
            </select>
          </div>

          <div className="flex items-center h-9">
            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={vegOnly}
                onChange={(e) => setVegOnly(e.target.checked)}
                className="w-4 h-4 rounded border-slate-800 bg-slate-950 text-brand-600 focus:ring-0"
              />
              <span>Pure Veg Only</span>
            </label>
          </div>

          <div>
            <button
              type="submit"
              disabled={nearLoading}
              className="w-full py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
            >
              {nearLoading ? 'Searching...' : 'Search Nearby'}
            </button>
          </div>
        </form>

        {nearData && nearData.results && (
          <div className="space-y-2 pt-2">
            {nearData.results.map((r, idx) => (
              <div key={idx} className="p-3.5 rounded-md bg-slate-950 border border-slate-800 text-xs flex items-center justify-between">
                <div>
                  <span className="font-semibold text-white">{r.name}</span>
                  {r.address && <p className="text-slate-400 text-[11px] mt-0.5">{r.address}</p>}
                </div>
                <div className="text-right">
                  <span className="text-brand-300 font-medium">{r.distance_km} km away</span>
                  {r.rating && <div className="text-[10px] text-slate-500">Rating: {r.rating}/5</div>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
