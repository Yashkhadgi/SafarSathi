import React, { useState } from 'react';
import { 
  Compass, 
  Map, 
  CloudRain, 
  Calendar, 
  DollarSign, 
  Sparkles, 
  ArrowRight, 
  Loader2 
} from 'lucide-react';
import { apiGet, apiPost } from '../api/client';

export const PlanningOptimizerPage: React.FC = () => {
  // Multi-City Optimizer State
  const [citiesInput, setCitiesInput] = useState('Jaipur, Jodhpur, Udaipur');
  const [originCity, setOriginCity] = useState('Delhi');
  const [totalDays, setTotalDays] = useState(7);
  const [optData, setOptData] = useState<{
    ordered_cities?: string[];
    total_km?: number;
    day_allocation?: Record<string, number>;
    inter_city_legs?: Array<{ from: string; to: string; distance_km: number; travel_time_hours?: string }>;
  } | null>(null);
  const [optLoading, setOptLoading] = useState(false);

  // Destination Recommender State
  const [recBudget, setRecBudget] = useState(20000);
  const [recDays, setRecDays] = useState(4);
  const [recMonth, setRecMonth] = useState('November');
  const [recMood, setRecMood] = useState('heritage');
  const [recOrigin, setRecOrigin] = useState('Delhi');
  const [recData, setRecData] = useState<{
    recommendations?: Array<{ destination: string; score: number; match_reason: string; approx_cost_inr: number }>;
  } | null>(null);
  const [recLoading, setRecLoading] = useState(false);

  // Best Time State
  const [bestPlace, setBestPlace] = useState('Goa');
  const [bestData, setBestData] = useState<{
    place?: string;
    best_months?: string[];
    off_season?: string[];
    crowd_advice?: string;
  } | null>(null);
  const [bestLoading, setBestLoading] = useState(false);

  const handleOptimize = async (e: React.FormEvent) => {
    e.preventDefault();
    setOptLoading(true);
    const cities = citiesInput.split(',').map((c) => c.trim()).filter(Boolean);
    try {
      const res = await apiPost<unknown>('/tools/optimizer/route', {
        cities,
        origin: originCity,
        total_days: Number(totalDays),
      });
      setOptData(res as typeof optData);
    } catch {
      setOptData(null);
    } finally {
      setOptLoading(false);
    }
  };

  const handleRecommend = async (e: React.FormEvent) => {
    e.preventDefault();
    setRecLoading(true);
    try {
      const res = await apiGet<unknown>(
        `/tools/recommender/destinations?budget_inr=${recBudget}&days=${recDays}&month=${recMonth}&mood=${recMood}&origin_city=${recOrigin}`
      );
      setRecData(res as typeof recData);
    } catch {
      setRecData(null);
    } finally {
      setRecLoading(false);
    }
  };

  const handleBestTime = async (e: React.FormEvent) => {
    e.preventDefault();
    setBestLoading(true);
    try {
      const res = await apiGet<unknown>(
        `/tools/recommender/best-time?place=${encodeURIComponent(bestPlace)}`
      );
      setBestData(res as typeof bestData);
    } catch {
      setBestData(null);
    } finally {
      setBestLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Route Optimizer & Destination Recommender</h1>
        <p className="mt-1 text-xs text-slate-400">
          Multi-city traveling salesperson optimizer (TSP with Haversine math) and deterministic destination scoring.
        </p>
      </div>

      {/* 1. Multi-City Route Optimizer */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Map className="w-4 h-4 text-brand-400" />
          <span>Multi-City Circuit Route Optimizer</span>
        </h2>

        <form onSubmit={handleOptimize} className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="opt-cities">
              Cities to Visit (Comma separated)
            </label>
            <input
              id="opt-cities"
              type="text"
              required
              value={citiesInput}
              onChange={(e) => setCitiesInput(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="opt-origin">
              Origin / Starting Point
            </label>
            <input
              id="opt-origin"
              type="text"
              required
              value={originCity}
              onChange={(e) => setOriginCity(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="opt-days">
              Total Trip Days
            </label>
            <input
              id="opt-days"
              type="number"
              min={3}
              max={30}
              required
              value={totalDays}
              onChange={(e) => setTotalDays(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={optLoading}
              className="w-full py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
            >
              {optLoading ? 'Optimizing...' : 'Optimize Circuit'}
            </button>
          </div>
        </form>

        {optData && (
          <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-900 pb-2">
              <span className="font-semibold text-white">Recommended Order:</span>
              <span className="text-brand-300 font-medium">Approx {optData.total_km || 0} km circuit</span>
            </div>

            {optData.ordered_cities && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 font-semibold">{originCity}</span>
                {optData.ordered_cities.map((city, idx) => (
                  <React.Fragment key={idx}>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                    <span className="px-2.5 py-1 rounded bg-brand-950 border border-brand-800 text-brand-200 font-semibold">
                      {city} {optData.day_allocation?.[city] ? `(${optData.day_allocation[city]} days)` : ''}
                    </span>
                  </React.Fragment>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 2. Destination Recommender */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-brand-400" />
          <span>Destination Recommender (Scoring Engine)</span>
        </h2>

        <form onSubmit={handleRecommend} className="grid grid-cols-1 sm:grid-cols-5 gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="rec-budget">
              Budget (INR)
            </label>
            <input
              id="rec-budget"
              type="number"
              min={5000}
              step={1000}
              value={recBudget}
              onChange={(e) => setRecBudget(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="rec-days">
              Days
            </label>
            <input
              id="rec-days"
              type="number"
              min={2}
              max={15}
              value={recDays}
              onChange={(e) => setRecDays(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="rec-mood">
              Mood / Style
            </label>
            <select
              id="rec-mood"
              value={recMood}
              onChange={(e) => setRecMood(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            >
              <option value="heritage">Heritage & Palaces</option>
              <option value="spiritual">Spiritual & Temples</option>
              <option value="beach">Beaches & Coastal</option>
              <option value="nature">Nature & Mountains</option>
              <option value="adventure">Adventure & Trekking</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="rec-month">
              Travel Month
            </label>
            <select
              id="rec-month"
              value={recMonth}
              onChange={(e) => setRecMonth(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            >
              <option value="October">October</option>
              <option value="November">November</option>
              <option value="December">December</option>
              <option value="January">January</option>
              <option value="February">February</option>
              <option value="March">March</option>
            </select>
          </div>

          <div>
            <button
              type="submit"
              disabled={recLoading}
              className="w-full py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
            >
              {recLoading ? 'Scoring...' : 'Find Matches'}
            </button>
          </div>
        </form>

        {recData && recData.recommendations && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            {recData.recommendations.map((rec, i) => (
              <div key={i} className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-sm">{rec.destination}</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 text-[10px] font-semibold">
                    Score: {rec.score}
                  </span>
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed">{rec.match_reason}</p>
                {rec.approx_cost_inr && (
                  <div className="text-brand-300 text-[11px] pt-1 border-t border-slate-900">
                    Est: ₹{rec.approx_cost_inr.toLocaleString()}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 3. Best Time to Visit */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Calendar className="w-4 h-4 text-brand-400" />
          <span>Best Time to Visit & Crowd Guidance</span>
        </h2>

        <form onSubmit={handleBestTime} className="flex gap-3 max-w-md">
          <input
            type="text"
            required
            value={bestPlace}
            onChange={(e) => setBestPlace(e.target.value)}
            placeholder="Destination (e.g. Goa, Ladakh, Varanasi)"
            className="flex-1 px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
          <button
            type="submit"
            disabled={bestLoading}
            className="py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            {bestLoading ? 'Checking...' : 'Check Season'}
          </button>
        </form>

        {bestData && (
          <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs space-y-2">
            <span className="font-bold text-white block">{bestData.place || bestPlace}</span>
            {bestData.best_months && (
              <p className="text-emerald-300">
                <strong>Peak Season:</strong> {bestData.best_months.join(', ')}
              </p>
            )}
            {bestData.crowd_advice && (
              <p className="text-slate-300 leading-relaxed pt-1">{bestData.crowd_advice}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
