import React, { useState } from 'react';
import { 
  Volume2, 
  Languages, 
  Copy, 
  Check, 
  Sparkles 
} from 'lucide-react';

export interface PhraseItem {
  situation?: string;
  english?: string;
  translated: string;
  phonetic?: string;
  audio_sample_url?: string;
  language?: string;
}

export interface PhrasebookData {
  language: string;
  language_code?: string;
  phrases: PhraseItem[];
}

interface PhrasebookCardProps {
  data: PhrasebookData;
  onSendMessage?: (message: string) => void;
}

export const PhrasebookCard: React.FC<PhrasebookCardProps> = ({ data, onSendMessage }) => {
  const [playingIdx, setPlayingIdx] = useState<number | null>(null);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  const speakPhrase = (text: string, idx: number, langCode?: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      if (langCode) {
        utterance.lang = langCode;
      } else if (data.language.toLowerCase().includes('hindi')) {
        utterance.lang = 'hi-IN';
      }
      utterance.onstart = () => setPlayingIdx(idx);
      utterance.onend = () => setPlayingIdx(null);
      utterance.onerror = () => setPlayingIdx(null);
      window.speechSynthesis.speak(utterance);
    }
  };

  const copyText = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="w-full my-3 rounded-lg border border-slate-700 bg-slate-900 text-slate-100 shadow-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-slate-800/80 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
            <Languages className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100">
              {data.language} Travel Phrasebook
            </h4>
            <p className="text-[11px] text-slate-400">Pronunciation & emergency translations</p>
          </div>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
          {data.phrases?.length || 0} Phrases
        </span>
      </div>

      {/* Phrasebook Items */}
      <div className="p-4 space-y-2.5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {data.phrases?.map((p, idx) => (
            <div 
              key={idx}
              className="p-3 rounded-md bg-slate-800/50 border border-slate-700/70 hover:border-slate-600 transition-colors space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                  {p.situation || 'Useful Phrase'}
                </span>
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => speakPhrase(p.translated, idx, data.language_code)}
                    className={`p-1.5 rounded border transition-colors ${
                      playingIdx === idx
                        ? 'bg-brand-600 text-white border-brand-500'
                        : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700 hover:text-slate-100'
                    }`}
                    title="Pronounce audio"
                  >
                    <Volume2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => copyText(p.translated, idx)}
                    className="p-1.5 rounded bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-slate-100 transition-colors"
                    title="Copy translation"
                  >
                    {copiedIdx === idx ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
              </div>

              <div>
                <div className="text-base font-semibold text-slate-100">
                  {p.translated}
                </div>
                {p.phonetic && (
                  <div className="text-xs font-mono text-indigo-300">
                    "{p.phonetic}"
                  </div>
                )}
                {p.english && (
                  <div className="text-[11px] text-slate-400 mt-1">
                    English: {p.english}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Quick Follow-up Actions */}
        {onSendMessage && (
          <div className="pt-2 flex flex-wrap gap-2">
            <button
              onClick={() => onSendMessage(`How to say 'How much for this?' and negotiate in Hindi?`)}
              className="px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
            >
              Shopping phrases
            </button>
            <button
              onClick={() => onSendMessage(`What are polite words and dining phrases in Marathi?`)}
              className="px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
            >
              Food & dining phrases
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
