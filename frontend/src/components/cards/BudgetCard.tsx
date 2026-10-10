import React, { useState } from 'react';
import { 
  DollarSign, 
  TrendingDown, 
  ShieldCheck, 
  Sparkles, 
  ArrowRightLeft, 
  Check 
} from 'lucide-react';

export interface BudgetCategoryBreakdown {
  stay?: number;
  food?: number;
  local_transport?: number;
  transport_to_destination?: number;
  entry_fees?: number;
  shopping?: number;
  buffer?: number;
}

export interface BudgetEstimateItem {
  tier: string;
  total_inr: number;
  per_person_inr: number;
  per_person_per_day_inr: number;
  categories: BudgetCategoryBreakdown;
  last_verified?: string;
  assumptions?: string[];
}

export interface BudgetCardData {
  destination?: string | string[];
  days?: number;
  travelers?: number;
  total_inr?: number;
  estimates?: BudgetEstimateItem[];
  categories?: BudgetCategoryBreakdown;
  recommendation?: string;
  currency?: string;
}

interface BudgetCardProps {
  data: BudgetCardData;
  onSendChatMessage?: (prompt: string) => void;
}

export const BudgetCard: React.FC<BudgetCardProps> = ({ data, onSendChatMessage }) => {
  const [selectedCurrency, setSelectedCurrency] = useState('INR');
  const rates: Record<string, number> = {
    INR: 1,
    USD: 0.012,
    EUR: 0.011,
    GBP: 0.0095,
    AED: 0.044,
  };

  const destinationName = Array.isArray(data.destination) ? data.destination.join(', ') : data.destination || 'India';
  const days = data.days || 3;
  const travelers = data.travelers || 1;
  const estimates = data.estimates || [];

  const formatMoney = (inrVal: number) => {
    const converted = inrVal * (rates[selectedCurrency] || 1);
    if (selectedCurrency === 'INR') {
      return `₹${inrVal.toLocaleString('en-IN')}`;
    }
    return `${selectedCurrency} ${converted.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
  };

  return (
    <div className="w-full rounded-lg bg-slate-900 border border-slate-800 p-4 space-y-4 shadow-lg text-slate-100">
      {/* Card Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-emerald-950 border border-emerald-800 text-emerald-400 flex items-center justify-center">
            <DollarSign className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white capitalize">{destinationName} Budget Benchmark</h3>
            <span className="text-[11px] text-slate-400">
              {days} Days • {travelers} Traveler{travelers > 1 ? 's' : ''} • Grounded Estimates
            </span>
          </div>
        </div>

        {/* Currency Switcher */}
        <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-xs">
          <span className="text-[10px] text-slate-400 font-mono">Curr:</span>
          <select
            value={selectedCurrency}
            onChange={(e) => setSelectedCurrency(e.target.value)}
            className="bg-transparent text-slate-200 text-xs font-semibold focus:outline-none cursor-pointer"
          >
            <option value="INR" className="bg-slate-900">INR (₹)</option>
            <option value="USD" className="bg-slate-900">USD ($)</option>
            <option value="EUR" className="bg-slate-900">EUR (€)</option>
            <option value="GBP" className="bg-slate-900">GBP (£)</option>
            <option value="AED" className="bg-slate-900">AED (د.إ)</option>
          </select>
        </div>
      </div>

      {/* Tier Comparison Table */}
      {estimates.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="pb-2 font-medium">Tier</th>
                <th className="pb-2 font-medium">Approx Total</th>
                <th className="pb-2 font-medium">Per Person</th>
                <th className="pb-2 font-medium">Per Day</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {estimates.map((est, idx) => {
                const tierName = est.tier === 'backpacker' ? 'Budget' : est.tier === 'mid' ? 'Moderate' : 'Luxury';
                const isMid = est.tier === 'mid';
                return (
                  <tr key={idx} className={isMid ? 'bg-brand-950/20' : ''}>
                    <td className="py-2.5 font-medium text-white flex items-center gap-1.5">
                      <span>{tierName}</span>
                      {isMid && (
                        <span className="text-[9px] px-1 py-0.2 rounded bg-brand-600/30 text-brand-300">
                          Popular
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 font-bold text-slate-100">{formatMoney(est.total_inr)}</td>
                    <td className="py-2.5 text-slate-300">{formatMoney(est.per_person_inr)}</td>
                    <td className="py-2.5 text-slate-400">{formatMoney(est.per_person_per_day_inr)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : data.total_inr ? (
        <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-[11px] text-slate-400 block">Total Estimated Spend</span>
            <strong className="text-base text-white">{formatMoney(data.total_inr)}</strong>
          </div>
          {data.categories && (
            <div className="text-right text-[11px] text-slate-400">
              <span>Stay: {formatMoney(data.categories.stay || 0)}</span> • 
              <span> Food: {formatMoney(data.categories.food || 0)}</span>
            </div>
          )}
        </div>
      ) : null}

      {/* Action Prompts */}
      {onSendChatMessage && (
        <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center gap-1.5 text-xs">
          <span className="text-[11px] text-slate-400 mr-1">Ask Agent:</span>
          <button
            onClick={() => onSendChatMessage(`How can I reduce expenses for ${destinationName} under a strict budget?`)}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] transition-colors"
          >
            Reduce Expenses
          </button>
          <button
            onClick={() => onSendChatMessage(`Break down food and entry fees for ${destinationName}`)}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] transition-colors"
          >
            Food & Entry Fees
          </button>
        </div>
      )}
    </div>
  );
};
