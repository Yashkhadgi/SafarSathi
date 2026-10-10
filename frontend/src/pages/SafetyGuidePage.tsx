import React, { useState } from 'react';
import { 
  ShieldAlert, 
  HeartPulse, 
  FileText, 
  AlertTriangle, 
  CheckCircle2, 
  PhoneCall, 
  Loader2 
} from 'lucide-react';
import { apiGet } from '../api/client';

export const SafetyGuidePage: React.FC = () => {
  // Area Safety State
  const [safetyCity, setSafetyCity] = useState('Jaipur');
  const [safetyContext, setSafetyContext] = useState('solo traveler');
  const [areaData, setAreaData] = useState<{
    safety_summary?: string;
    safe_areas?: string[];
    precautions?: string[];
    scam_warnings?: string[];
  } | null>(null);
  const [areaLoading, setAreaLoading] = useState(false);

  // Medical State
  const [symptom, setSymptom] = useState('heat exhaustion');
  const [medCity, setMedCity] = useState('Jaipur');
  const [medData, setMedData] = useState<{
    first_aid_steps?: string[];
    disclaimer?: string;
    emergency_numbers?: Record<string, string>;
  } | null>(null);
  const [medLoading, setMedLoading] = useState(false);

  // Lost Docs State
  const [docType, setDocType] = useState('passport');
  const [docData, setDocData] = useState<{
    recovery_steps?: string[];
    important_contacts?: string[];
  } | null>(null);
  const [docLoading, setDocLoading] = useState(false);

  const handleAreaSafety = async (e: React.FormEvent) => {
    e.preventDefault();
    setAreaLoading(true);
    try {
      const res = await apiGet<unknown>(
        `/tools/safety/area?city=${encodeURIComponent(safetyCity)}&context=${encodeURIComponent(safetyContext)}`
      );
      setAreaData(res as typeof areaData);
    } catch {
      setAreaData(null);
    } finally {
      setAreaLoading(false);
    }
  };

  const handleMedical = async (e: React.FormEvent) => {
    e.preventDefault();
    setMedLoading(true);
    try {
      const res = await apiGet<unknown>(
        `/tools/safety/medical?symptom=${encodeURIComponent(symptom)}&city=${encodeURIComponent(medCity)}`
      );
      setMedData(res as typeof medData);
    } catch {
      setMedData(null);
    } finally {
      setMedLoading(false);
    }
  };

  const handleLostDocs = async (e: React.FormEvent) => {
    e.preventDefault();
    setDocLoading(true);
    try {
      const res = await apiGet<unknown>(
        `/tools/safety/lost-docs?what_lost=${encodeURIComponent(docType)}`
      );
      setDocData(res as typeof docData);
    } catch {
      setDocData(null);
    } finally {
      setDocLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Safety, Medical First-Aid & Lost Docs</h1>
        <p className="mt-1 text-xs text-slate-400">
          Verified regional safety benchmarks, medical first-aid action cards (no prescriptions), and document recovery guides.
        </p>
      </div>

      {/* 1. Area Safety Advisor */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-brand-400" />
          <span>Area Safety Advisor</span>
        </h2>

        <form onSubmit={handleAreaSafety} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <input
            type="text"
            required
            value={safetyCity}
            onChange={(e) => setSafetyCity(e.target.value)}
            placeholder="City (e.g. Jaipur, Delhi)"
            className="px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
          <input
            type="text"
            value={safetyContext}
            onChange={(e) => setSafetyContext(e.target.value)}
            placeholder="Context (e.g. night, solo female)"
            className="px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
          <button
            type="submit"
            disabled={areaLoading}
            className="py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            {areaLoading ? 'Checking...' : 'Check Safety'}
          </button>
        </form>

        {areaData && (
          <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs space-y-3">
            {areaData.safety_summary && (
              <p className="text-slate-300 leading-relaxed">{areaData.safety_summary}</p>
            )}
            {areaData.safe_areas && areaData.safe_areas.length > 0 && (
              <div>
                <strong className="text-slate-200 block mb-1">Recommended Areas:</strong>
                <ul className="list-disc pl-4 space-y-0.5 text-slate-400">
                  {areaData.safe_areas.map((a, i) => (
                    <li key={i}>{a}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 2. Medical Help with First-Aid Cards */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <HeartPulse className="w-4 h-4 text-emerald-400" />
          <span>Medical First-Aid Action Cards (No Prescriptions)</span>
        </h2>

        <form onSubmit={handleMedical} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <select
            value={symptom}
            onChange={(e) => setSymptom(e.target.value)}
            className="px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          >
            <option value="heat exhaustion">Heat Exhaustion / Dehydration</option>
            <option value="altitude sickness">Altitude Sickness (AMS)</option>
            <option value="stomach upset">Stomach Bug / Travelers Diarrhea</option>
            <option value="minor cut">Minor Cuts & Scrapes</option>
            <option value="insect bite">Insect / Mosquito Bites</option>
          </select>
          <input
            type="text"
            value={medCity}
            onChange={(e) => setMedCity(e.target.value)}
            placeholder="City (e.g. Jaipur, Leh)"
            className="px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
          <button
            type="submit"
            disabled={medLoading}
            className="py-2 px-4 rounded-md bg-emerald-700 hover:bg-emerald-600 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            {medLoading ? 'Loading...' : 'Get First-Aid Guide'}
          </button>
        </form>

        {medData && (
          <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs space-y-3">
            <div className="p-2.5 rounded bg-amber-950/40 border border-amber-900/60 text-amber-200 text-[11px]">
              <strong className="block mb-0.5">Medical Disclaimer:</strong>
              {medData.disclaimer || 'First-aid tips are for reference only. For acute conditions or severe pain, dial 108 / 112 immediately.'}
            </div>

            {medData.first_aid_steps && (
              <div>
                <strong className="text-slate-200 block mb-1">Recommended First-Aid Steps:</strong>
                <ol className="list-decimal pl-4 space-y-1 text-slate-300">
                  {medData.first_aid_steps.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 3. Lost Documents Checklist */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <FileText className="w-4 h-4 text-brand-400" />
          <span>Lost Passport, Wallet, or Phone Recovery</span>
        </h2>

        <form onSubmit={handleLostDocs} className="flex gap-3 max-w-md">
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            className="flex-1 px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          >
            <option value="passport">Lost Passport (Foreign / Indian)</option>
            <option value="phone">Lost Smartphone / SIM Card</option>
            <option value="wallet">Lost Wallet / Bank Cards</option>
            <option value="aadhar">Lost Aadhar / Voter ID</option>
          </select>
          <button
            type="submit"
            disabled={docLoading}
            className="py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            {docLoading ? 'Loading...' : 'Get Checklist'}
          </button>
        </form>

        {docData && (
          <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs space-y-3">
            {docData.recovery_steps && (
              <div>
                <strong className="text-slate-200 block mb-1">Step-by-Step Action Plan:</strong>
                <ol className="list-decimal pl-4 space-y-1 text-slate-300">
                  {docData.recovery_steps.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
