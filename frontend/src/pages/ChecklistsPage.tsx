import React, { useState } from 'react';
import { 
  Luggage, 
  CheckSquare, 
  Square, 
  Calendar, 
  CheckCircle2, 
  Plus, 
  Loader2 
} from 'lucide-react';
import { apiGet } from '../api/client';

export const ChecklistsPage: React.FC = () => {
  // Packing List State
  const [packDest, setPackDest] = useState('Goa');
  const [packDays, setPackDays] = useState(4);
  const [packSeason, setPackSeason] = useState('winter');
  const [packActivities, setPackActivities] = useState('beach, swimming, nightlife');
  const [packingData, setPackingData] = useState<{
    categories?: Record<string, string[]>;
  } | null>(null);
  const [packChecked, setPackChecked] = useState<Record<string, boolean>>({});
  const [packLoading, setPackLoading] = useState(false);

  // Pre-Trip State
  const [preTripDest, setPreTripDest] = useState('Leh Ladakh');
  const [isInternational, setIsInternational] = useState(false);
  const [preTripData, setPreTripData] = useState<{
    timeline?: Record<string, string[]>;
  } | null>(null);
  const [preTripChecked, setPreTripChecked] = useState<Record<string, boolean>>({});
  const [preTripLoading, setPreTripLoading] = useState(false);

  const handlePacking = async (e: React.FormEvent) => {
    e.preventDefault();
    setPackLoading(true);
    try {
      const res = await apiGet<unknown>(
        `/tools/checklist/packing?destination=${encodeURIComponent(packDest)}&days=${packDays}&season=${packSeason}&activities=${encodeURIComponent(packActivities)}`
      );
      setPackingData(res as typeof packingData);
      setPackChecked({});
    } catch {
      setPackingData(null);
    } finally {
      setPackLoading(false);
    }
  };

  const handlePreTrip = async (e: React.FormEvent) => {
    e.preventDefault();
    setPreTripLoading(true);
    try {
      const res = await apiGet<unknown>(
        `/tools/checklist/pre-trip?destination=${encodeURIComponent(preTripDest)}&is_international=${isInternational}`
      );
      setPreTripData(res as typeof preTripData);
      setPreTripChecked({});
    } catch {
      setPreTripData(null);
    } finally {
      setPreTripLoading(false);
    }
  };

  const toggleItem = (key: string, isPreTrip = false) => {
    if (isPreTrip) {
      setPreTripChecked((prev) => ({ ...prev, [key]: !prev[key] }));
    } else {
      setPackChecked((prev) => ({ ...prev, [key]: !prev[key] }));
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Packing List & Pre-Trip Checklists</h1>
        <p className="mt-1 text-xs text-slate-400">
          Smart categorized packing recommendations and date-based pre-trip preparation timelines.
        </p>
      </div>

      {/* 1. Smart Packing List */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Luggage className="w-4 h-4 text-brand-400" />
          <span>Smart Packing List</span>
        </h2>

        <form onSubmit={handlePacking} className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="pack-dest">
              Destination
            </label>
            <input
              id="pack-dest"
              type="text"
              required
              value={packDest}
              onChange={(e) => setPackDest(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="pack-days">
              Days
            </label>
            <input
              id="pack-days"
              type="number"
              min={1}
              max={30}
              required
              value={packDays}
              onChange={(e) => setPackDays(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="pack-season">
              Season
            </label>
            <select
              id="pack-season"
              value={packSeason}
              onChange={(e) => setPackSeason(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            >
              <option value="summer">Summer (Hot / Sunny)</option>
              <option value="monsoon">Monsoon (Rainy / Humid)</option>
              <option value="winter">Winter (Cool / Cold)</option>
            </select>
          </div>

          <div>
            <button
              type="submit"
              disabled={packLoading}
              className="w-full py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
            >
              {packLoading ? 'Generating...' : 'Generate Packing List'}
            </button>
          </div>
        </form>

        {packingData && packingData.categories && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-3">
            {Object.entries(packingData.categories).map(([category, items]) => (
              <div key={category} className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                <span className="font-semibold text-white text-xs block capitalize border-b border-slate-900 pb-1.5">
                  {category.replace('_', ' ')}
                </span>
                <div className="space-y-1.5 pt-1">
                  {items.map((item, idx) => {
                    const itemKey = `${category}_${idx}`;
                    const checked = Boolean(packChecked[itemKey]);
                    return (
                      <div
                        key={idx}
                        onClick={() => toggleItem(itemKey, false)}
                        className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none"
                      >
                        {checked ? (
                          <CheckSquare className="w-4 h-4 text-emerald-400 shrink-0" />
                        ) : (
                          <Square className="w-4 h-4 text-slate-600 shrink-0" />
                        )}
                        <span className={checked ? 'line-through text-slate-500' : ''}>{item}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 2. Pre-Trip Timeline Checklist */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Calendar className="w-4 h-4 text-brand-400" />
          <span>Pre-Trip Timeline Checklist (T-30, T-7, T-1)</span>
        </h2>

        <form onSubmit={handlePreTrip} className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="pretrip-dest">
              Destination
            </label>
            <input
              id="pretrip-dest"
              type="text"
              required
              value={preTripDest}
              onChange={(e) => setPreTripDest(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div className="flex items-center h-9">
            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={isInternational}
                onChange={(e) => setIsInternational(e.target.checked)}
                className="w-4 h-4 rounded border-slate-800 bg-slate-950 text-brand-600 focus:ring-0"
              />
              <span>International Traveler (Passport/Visa)</span>
            </label>
          </div>

          <div>
            <button
              type="submit"
              disabled={preTripLoading}
              className="w-full py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
            >
              {preTripLoading ? 'Loading...' : 'Get Timeline'}
            </button>
          </div>
        </form>

        {preTripData && preTripData.timeline && (
          <div className="space-y-4 pt-3">
            {Object.entries(preTripData.timeline).map(([milestone, tasks]) => (
              <div key={milestone} className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between border-b border-slate-900 pb-1.5">
                  <span className="font-bold text-brand-300 text-xs">{milestone}</span>
                  <span className="text-[10px] text-slate-500">{tasks.length} tasks</span>
                </div>
                <div className="space-y-2 pt-1">
                  {tasks.map((task, idx) => {
                    const taskKey = `${milestone}_${idx}`;
                    const checked = Boolean(preTripChecked[taskKey]);
                    return (
                      <div
                        key={idx}
                        onClick={() => toggleItem(taskKey, true)}
                        className="flex items-start gap-2.5 text-xs text-slate-300 cursor-pointer select-none"
                      >
                        {checked ? (
                          <CheckSquare className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                        ) : (
                          <Square className="w-4 h-4 text-slate-600 mt-0.5 shrink-0" />
                        )}
                        <span className={checked ? 'line-through text-slate-500' : 'leading-relaxed'}>
                          {task}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
