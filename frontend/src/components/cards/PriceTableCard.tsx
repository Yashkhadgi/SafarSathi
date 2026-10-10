import React from 'react';
import { 
  BadgeIndianRupee, 
  Landmark, 
  Info, 
  ShieldCheck, 
  ExternalLink 
} from 'lucide-react';

export interface PriceTableItem {
  label: string;
  price_inr: string;
  foreign_price_inr?: string;
  free_days?: string;
  source_url?: string;
  last_verified?: string;
}

export interface PriceTableData {
  city_or_place: string;
  kind?: string;
  items: PriceTableItem[];
  disclaimer?: string;
}

interface PriceTableCardProps {
  data: PriceTableData;
  onSendMessage?: (message: string) => void;
}

export const PriceTableCard: React.FC<PriceTableCardProps> = ({ data, onSendMessage }) => {
  const isMonument = data.kind === 'monument_entry' || data.items?.some(i => i.foreign_price_inr && i.foreign_price_inr !== 'verify');

  return (
    <div className="w-full my-3 rounded-lg border border-slate-700 bg-slate-900 text-slate-100 shadow-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-slate-800/80 border-b border-slate-700 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-amber-600/20 text-amber-400 border border-amber-500/30">
            {isMonument ? <Landmark className="w-4 h-4" /> : <BadgeIndianRupee className="w-4 h-4" />}
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100 capitalize">
              {data.city_or_place} {isMonument ? 'Monument Entry Fees' : 'Fair Price Guide'}
            </h4>
            <p className="text-[11px] text-slate-400">Official ASI & transport pricing benchmarks</p>
          </div>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
          {data.items?.length || 0} Entries
        </span>
      </div>

      {/* Table Content */}
      <div className="p-4 space-y-3">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-700 text-slate-400">
                <th className="py-2 px-2 font-medium">Item / Monument</th>
                <th className="py-2 px-2 font-medium">{isMonument ? 'Indian Price' : 'Approx Fare / Rate'}</th>
                {isMonument && <th className="py-2 px-2 font-medium">Foreign Tourist</th>}
                <th className="py-2 px-2 font-medium">Notes / Free Days</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {data.items?.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-2.5 px-2 font-medium text-slate-200">{item.label}</td>
                  <td className="py-2.5 px-2 font-mono text-emerald-400 font-medium">
                    {item.price_inr.startsWith('₹') || item.price_inr.startsWith('INR') ? item.price_inr : `₹${item.price_inr}`}
                  </td>
                  {isMonument && (
                    <td className="py-2.5 px-2 font-mono text-sky-300">
                      {item.foreign_price_inr ? (item.foreign_price_inr.startsWith('₹') ? item.foreign_price_inr : `₹${item.foreign_price_inr}`) : 'verify'}
                    </td>
                  )}
                  <td className="py-2.5 px-2 text-slate-400 text-[11px]">
                    {item.free_days || 'Check at entrance'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Disclaimer */}
        {data.disclaimer && (
          <div className="p-2.5 rounded-md bg-slate-800/50 border border-slate-700/60 flex items-start gap-2 text-[11px] text-slate-400">
            <Info className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
            <span>{data.disclaimer}</span>
          </div>
        )}

        {/* Follow-up Prompts */}
        {onSendMessage && (
          <div className="pt-2 flex flex-wrap gap-2">
            <button
              onClick={() => onSendMessage(`What is the fair auto rickshaw fare from airport/station in ${data.city_or_place}?`)}
              className="px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
            >
              Auto & taxi rates
            </button>
            <button
              onClick={() => onSendMessage(`How to avoid tourist overcharging and scams in ${data.city_or_place}?`)}
              className="px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
            >
              Scam & safety tips
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
