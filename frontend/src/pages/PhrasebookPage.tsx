import React, { useEffect, useState } from 'react';
import { 
  BookOpen, 
  Volume2, 
  Languages, 
  ShieldAlert, 
  Search, 
  Loader2 
} from 'lucide-react';
import { apiGet } from '../api/client';

const LANGUAGES = [
  { code: 'hi-IN', name: 'Hindi (हिंदी)' },
  { code: 'ta-IN', name: 'Tamil (தமிழ்)' },
  { code: 'te-IN', name: 'Telugu (తెలుగు)' },
  { code: 'bn-IN', name: 'Bengali (বাংলা)' },
  { code: 'kn-IN', name: 'Kannada (ಕನ್ನಡ)' },
  { code: 'mr-IN', name: 'Marathi (मराठी)' },
  { code: 'gu-IN', name: 'Gujarati (ગુજરાતી)' },
  { code: 'en-IN', name: 'English (Indian)' },
];

export const PhrasebookPage: React.FC = () => {
  const [phrasesData, setPhrasesData] = useState<{
    situations?: Record<string, Record<string, [string, string]>>;
  } | null>(null);
  const [emergencyData, setEmergencyData] = useState<{
    phrases?: Array<{ language: string; text: string; code: string }>;
  } | null>(null);

  const [selectedLang, setSelectedLang] = useState('hi-IN');
  const [selectedSituation, setSelectedSituation] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [pRes, eRes] = await Promise.all([
          apiGet<unknown>('/tools/phrasebook'),
          apiGet<unknown>('/tools/phrasebook/emergency'),
        ]);
        setPhrasesData(pRes as typeof phrasesData);
        setEmergencyData(eRes as typeof emergencyData);
      } catch {
        // Ignore
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const speakText = (text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      window.speechSynthesis.speak(utterance);
    }
  };

  const situationsList = phrasesData?.situations ? Object.keys(phrasesData.situations) : [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Regional Phrasebooks & Emergency Phrases</h1>
        <p className="mt-1 text-xs text-slate-400">
          Pronunciation guides and offline travel phrases in 8 major Indian languages.
        </p>
      </div>

      {/* Language Selector */}
      <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
          <Languages className="w-4 h-4 text-brand-400" />
          <span>Target Language:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => setSelectedLang(lang.code)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors cursor-pointer ${
                selectedLang === lang.code
                  ? 'bg-brand-600 text-white'
                  : 'bg-slate-950 border border-slate-800 text-slate-300 hover:bg-slate-800'
              }`}
            >
              {lang.name}
            </button>
          ))}
        </div>
      </div>

      {/* Emergency Phrases Section */}
      <div className="p-6 rounded-lg bg-red-950/20 border border-red-900/60 space-y-4">
        <h2 className="text-sm font-semibold text-red-200 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-red-400" />
          <span>Critical Emergency Phrases</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {emergencyData?.phrases?.map((ep, idx) => (
            <div key={idx} className="p-3.5 rounded-md bg-slate-950 border border-red-900/40 text-xs flex items-center justify-between">
              <div>
                <span className="text-[10px] text-red-400 block font-medium">{ep.language}</span>
                <span className="font-semibold text-white mt-0.5 block">{ep.text}</span>
              </div>
              <button
                onClick={() => speakText(ep.text)}
                className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                title="Speak phrase"
              >
                <Volume2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Situation-wise Phrases */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-brand-400" />
            <span>Everyday Situations</span>
          </h2>

          <select
            value={selectedSituation}
            onChange={(e) => setSelectedSituation(e.target.value)}
            className="px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:border-brand-500"
          >
            <option value="all">All Situations</option>
            {situationsList.map((sit) => (
              <option key={sit} value={sit}>
                {sit.charAt(0).toUpperCase() + sit.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-500 text-xs">
            <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-brand-400" />
            <span>Loading phrasebook...</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {situationsList
              .filter((s) => selectedSituation === 'all' || selectedSituation === s)
              .map((situation) => {
                const entry = phrasesData?.situations?.[situation]?.[selectedLang];
                const text = entry ? entry[0] : 'Phrase unavailable in this language';
                const pronunciation = entry ? entry[1] : '';

                return (
                  <div key={situation} className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex items-start justify-between">
                    <div className="space-y-1">
                      <span className="text-[10px] text-brand-400 uppercase font-semibold tracking-wider">
                        {situation}
                      </span>
                      <h3 className="text-sm font-bold text-white">{text}</h3>
                      {pronunciation && (
                        <p className="text-xs text-slate-400 italic">Pronunciation: "{pronunciation}"</p>
                      )}
                    </div>

                    <button
                      onClick={() => speakText(text)}
                      className="p-2 rounded-md hover:bg-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
                      title="Listen"
                    >
                      <Volume2 className="w-4 h-4" />
                    </button>
                  </div>
                );
              })}
          </div>
        )}
      </div>
    </div>
  );
};
