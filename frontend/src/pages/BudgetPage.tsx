import React, { useState } from 'react';
import { 
  DollarSign, 
  Banknote, 
  ArrowRightLeft, 
  AlertCircle, 
  CheckCircle2, 
  Calculator, 
  Loader2 
} from 'lucide-react';
import { apiGet, apiPost } from '../api/client';

interface BudgetTier {
  tier: string;
  total_inr: number;
  per_person_inr: number;
  per_person_per_day_inr: number;
  categories: {
    transport_to_destination: number;
    stay: number;
    food: number;
    local_transport: number;
    entry_fees: number;
    shopping: number;
    buffer: number;
  };
}

interface BudgetComparison {
  estimates: BudgetTier[];
  recommendation?: string;
  assumptions?: string[];
  last_verified?: string;
}

export const BudgetPage: React.FC = () => {
  const [destination, setDestination] = useState('Jaipur');
  const [days, setDays] = useState(3);
  const [travelers, setTravelers] = useState(1);
  const [data, setData] = useState<BudgetComparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Currency Converter State
  const [convAmount, setConvAmount] = useState(100);
  const [fromCurr, setFromCurr] = useState('USD');
  const [toCurr, setToCurr] = useState('INR');
  const [convResult, setConvResult] = useState<{ converted_amount?: number; rate?: number } | null>(null);
  const [convLoading, setConvLoading] = useState(false);

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await apiGet<BudgetComparison>(
        `/tools/budget/tiers?destination=${encodeURIComponent(destination)}&days=${days}&travelers=${travelers}`
      );
      if ('error' in res) {
        setError(String(res.error));
      } else {
        setData(res);
      }
    } catch {
      setError('Could not calculate budget tiers');
    } finally {
      setLoading(false);
    }
  };

  const handleConvert = async (e: React.FormEvent) => {
    e.preventDefault();
    setConvLoading(true);

    try {
      const res = await apiGet<{ converted_amount?: number; rate?: number }>(
        `/tools/budget/currency?amount=${convAmount}&from_curr=${fromCurr}&to_curr=${toCurr}`
      );
      setConvResult(res);
    } catch {
      setConvResult(null);
    } finally {
      setConvLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Trip Budget Estimator</h1>
        <p className="mt-1 text-xs text-slate-400">
          Deterministic 3-tier travel cost benchmarks computed in Python arithmetic.
        </p>
      </div>

      {error && (
        <div className="p-3.5 rounded-md bg-red-950/60 border border-red-900 text-red-200 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Input Parameters */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800">
        <form onSubmit={handleCalculate} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="budget-dest">
              Destination City
            </label>
            <input
              id="budget-dest"
              type="text"
              required
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="e.g. Jaipur, Goa, Leh"
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="budget-days">
              Duration (Days)
            </label>
            <input
              id="budget-days"
              type="number"
              min={1}
              max={30}
              required
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="budget-travelers">
              Travelers
            </label>
            <input
              id="budget-travelers"
              type="number"
              min={1}
              max={20}
              required
              value={travelers}
              onChange={(e) => setTravelers(Number(e.target.value))}
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
                  <span>Computing...</span>
                </>
              ) : (
                <>
                  <Calculator className="w-4 h-4" />
                  <span>Compare Tiers</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Comparison Cards */}
      {data && data.estimates && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {data.estimates.map((tier) => {
              const tierName = tier.tier.charAt(0).toUpperCase() + tier.tier.slice(1);
              const isMid = tier.tier === 'mid';
              return (
                <div
                  key={tier.tier}
                  className={`p-6 rounded-lg border flex flex-col justify-between ${
                    isMid
                      ? 'bg-slate-900 border-brand-500/60 shadow-lg shadow-brand-950/30'
                      : 'bg-slate-900 border-slate-800'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                        {tierName}
                      </span>
                      {isMid && (
                        <span className="px-2 py-0.5 rounded bg-brand-950 border border-brand-800 text-brand-300 text-[10px] font-medium">
                          Recommended
                        </span>
                      )}
                    </div>

                    <div className="mb-6">
                      <div className="text-2xl font-bold text-white">
                        ₹{tier.total_inr.toLocaleString()}
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        ₹{tier.per_person_per_day_inr.toLocaleString()} / person / day
                      </div>
                    </div>

                    {/* Breakdown List */}
                    <div className="space-y-2 text-xs border-t border-slate-800 pt-4 text-slate-300">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Stay:</span>
                        <span>₹{tier.categories.stay.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Food:</span>
                        <span>₹{tier.categories.food.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Transit to City:</span>
                        <span>₹{tier.categories.transport_to_destination.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Local Transport:</span>
                        <span>₹{tier.categories.local_transport.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Entry Fees:</span>
                        <span>₹{tier.categories.entry_fees.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Buffer (12%):</span>
                        <span>₹{tier.categories.buffer.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 pt-4 border-t border-slate-800 text-[11px] text-slate-500">
                    Per-person total: ₹{tier.per_person_inr.toLocaleString()}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Assumptions Notice */}
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-400 space-y-1">
            <strong className="text-slate-200 block">Pricing Assumptions & Source:</strong>
            <p className="text-[11px] leading-relaxed">
              {data.recommendation} Verified benchmarks last updated: {data.last_verified || '2024-10'}.
            </p>
          </div>
        </div>
      )}

      {/* Currency Converter Utility */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Banknote className="w-4 h-4 text-brand-400" />
          <span>Real-time Currency Converter</span>
        </h2>

        <form onSubmit={handleConvert} className="grid grid-cols-1 sm:grid-cols-4 gap-4 items-end">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="conv-amt">
              Amount
            </label>
            <input
              id="conv-amt"
              type="number"
              min={1}
              required
              value={convAmount}
              onChange={(e) => setConvAmount(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="from-curr">
              From Currency
            </label>
            <select
              id="from-curr"
              value={fromCurr}
              onChange={(e) => setFromCurr(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            >
              <option value="USD">USD ($)</option>
              <option value="EUR">EUR (€)</option>
              <option value="GBP">GBP (£)</option>
              <option value="AUD">AUD (A$)</option>
              <option value="SGD">SGD (S$)</option>
              <option value="CAD">CAD (C$)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="to-curr">
              To Currency
            </label>
            <select
              id="to-curr"
              value={toCurr}
              onChange={(e) => setToCurr(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            >
              <option value="INR">INR (₹)</option>
              <option value="USD">USD ($)</option>
              <option value="EUR">EUR (€)</option>
            </select>
          </div>

          <div>
            <button
              type="submit"
              disabled={convLoading}
              className="w-full py-2 px-4 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center justify-center gap-2 cursor-pointer transition-colors"
            >
              <ArrowRightLeft className="w-3.5 h-3.5" />
              <span>Convert</span>
            </button>
          </div>
        </form>

        {convResult && convResult.converted_amount && (
          <div className="p-3.5 rounded-md bg-slate-950 border border-slate-800 text-xs flex items-center justify-between">
            <span className="text-slate-400">
              {convAmount} {fromCurr} =
            </span>
            <strong className="text-white text-sm">
              {convResult.converted_amount.toLocaleString()} {toCurr}
            </strong>
          </div>
        )}
      </div>
    </div>
  );
};
