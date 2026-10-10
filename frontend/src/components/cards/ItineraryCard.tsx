import React, { useState } from 'react';
import { 
  Calendar, 
  Clock, 
  MapPin, 
  RotateCcw, 
  Bookmark, 
  Share2, 
  FileDown, 
  Sparkles, 
  Maximize2, 
  Check, 
  ChevronDown, 
  ChevronUp, 
  Loader2 
} from 'lucide-react';
import { apiPost } from '../../api/client';

export interface ItinerarySlot {
  time: string;
  place: string;
  duration_min: number;
  travel_from_prev?: string;
  opening_hours?: string;
  notes?: string;
  source?: { name: string; url: string; last_verified?: string };
}

export interface ItineraryDay {
  day: number;
  theme?: string;
  slots: ItinerarySlot[];
}

export interface ItineraryData {
  trip_id?: string;
  destination: string;
  days: ItineraryDay[];
  version?: number;
  assumptions?: string[];
  warnings?: string[];
  diff_summary?: string;
}

interface ItineraryCardProps {
  data: ItineraryData;
  onSendChatMessage?: (prompt: string) => void;
  onOpenInspector?: (data: ItineraryData) => void;
}

export const ItineraryCard: React.FC<ItineraryCardProps> = ({
  data,
  onSendChatMessage,
  onOpenInspector,
}) => {
  const [expandedDay, setExpandedDay] = useState<number>(1);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [undoing, setUndoing] = useState(false);
  const [exportCopied, setExportCopied] = useState(false);

  const tripId = data.trip_id || 'active';
  const destination = data.destination || 'Destination';
  const days = data.days || [];
  const version = data.version || 1;

  // Non-LLM Action: Save Trip
  const handleSaveTrip = async () => {
    setSaving(true);
    setSavedSuccess(false);
    try {
      await apiPost('/trips', {
        destination,
        days_count: days.length,
        trip_data: data,
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch {
      // Soft error
    } finally {
      setSaving(false);
    }
  };

  // Non-LLM Action: Undo Trip
  const handleUndo = async () => {
    setUndoing(true);
    try {
      await apiPost(`/tools/itinerary/undo?trip_id=${tripId}`);
      if (onSendChatMessage) {
        onSendChatMessage('Show the updated itinerary after undoing the previous change.');
      }
    } catch {
      // Soft error
    } finally {
      setUndoing(false);
    }
  };

  // Non-LLM Action: WhatsApp Plain Text Export
  const handleExportWhatsApp = () => {
    const lines = [`🗺️ *${destination.toUpperCase()} ITINERARY* (Version ${version})\n`];
    days.forEach((d) => {
      lines.push(`*Day ${d.day}:*`);
      d.slots.forEach((s) => {
        lines.push(`• ${s.time} - ${s.place} (${s.duration_min} mins)`);
        if (s.opening_hours && s.opening_hours !== 'verify opening hours and closed days') {
          lines.push(`  Hours: ${s.opening_hours}`);
        }
      });
      lines.push('');
    });
    lines.push('Generated via SafarSathi (safarsathi.in)');

    navigator.clipboard.writeText(lines.join('\n'));
    setExportCopied(true);
    setTimeout(() => setExportCopied(false), 3000);
  };

  // Non-LLM Action: Download iCalendar (.ics)
  const handleDownloadICS = () => {
    const icsLines = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//SafarSathi Travel Assistant//EN',
      'CALSCALE:GREGORIAN',
    ];

    const today = new Date();
    days.forEach((day, dayIdx) => {
      day.slots.forEach((slot, sIdx) => {
        const eventDate = new Date(today);
        eventDate.setDate(today.getDate() + dayIdx + 1);
        const [hh, mm] = (slot.time && slot.time.includes(':') ? slot.time : '09:00').split(':');
        eventDate.setHours(parseInt(hh, 10) || 9, parseInt(mm, 10) || 0, 0, 0);

        const startStr = eventDate.toISOString().replace(/[-:]/g, '').slice(0, 15) + 'Z';
        const endDate = new Date(eventDate.getTime() + (slot.duration_min || 90) * 60000);
        const endStr = endDate.toISOString().replace(/[-:]/g, '').slice(0, 15) + 'Z';

        icsLines.push('BEGIN:VEVENT');
        icsLines.push(`SUMMARY:${slot.place} - ${destination}`);
        icsLines.push(`DESCRIPTION:SafarSathi Itinerary Day ${day.day}. ${slot.notes || ''}`);
        icsLines.push(`DTSTART:${startStr}`);
        icsLines.push(`DTEND:${endStr}`);
        icsLines.push(`LOCATION:${slot.place}, ${destination}`);
        icsLines.push(`UID:safarsathi-${tripId}-d${day.day}-s${sIdx}@safarsathi.in`);
        icsLines.push('END:VEVENT');
      });
    });

    icsLines.push('END:VCALENDAR');
    const blob = new Blob([icsLines.join('\r\n')], { type: 'text/calendar;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `itinerary_${destination.toLowerCase()}_${days.length}days.ics`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="w-full rounded-lg bg-slate-900 border border-slate-800 p-4 space-y-4 shadow-lg text-slate-100">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-brand-950 border border-brand-800 text-brand-400 flex items-center justify-center">
            <Calendar className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white capitalize">{destination} Trip Plan</h3>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
                v{version}
              </span>
            </div>
            <span className="text-[11px] text-slate-400">
              {days.length} Days Itinerary with verified opening hours
            </span>
          </div>
        </div>

        {onOpenInspector && (
          <button
            onClick={() => onOpenInspector(data)}
            className="flex items-center gap-1 px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] font-medium transition-colors"
            title="Inspect in side panel"
          >
            <Maximize2 className="w-3.5 h-3.5" />
            <span>Inspector</span>
          </button>
        )}
      </div>

      {/* Diff Summary alert if present */}
      {data.diff_summary && (
        <div className="p-2 rounded bg-brand-950/40 border border-brand-900/60 text-[11px] text-brand-300 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 shrink-0" />
          <span>Latest edit: {data.diff_summary}</span>
        </div>
      )}

      {/* Accordion Days List */}
      <div className="space-y-2">
        {days.map((day) => {
          const isExpanded = expandedDay === day.day;
          return (
            <div key={day.day} className="rounded-md border border-slate-800 bg-slate-950 overflow-hidden">
              <button
                type="button"
                onClick={() => setExpandedDay(isExpanded ? 0 : day.day)}
                className="w-full px-3 py-2 flex items-center justify-between text-left hover:bg-slate-900/60 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded bg-brand-600/20 text-brand-400 font-bold text-[10px] flex items-center justify-center">
                    D{day.day}
                  </span>
                  <span className="text-xs font-semibold text-white">
                    Day {day.day} {day.theme ? `• ${day.theme}` : ''}
                  </span>
                  <span className="text-[10px] text-slate-500">({day.slots.length} stops)</span>
                </div>
                {isExpanded ? <ChevronUp className="w-3.5 h-3.5 text-slate-400" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-400" />}
              </button>

              {isExpanded && (
                <div className="px-3 pb-3 pt-1 space-y-2 border-t border-slate-800/80">
                  {day.slots.map((slot, sIdx) => (
                    <div key={sIdx} className="p-2 rounded bg-slate-900/80 border border-slate-800/60 text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5 font-medium text-slate-200">
                          <MapPin className="w-3 h-3 text-brand-400 shrink-0" />
                          <span>{slot.place}</span>
                        </div>
                        <div className="flex items-center gap-1 text-[11px] text-slate-400">
                          <Clock className="w-3 h-3" />
                          <span>{slot.time} ({slot.duration_min} min)</span>
                        </div>
                      </div>

                      {slot.opening_hours && slot.opening_hours !== 'verify opening hours and closed days' && (
                        <p className="text-[10px] text-emerald-400/90">
                          Hours: {slot.opening_hours}
                        </p>
                      )}

                      {slot.source && slot.source.url && (
                        <div className="text-[10px] text-slate-500 flex items-center gap-1 pt-0.5">
                          <span>Source: {slot.source.name}</span>
                          {slot.source.last_verified && <span>(verified {slot.source.last_verified})</span>}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Card Action Buttons (Chat Prompts vs Non-LLM API) */}
      <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center justify-between gap-2 text-xs">
        {/* Chat Edit Prompts */}
        {onSendChatMessage && (
          <div className="flex flex-wrap items-center gap-1.5">
            <button
              onClick={() => onSendChatMessage(`Make the ${destination} itinerary pace relaxed with fewer stops`)}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] transition-colors"
            >
              Make Relaxed
            </button>
            <button
              onClick={() => onSendChatMessage(`Swap Day 1 and Day 2 in my ${destination} itinerary`)}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] transition-colors"
            >
              Swap Days
            </button>
            <button
              onClick={() => onSendChatMessage(`Remove the last stop from Day 1 in my ${destination} itinerary`)}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] transition-colors"
            >
              Remove Stop
            </button>
          </div>
        )}

        {/* Non-LLM Actions */}
        <div className="flex items-center gap-1.5 ml-auto">
          {version > 1 && (
            <button
              onClick={handleUndo}
              disabled={undoing}
              className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
              title="Undo last edit (Non-LLM API)"
            >
              {undoing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RotateCcw className="w-3.5 h-3.5" />}
            </button>
          )}

          <button
            onClick={handleSaveTrip}
            disabled={saving}
            className={`flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
              savedSuccess
                ? 'bg-emerald-950 border border-emerald-800 text-emerald-300'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-200'
            }`}
          >
            {saving ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : savedSuccess ? (
              <Check className="w-3 h-3" />
            ) : (
              <Bookmark className="w-3 h-3" />
            )}
            <span>{savedSuccess ? 'Saved' : 'Save Trip'}</span>
          </button>

          <button
            onClick={handleExportWhatsApp}
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-medium transition-colors"
            title="Copy WhatsApp formatted itinerary text"
          >
            {exportCopied ? <Check className="w-3 h-3 text-emerald-400" /> : <Share2 className="w-3 h-3" />}
            <span>{exportCopied ? 'Copied' : 'WhatsApp'}</span>
          </button>

          <button
            onClick={handleDownloadICS}
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-brand-600 hover:bg-brand-700 text-white text-[11px] font-medium transition-colors"
            title="Download iCalendar file (.ics)"
          >
            <FileDown className="w-3 h-3" />
            <span>.ICS</span>
          </button>
        </div>
      </div>
    </div>
  );
};
