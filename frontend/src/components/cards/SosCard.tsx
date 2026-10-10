import React from 'react';
import { 
  ShieldAlert, 
  PhoneCall, 
  AlertTriangle, 
  MapPin, 
  HeartHandshake, 
  ExternalLink 
} from 'lucide-react';

export interface SosCardData {
  city?: string;
  safety_tips?: string;
  symptom?: string;
  guidance?: string;
  emergency_numbers?: Record<string, string>;
  source?: string;
  source_url?: string;
  last_verified?: string;
}

interface SosCardProps {
  data: SosCardData;
  onSendChatMessage?: (prompt: string) => void;
}

export const SosCard: React.FC<SosCardProps> = ({ data, onSendChatMessage }) => {
  const numbers = data.emergency_numbers || {
    national_emergency: '112',
    ambulance: '108',
    tourist_police: '1363',
    women_helpline: '1091',
  };

  return (
    <div className="w-full rounded-lg bg-red-950/30 border border-red-900/80 p-4 space-y-4 shadow-lg text-slate-100">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-red-900/60 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-red-900 border border-red-700 text-white flex items-center justify-center animate-pulse">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-red-200">
              {data.city ? `${data.city} Emergency & Safety Support` : 'Emergency Assistance'}
            </h3>
            <span className="text-[11px] text-red-300/80">
              Immediate national emergency hotlines & verified guidance
            </span>
          </div>
        </div>
      </div>

      {/* 1-Tap Emergency Hotlines */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <a
          href="tel:112"
          className="p-2.5 rounded-md bg-red-900/80 hover:bg-red-800 border border-red-700 text-white flex flex-col items-center justify-center text-center transition-colors font-bold shadow"
        >
          <PhoneCall className="w-4 h-4 mb-1" />
          <span className="text-sm">112</span>
          <span className="text-[10px] font-normal text-red-200">National Emergency</span>
        </a>

        <a
          href="tel:108"
          className="p-2.5 rounded-md bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-100 flex flex-col items-center justify-center text-center transition-colors"
        >
          <PhoneCall className="w-4 h-4 mb-1 text-emerald-400" />
          <span className="text-sm font-bold">108</span>
          <span className="text-[10px] text-slate-400">Ambulance</span>
        </a>

        <a
          href="tel:1091"
          className="p-2.5 rounded-md bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-100 flex flex-col items-center justify-center text-center transition-colors"
        >
          <PhoneCall className="w-4 h-4 mb-1 text-purple-400" />
          <span className="text-sm font-bold">1091</span>
          <span className="text-[10px] text-slate-400">Women Helpline</span>
        </a>

        <a
          href="tel:1363"
          className="p-2.5 rounded-md bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-100 flex flex-col items-center justify-center text-center transition-colors"
        >
          <PhoneCall className="w-4 h-4 mb-1 text-amber-400" />
          <span className="text-sm font-bold">1363</span>
          <span className="text-[10px] text-slate-400">Tourist Police</span>
        </a>
      </div>

      {/* Safety or Medical Guidance Text */}
      {(data.safety_tips || data.guidance) && (
        <div className="p-3 rounded-md bg-slate-950 border border-slate-800 text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
          {data.safety_tips || data.guidance}
        </div>
      )}

      {/* Disclaimer */}
      <div className="p-2 rounded bg-red-950/60 border border-red-900/40 text-[10px] text-red-300 flex items-start gap-2">
        <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-red-400" />
        <span>
          Medical & legal notices are for general orientation only. Consult a doctor or local authorities. No medicine dosages are provided.
        </span>
      </div>

      {/* Action Prompts */}
      {onSendChatMessage && (
        <div className="pt-2 border-t border-red-900/40 flex flex-wrap items-center gap-1.5 text-xs">
          <button
            onClick={() => onSendChatMessage(`Find nearest government hospital in ${data.city || 'my location'}`)}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] transition-colors"
          >
            Nearest Hospital
          </button>
          <button
            onClick={() => onSendChatMessage(`How to report a lost passport or document in India?`)}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] transition-colors"
          >
            Lost Document Steps
          </button>
        </div>
      )}
    </div>
  );
};
