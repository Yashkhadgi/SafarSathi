import React, { useState, useEffect } from 'react';
import { 
  CheckSquare, 
  Square, 
  Luggage, 
  Sparkles, 
  CheckCircle2, 
  RotateCcw 
} from 'lucide-react';

export interface ChecklistItem {
  id: string;
  label: string;
  essential?: boolean;
  checked?: boolean;
}

export interface ChecklistCategory {
  name: string;
  items: ChecklistItem[];
}

export interface ChecklistData {
  title: string;
  destination?: string;
  season?: string;
  categories: ChecklistCategory[];
  tip?: string;
}

interface ChecklistCardProps {
  data: ChecklistData;
  onSendMessage?: (message: string) => void;
}

export const ChecklistCard: React.FC<ChecklistCardProps> = ({ data, onSendMessage }) => {
  const storageKey = `safarsathi_checklist_${data.title.replace(/\s+/g, '_')}`;

  // Load checked items from local storage
  const [checkedMap, setCheckedMap] = useState<Record<string, boolean>>(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) return JSON.parse(saved);
    } catch {
      // Ignore storage error
    }
    return {};
  });

  const toggleItem = (id: string) => {
    setCheckedMap((prev) => {
      const next = { ...prev, [id]: !prev[id] };
      try {
        localStorage.setItem(storageKey, JSON.stringify(next));
      } catch {
        // Ignore
      }
      return next;
    });
  };

  const resetAll = () => {
    setCheckedMap({});
    try {
      localStorage.removeItem(storageKey);
    } catch {
      // Ignore
    }
  };

  // Calculate completion
  const allItems = data.categories?.flatMap((c) => c.items) || [];
  const completedCount = allItems.filter((i) => checkedMap[i.id]).length;
  const progressPct = allItems.length > 0 ? Math.round((completedCount / allItems.length) * 100) : 0;

  return (
    <div className="w-full my-3 rounded-lg border border-slate-700 bg-slate-900 text-slate-100 shadow-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-slate-800/80 border-b border-slate-700 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <Luggage className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100">{data.title}</h4>
            <p className="text-[11px] text-slate-400">Interactive tickable checklist (state saved)</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-emerald-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
            {completedCount} / {allItems.length} Done ({progressPct}%)
          </span>
          {completedCount > 0 && (
            <button
              onClick={resetAll}
              className="p-1 rounded bg-slate-800 border border-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
              title="Reset checklist"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-1 bg-slate-800">
        <div 
          className="h-full bg-emerald-500 transition-all duration-300"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Categories & Items */}
      <div className="p-4 space-y-4">
        {data.categories?.map((cat, cIdx) => (
          <div key={cIdx} className="space-y-2">
            <div className="text-xs font-semibold text-slate-300 flex items-center justify-between border-b border-slate-800 pb-1">
              <span>{cat.name}</span>
              <span className="text-[10px] text-slate-500 font-normal font-mono">
                {cat.items.filter(i => checkedMap[i.id]).length} / {cat.items.length}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {cat.items.map((item) => {
                const isChecked = !!checkedMap[item.id];
                return (
                  <button
                    key={item.id}
                    onClick={() => toggleItem(item.id)}
                    className={`p-2 rounded-md border text-left flex items-start gap-2.5 transition-colors cursor-pointer ${
                      isChecked
                        ? 'bg-slate-800/40 border-emerald-900/60 text-slate-400 line-through'
                        : 'bg-slate-800/70 border-slate-700/80 text-slate-200 hover:border-slate-600'
                    }`}
                  >
                    <div className="mt-0.5 shrink-0">
                      {isChecked ? (
                        <CheckSquare className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <Square className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                    <div className="text-xs flex-1">
                      <span>{item.label}</span>
                      {item.essential && !isChecked && (
                        <span className="ml-1.5 text-[9px] px-1 py-0.2 rounded bg-amber-950 border border-amber-800 text-amber-300 font-mono no-underline inline-block">
                          Essential
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        ))}

        {/* Packing Tip */}
        {data.tip && (
          <div className="p-2.5 rounded-md bg-slate-800/50 border border-slate-700/60 flex items-start gap-2 text-[11px] text-slate-400">
            <Sparkles className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
            <span>{data.tip}</span>
          </div>
        )}

        {/* Quick Follow-up Actions */}
        {onSendMessage && (
          <div className="pt-2 flex flex-wrap gap-2">
            <button
              onClick={() => onSendMessage(`What medicines or first-aid kit should I pack for travel in India?`)}
              className="px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
            >
              Medical kit list
            </button>
            <button
              onClick={() => onSendMessage(`What documents do foreign tourists or domestic travelers need?`)}
              className="px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
            >
              Document checklist
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
