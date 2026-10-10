import React, { useState } from 'react';
import { 
  FileDown, 
  MessageSquare, 
  Calendar, 
  Printer, 
  Copy, 
  Check, 
  Loader2 
} from 'lucide-react';
import { apiPost } from '../api/client';

export const ExportPage: React.FC = () => {
  const [copied, setCopied] = useState(false);
  const [textExport, setTextExport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleExportText = async () => {
    setLoading(true);
    try {
      const res = await apiPost<{ text?: string }>('/tools/export/text', {});
      if (res && res.text) {
        setTextExport(res.text);
      } else {
        setTextExport('No active itinerary found. Build an itinerary in the planner first.');
      }
    } catch {
      setTextExport('Failed to export itinerary.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadIcs = async () => {
    try {
      const res = await apiPost<{ ics_content?: string }>('/tools/export/ics', {});
      if (res && res.ics_content) {
        const blob = new Blob([res.ics_content], { type: 'text/calendar' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `safarsathi_trip_${new Date().toISOString().slice(0, 10)}.ics`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        alert('No active itinerary found.');
      }
    } catch {
      alert('Could not download .ics file.');
    }
  };

  const handleCopy = () => {
    if (textExport) {
      navigator.clipboard.writeText(textExport);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Export Itinerary</h1>
        <p className="mt-1 text-xs text-slate-400">
          Share your plan on WhatsApp, sync stops to Apple/Google Calendar (.ics), or print a clean summary.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* WhatsApp Export Card */}
        <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 flex flex-col justify-between space-y-4">
          <div>
            <div className="w-10 h-10 rounded-md bg-emerald-950 border border-emerald-800 text-emerald-400 flex items-center justify-center mb-3">
              <MessageSquare className="w-5 h-5" />
            </div>
            <h2 className="text-sm font-bold text-white">WhatsApp & SMS Text</h2>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Clean emoji-free structured itinerary text ready to copy-paste into messaging apps.
            </p>
          </div>

          <button
            onClick={handleExportText}
            disabled={loading}
            className="w-full py-2 px-3 rounded-md bg-emerald-700 hover:bg-emerald-600 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            {loading ? 'Generating...' : 'Generate Text'}
          </button>
        </div>

        {/* iCalendar (.ics) Card */}
        <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 flex flex-col justify-between space-y-4">
          <div>
            <div className="w-10 h-10 rounded-md bg-brand-950 border border-brand-800 text-brand-400 flex items-center justify-center mb-3">
              <Calendar className="w-5 h-5" />
            </div>
            <h2 className="text-sm font-bold text-white">iCalendar (.ics) Sync</h2>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Download standard .ics file to automatically add all daily activities to Google or Apple Calendar.
            </p>
          </div>

          <button
            onClick={handleDownloadIcs}
            className="w-full py-2 px-3 rounded-md bg-brand-600 hover:bg-brand-700 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            Download .ICS File
          </button>
        </div>

        {/* Print Summary Card */}
        <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 flex flex-col justify-between space-y-4">
          <div>
            <div className="w-10 h-10 rounded-md bg-slate-800 border border-slate-700 text-slate-300 flex items-center justify-center mb-3">
              <Printer className="w-5 h-5" />
            </div>
            <h2 className="text-sm font-bold text-white">Print View</h2>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              High-contrast, printer-friendly summary of daily stops and verified timings.
            </p>
          </div>

          <button
            onClick={() => window.print()}
            className="w-full py-2 px-3 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors cursor-pointer"
          >
            Print Itinerary
          </button>
        </div>
      </div>

      {/* Text Preview Box */}
      {textExport && (
        <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="text-xs font-semibold text-white">Formatted Plain-Text Summary</span>
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 px-3 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors cursor-pointer"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy Text</span>
                </>
              )}
            </button>
          </div>

          <pre className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300 whitespace-pre-wrap leading-relaxed">
            {textExport}
          </pre>
        </div>
      )}
    </div>
  );
};
