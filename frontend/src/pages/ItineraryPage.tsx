import React, { useEffect, useState } from 'react';
import { 
  Calendar, 
  Clock, 
  RotateCcw, 
  Plus, 
  AlertCircle, 
  CheckCircle2, 
  ExternalLink, 
  History, 
  Sparkles, 
  Loader2, 
  MapPin, 
  Edit3 
} from 'lucide-react';
import { apiGet, apiPost, ApiError } from '../api/client';

interface Slot {
  place: string;
  time?: string;
  duration_min?: number;
  travel_from_prev?: string;
  opening_hours?: string;
  closed_on_visit_date?: boolean;
  notes?: string;
  source?: {
    name?: string;
    url?: string;
    last_verified?: string;
  };
}

interface Day {
  day: number;
  theme?: string;
  slots: Slot[];
}

interface Itinerary {
  trip_id?: string;
  destination?: string;
  pace?: string;
  days?: Day[];
  warnings?: string[];
  version?: number;
  diff_summary?: string;
  markdown?: string;
}

interface VersionItem {
  version: number;
  summary: string;
  created_at: string;
}

export const ItineraryPage: React.FC = () => {
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [versions, setVersions] = useState<VersionItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [destination, setDestination] = useState('Jaipur');
  const [days, setDays] = useState(3);
  const [pace, setPace] = useState('normal');
  const [theme, setTheme] = useState('');
  const [travelerType, setTravelerType] = useState('');

  // Edit State
  const [editInstructions, setEditInstructions] = useState('');
  const [editing, setEditing] = useState(false);

  const fetchActive = async () => {
    try {
      const res = await apiGet<{ itinerary: Itinerary; versions: VersionItem[] }>('/tools/itinerary/active');
      if (res.itinerary && !('error' in res.itinerary)) {
        setItinerary(res.itinerary);
        setVersions(res.versions || []);
      }
    } catch {
      // Ignore initial lookup failure
    }
  };

  useEffect(() => {
    fetchActive();
  }, []);

  const handleBuild = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await apiPost<Itinerary>('/tools/itinerary/build', {
        destination,
        days: Number(days),
        pace,
        theme,
        traveler_type: travelerType,
      });

      if ('error' in res) {
        setError(String(res.error));
      } else {
        setItinerary(res);
        await fetchActive();
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.data.detail || 'Could not build itinerary');
      } else {
        setError('Network error building itinerary');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editInstructions.trim() || !itinerary) return;

    setError(null);
    setEditing(true);

    try {
      const res = await apiPost<Itinerary>('/tools/itinerary/edit', {
        trip_id: itinerary.trip_id,
        instructions: editInstructions,
      });

      if ('error' in res) {
        setError(String(res.error));
      } else {
        setItinerary(res);
        setEditInstructions('');
        await fetchActive();
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.data.detail || 'Failed to apply patch edit');
      } else {
        setError('Network error editing itinerary');
      }
    } finally {
      setEditing(false);
    }
  };

  const handleUndo = async () => {
    if (!itinerary?.trip_id) return;
    setError(null);
    setEditing(true);

    try {
      const res = await apiPost<Itinerary>(`/tools/itinerary/undo?trip_id=${itinerary.trip_id}`);
      if ('error' in res) {
        setError(String(res.error));
      } else {
        setItinerary(res);
        await fetchActive();
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.data.detail || 'Undo failed');
      }
    } finally {
      setEditing(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Smart Itinerary Planner</h1>
        <p className="mt-1 text-xs text-slate-400">
          Deterministic day-by-day itinerary planning with opening-hours validation and immutable patch versioning.
        </p>
      </div>

      {error && (
        <div className="p-3.5 rounded-md bg-red-950/60 border border-red-900 text-red-200 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Plan Creation Form */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-brand-400" />
          <span>Generate New Verified Plan</span>
        </h2>

        <form onSubmit={handleBuild} className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="itin-dest">
              Destination
            </label>
            <input
              id="itin-dest"
              type="text"
              required
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="e.g. Jaipur, Goa, Leh"
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="itin-days">
              Days (1-7)
            </label>
            <input
              id="itin-days"
              type="number"
              min={1}
              max={7}
              required
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="itin-pace">
              Pace
            </label>
            <select
              id="itin-pace"
              value={pace}
              onChange={(e) => setPace(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            >
              <option value="relaxed">Relaxed (2 sights/day)</option>
              <option value="normal">Normal (3 sights/day)</option>
              <option value="packed">Packed (4 sights/day)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="itin-theme">
              Theme (Optional)
            </label>
            <select
              id="itin-theme"
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            >
              <option value="">All / Heritage</option>
              <option value="spiritual">Spiritual</option>
              <option value="adventure">Adventure</option>
              <option value="food">Food & Culinary</option>
              <option value="family">Family Friendly</option>
            </select>
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
                  <span>Building...</span>
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  <span>Build Itinerary</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Itinerary Display */}
      {itinerary && itinerary.days && itinerary.days.length > 0 ? (
        <div className="space-y-6">
          {/* Header Action Bar */}
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white">{itinerary.destination} Itinerary</h2>
                <span className="px-2 py-0.5 rounded bg-brand-950 border border-brand-800 text-brand-300 text-[10px] font-mono">
                  v{itinerary.version || 1}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                {itinerary.days.length} days, {itinerary.pace} pace {itinerary.diff_summary && `(${itinerary.diff_summary})`}
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleUndo}
                disabled={editing || (itinerary.version || 1) <= 1}
                className="px-3 py-1.5 rounded-md border border-slate-700 hover:bg-slate-800 disabled:opacity-40 text-slate-300 text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Undo Edit</span>
              </button>
            </div>
          </div>

          {/* Validation Warnings */}
          {itinerary.warnings && itinerary.warnings.length > 0 && (
            <div className="p-3.5 rounded-md bg-amber-950/40 border border-amber-900/60 text-amber-200 text-xs space-y-1">
              <div className="font-semibold flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4 text-amber-400" />
                <span>Planning Notices:</span>
              </div>
              <ul className="list-disc pl-5 space-y-0.5 text-[11px] text-amber-300/90">
                {itinerary.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Days Grid */}
          <div className="grid grid-cols-1 gap-6">
            {itinerary.days.map((dayItem) => (
              <div key={dayItem.day} className="p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-md bg-brand-600 text-white font-bold text-xs flex items-center justify-center">
                      {dayItem.day}
                    </span>
                    <h3 className="text-sm font-semibold text-white">Day {dayItem.day}</h3>
                  </div>
                  <span className="text-xs text-slate-400">{dayItem.slots?.length || 0} stops</span>
                </div>

                <div className="space-y-3">
                  {dayItem.slots?.map((slot, sIdx) => (
                    <div
                      key={sIdx}
                      className={`p-3.5 rounded-md border text-xs transition-colors ${
                        slot.closed_on_visit_date
                          ? 'bg-red-950/30 border-red-900/60'
                          : 'bg-slate-950 border-slate-800/80 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-white text-sm">{slot.place}</span>
                            {slot.closed_on_visit_date && (
                              <span className="px-1.5 py-0.5 rounded bg-red-950 border border-red-800 text-red-300 text-[10px] font-medium">
                                Closed Today
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-3 mt-1 text-slate-400 text-[11px]">
                            {slot.duration_min && (
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3 text-slate-500" />
                                <span>{slot.duration_min} min</span>
                              </span>
                            )}
                            {slot.travel_from_prev && (
                              <span className="text-slate-500">
                                Transit: {slot.travel_from_prev}
                              </span>
                            )}
                          </div>
                        </div>

                        {slot.source?.url && (
                          <a
                            href={slot.source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-brand-400 hover:underline flex items-center gap-1 text-[11px] shrink-0"
                          >
                            <span>Source</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>

                      {slot.opening_hours && (
                        <div className="mt-2 pt-2 border-t border-slate-900 text-[11px] text-slate-400">
                          <span>Hours: {slot.opening_hours}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Edit / Patch Operations Form */}
          <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
            <h3 className="text-xs font-semibold text-white flex items-center gap-1.5">
              <Edit3 className="w-4 h-4 text-brand-400" />
              <span>Natural Language Edit (Immutable Patch)</span>
            </h3>
            <p className="text-[11px] text-slate-400">
              Type instructions like: <em>"Swap day 1 and day 2"</em>, <em>"Remove slot 1 from day 2"</em>, or <em>"Change pace to packed"</em>.
            </p>
            <form onSubmit={handleEdit} className="flex gap-2">
              <input
                type="text"
                value={editInstructions}
                onChange={(e) => setEditInstructions(e.target.value)}
                placeholder="Enter modification instruction..."
                className="flex-1 px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
              />
              <button
                type="submit"
                disabled={editing || !editInstructions.trim()}
                className="py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
              >
                {editing ? 'Applying...' : 'Apply Edit'}
              </button>
            </form>
          </div>

          {/* Version History Drawer */}
          {versions.length > 0 && (
            <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
              <h3 className="text-xs font-semibold text-white flex items-center gap-1.5">
                <History className="w-4 h-4 text-slate-400" />
                <span>Version History</span>
              </h3>
              <div className="space-y-2">
                {versions.map((v) => (
                  <div key={v.version} className="p-2.5 rounded-md bg-slate-950 border border-slate-800/80 text-xs flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-slate-200">Version {v.version}</span>
                      <span className="text-slate-400 ml-2">{v.summary}</span>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {new Date(v.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="p-12 rounded-lg bg-slate-900 border border-slate-800 text-center space-y-3">
          <div className="w-12 h-12 rounded-md bg-slate-950 border border-slate-800 text-slate-500 mx-auto flex items-center justify-center">
            <Calendar className="w-6 h-6" />
          </div>
          <h2 className="text-sm font-semibold text-slate-300">No active itinerary</h2>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Choose a destination above and click Build Itinerary to generate a verified, paced day-by-day plan.
          </p>
        </div>
      )}
    </div>
  );
};
