import React, { useState } from 'react';
import { 
  Banknote, 
  DollarSign, 
  MapPin, 
  CreditCard, 
  ExternalLink, 
  Search, 
  Loader2 
} from 'lucide-react';
import { apiGet } from '../api/client';

export const FairPricingPage: React.FC = () => {
  // Entry Fees State
  const [monumentName, setMonumentName] = useState('Taj Mahal');
  const [feeData, setFeeData] = useState<{
    place?: string;
    indian_entry_inr?: number;
    foreign_entry_inr?: number;
    free_days?: string[];
    source_url?: string;
    last_verified?: string;
  } | null>(null);
  const [feeLoading, setFeeLoading] = useState(false);

  // Fair Prices State
  const [fairCity, setFairCity] = useState('Jaipur');
  const [priceData, setPriceData] = useState<{
    city?: string;
    transport?: Record<string, string>;
    meals?: Record<string, string>;
    bargaining_tips?: string;
    last_verified?: string;
  } | null>(null);
  const [priceLoading, setPriceLoading] = useState(false);

  // ATM State
  const [atmCity, setAtmCity] = useState('Jaipur');
  const [atmData, setAtmData] = useState<{
    general?: string;
    city_note?: string;
  } | null>(null);
  const [atmLoading, setAtmLoading] = useState(false);

  const handleFee = async (e: React.FormEvent) => {
    e.preventDefault();
    setFeeLoading(true);
    try {
      const res = await apiGet<unknown>(`/tools/budget/entry-fees?place=${encodeURIComponent(monumentName)}`);
      setFeeData(res as typeof feeData);
    } catch {
      setFeeData(null);
    } finally {
      setFeeLoading(false);
    }
  };

  const handlePrices = async (e: React.FormEvent) => {
    e.preventDefault();
    setPriceLoading(true);
    try {
      const res = await apiGet<unknown>(`/tools/budget/fair-prices?city=${encodeURIComponent(fairCity)}`);
      setPriceData(res as typeof priceData);
    } catch {
      setPriceData(null);
    } finally {
      setPriceLoading(false);
    }
  };

  const handleAtm = async (e: React.FormEvent) => {
    e.preventDefault();
    setAtmLoading(true);
    try {
      const res = await apiGet<unknown>(`/tools/budget/atm?city=${encodeURIComponent(atmCity)}`);
      setAtmData(res as typeof atmData);
    } catch {
      setAtmData(null);
    } finally {
      setAtmLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Entry Fees, Fair Prices & ATM Guide</h1>
        <p className="mt-1 text-xs text-slate-400">
          Official Archaeological Survey of India (ASI) ticket rates, auto-rickshaw meter benchmarks, and money safety tips.
        </p>
      </div>

      {/* 1. Monument Entry Fees */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Banknote className="w-4 h-4 text-brand-400" />
          <span>Monument Entry Fees & Free Days</span>
        </h2>

        <form onSubmit={handleFee} className="flex gap-3 max-w-md">
          <input
            type="text"
            required
            value={monumentName}
            onChange={(e) => setMonumentName(e.target.value)}
            placeholder="Monument (e.g. Taj Mahal, Red Fort)"
            className="flex-1 px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
          <button
            type="submit"
            disabled={feeLoading}
            className="py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            {feeLoading ? 'Looking up...' : 'Lookup Fee'}
          </button>
        </form>

        {feeData && (
          <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs space-y-2">
            <div className="flex items-center justify-between border-b border-slate-900 pb-2">
              <span className="font-bold text-white text-sm">{feeData.place || monumentName}</span>
              {feeData.source_url && (
                <a
                  href={feeData.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand-400 hover:underline flex items-center gap-1 text-[11px]"
                >
                  <span>Official ASI Source</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4 pt-1">
              <div>
                <span className="text-slate-400 block">Indian Citizens:</span>
                <strong className="text-white text-sm">
                  {feeData.indian_entry_inr !== undefined ? `₹${feeData.indian_entry_inr}` : 'Verify locally'}
                </strong>
              </div>
              <div>
                <span className="text-slate-400 block">Foreign Tourists:</span>
                <strong className="text-white text-sm">
                  {feeData.foreign_entry_inr !== undefined ? `₹${feeData.foreign_entry_inr}` : 'Verify locally'}
                </strong>
              </div>
            </div>

            {feeData.free_days && feeData.free_days.length > 0 && (
              <p className="text-slate-400 text-[11px] pt-1">
                Free entry days: {feeData.free_days.join(', ')}
              </p>
            )}
          </div>
        )}
      </div>

      {/* 2. City Fair Price Benchmarks */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <DollarSign className="w-4 h-4 text-brand-400" />
          <span>City Transport & Meal Fair Prices</span>
        </h2>

        <form onSubmit={handlePrices} className="flex gap-3 max-w-md">
          <input
            type="text"
            required
            value={fairCity}
            onChange={(e) => setFairCity(e.target.value)}
            placeholder="City (e.g. Jaipur, Varanasi)"
            className="flex-1 px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
          <button
            type="submit"
            disabled={priceLoading}
            className="py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            {priceLoading ? 'Loading...' : 'Check Benchmarks'}
          </button>
        </form>

        {priceData && (
          <div className="space-y-4 pt-2">
            {priceData.transport && (
              <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs space-y-2">
                <strong className="text-white block font-semibold">Transport Reference Ranges:</strong>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-300">
                  {Object.entries(priceData.transport).map(([k, v]) => (
                    <div key={k} className="flex justify-between border-b border-slate-900 pb-1">
                      <span className="capitalize text-slate-400">{k}:</span>
                      <span>{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {priceData.bargaining_tips && (
              <div className="p-3.5 rounded-md bg-slate-950 border border-slate-800 text-xs text-slate-300">
                <strong className="text-slate-200 block mb-1">Bargaining & Payment Advice:</strong>
                <p className="text-[11px] text-slate-400 leading-relaxed">{priceData.bargaining_tips}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 3. ATM & Cash Guide */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <CreditCard className="w-4 h-4 text-brand-400" />
          <span>ATM Availability & Currency Safety</span>
        </h2>

        <form onSubmit={handleAtm} className="flex gap-3 max-w-md">
          <input
            type="text"
            value={atmCity}
            onChange={(e) => setAtmCity(e.target.value)}
            placeholder="City (e.g. Leh, Goa)"
            className="flex-1 px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
          <button
            type="submit"
            disabled={atmLoading}
            className="py-2 px-4 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors cursor-pointer"
          >
            {atmLoading ? 'Loading...' : 'Check ATM Tips'}
          </button>
        </form>

        {atmData && (
          <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs space-y-2 text-slate-300">
            {atmData.general && <p className="leading-relaxed">{atmData.general}</p>}
            {atmData.city_note && (
              <div className="p-2.5 rounded bg-brand-950/40 border border-brand-800/60 text-brand-200 text-[11px]">
                <strong>City Notice ({atmCity}):</strong> {atmData.city_note}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
