import React, { useState } from 'react';
import { 
  Utensils, 
  Compass, 
  BookOpen, 
  ShieldCheck, 
  Search, 
  AlertCircle, 
  Loader2 
} from 'lucide-react';
import { apiGet } from '../api/client';

export const CultureFoodPage: React.FC = () => {
  // Food Guide State
  const [foodCity, setFoodCity] = useState('Jaipur');
  const [dietFilter, setDietFilter] = useState('');
  const [foodData, setFoodData] = useState<{
    city?: string;
    must_try_dishes?: Array<{ name: string; description: string; type: string }>;
    street_food_tips?: string[];
  } | null>(null);
  const [foodLoading, setFoodLoading] = useState(false);

  // Temple Guide State
  const [templeSite, setTempleSite] = useState('Golden Temple');
  const [templeData, setTempleData] = useState<{
    site?: string;
    dress_code?: string;
    rules?: string[];
    customs?: string[];
  } | null>(null);
  const [templeLoading, setTempleLoading] = useState(false);

  // Etiquette State
  const [etiquetteState, setEtiquetteState] = useState('Rajasthan');
  const [etiquetteData, setEtiquetteData] = useState<{
    general_customs?: string[];
    tipping?: string;
    social_norms?: string[];
  } | null>(null);
  const [etiquetteLoading, setEtiquetteLoading] = useState(false);

  const handleFood = async (e: React.FormEvent) => {
    e.preventDefault();
    setFoodLoading(true);
    try {
      const res = await apiGet<unknown>(
        `/tools/knowledge/food?city=${encodeURIComponent(foodCity)}&diet_filter=${encodeURIComponent(dietFilter)}`
      );
      setFoodData(res as typeof foodData);
    } catch {
      setFoodData(null);
    } finally {
      setFoodLoading(false);
    }
  };

  const handleTemple = async (e: React.FormEvent) => {
    e.preventDefault();
    setTempleLoading(true);
    try {
      const res = await apiGet<unknown>(
        `/tools/knowledge/temple?site_or_city=${encodeURIComponent(templeSite)}`
      );
      setTempleData(res as typeof templeData);
    } catch {
      setTempleData(null);
    } finally {
      setTempleLoading(false);
    }
  };

  const handleEtiquette = async (e: React.FormEvent) => {
    e.preventDefault();
    setEtiquetteLoading(true);
    try {
      const res = await apiGet<unknown>(
        `/tools/knowledge/etiquette?state_or_religion=${encodeURIComponent(etiquetteState)}`
      );
      setEtiquetteData(res as typeof etiquetteData);
    } catch {
      setEtiquetteData(null);
    } finally {
      setEtiquetteLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Food, Temple Customs & Local Etiquette</h1>
        <p className="mt-1 text-xs text-slate-400">
          Regional food specialties with dietary filters, religious site dress codes, and respectful social norms.
        </p>
      </div>

      {/* 1. Regional Food Guide */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Utensils className="w-4 h-4 text-brand-400" />
          <span>Regional Food Guide with Dietary Filters</span>
        </h2>

        <form onSubmit={handleFood} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <input
            type="text"
            required
            value={foodCity}
            onChange={(e) => setFoodCity(e.target.value)}
            placeholder="City (e.g. Jaipur, Kolkata, Goa)"
            className="px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
          <select
            value={dietFilter}
            onChange={(e) => setDietFilter(e.target.value)}
            className="px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          >
            <option value="">All Dietary Styles</option>
            <option value="veg">Pure Vegetarian</option>
            <option value="vegan">Vegan</option>
            <option value="jain">Jain (No Root Veg)</option>
            <option value="halal">Halal</option>
          </select>
          <button
            type="submit"
            disabled={foodLoading}
            className="py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            {foodLoading ? 'Finding dishes...' : 'Find Food'}
          </button>
        </form>

        {foodData && (
          <div className="space-y-3 pt-2">
            {foodData.must_try_dishes && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {foodData.must_try_dishes.map((dish, i) => (
                  <div key={i} className="p-3.5 rounded-md bg-slate-950 border border-slate-800 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white text-sm">{dish.name}</span>
                      <span className="px-1.5 py-0.5 rounded bg-slate-800 text-brand-300 text-[10px]">
                        {dish.type}
                      </span>
                    </div>
                    <p className="text-slate-400 text-[11px] leading-relaxed">{dish.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 2. Temple & Religious Site Guide */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Compass className="w-4 h-4 text-amber-400" />
          <span>Temple, Mosque & Gurudwara Etiquette</span>
        </h2>

        <form onSubmit={handleTemple} className="flex gap-3 max-w-md">
          <input
            type="text"
            required
            value={templeSite}
            onChange={(e) => setTempleSite(e.target.value)}
            placeholder="Temple / site (e.g. Golden Temple, Tirupati)"
            className="flex-1 px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
          <button
            type="submit"
            disabled={templeLoading}
            className="py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            {templeLoading ? 'Loading...' : 'Check Customs'}
          </button>
        </form>

        {templeData && (
          <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs space-y-3">
            {templeData.dress_code && (
              <div>
                <strong className="text-white block mb-0.5">Dress Code Requirements:</strong>
                <p className="text-slate-300">{templeData.dress_code}</p>
              </div>
            )}
            {templeData.rules && (
              <div>
                <strong className="text-white block mb-0.5">Key Regulations:</strong>
                <ul className="list-disc pl-4 space-y-0.5 text-slate-400">
                  {templeData.rules.map((r, idx) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 3. Regional Social Norms & Tipping */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-emerald-400" />
          <span>State Etiquette & Tipping Customs</span>
        </h2>

        <form onSubmit={handleEtiquette} className="flex gap-3 max-w-md">
          <input
            type="text"
            required
            value={etiquetteState}
            onChange={(e) => setEtiquetteState(e.target.value)}
            placeholder="State (e.g. Rajasthan, Kerala, Ladakh)"
            className="flex-1 px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
          <button
            type="submit"
            disabled={etiquetteLoading}
            className="py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            {etiquetteLoading ? 'Loading...' : 'Check Etiquette'}
          </button>
        </form>

        {etiquetteData && (
          <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs space-y-3">
            {etiquetteData.tipping && (
              <div>
                <strong className="text-white block mb-0.5">Tipping Benchmark:</strong>
                <p className="text-slate-300">{etiquetteData.tipping}</p>
              </div>
            )}
            {etiquetteData.general_customs && (
              <div>
                <strong className="text-white block mb-0.5">Social Norms:</strong>
                <ul className="list-disc pl-4 space-y-0.5 text-slate-400">
                  {etiquetteData.general_customs.map((c, idx) => (
                    <li key={idx}>{c}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
