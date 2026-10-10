import React from 'react';
import { FileText, AlertTriangle, PhoneCall, CheckCircle } from 'lucide-react';

export const TermsPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <div className="mb-10 pb-6 border-b border-slate-800">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-slate-900 border border-slate-800 text-xs text-brand-400 mb-3">
          <FileText className="w-3.5 h-3.5" />
          <span>Last Updated: October 2024</span>
        </div>
        <h1 className="text-3xl font-bold text-white">Terms and Conditions</h1>
        <p className="mt-2 text-sm text-slate-400">
          Terms governing the use of the SafarSathi informational travel assistant and safety tools.
        </p>
      </div>

      <div className="space-y-8 text-sm text-slate-300 leading-relaxed">
        {/* Section 1 */}
        <section className="p-6 rounded-lg bg-slate-900 border border-slate-800">
          <div className="flex items-center gap-2.5 text-base font-semibold text-white mb-3">
            <CheckCircle className="w-5 h-5 text-brand-400" />
            <h2>1. Informational Service Only</h2>
          </div>
          <p className="text-slate-400 text-xs leading-relaxed">
            SafarSathi is an automated informational travel planning assistant. SafarSathi is not a registered travel agency, tour operator, or booking engine. We do not sell airline tickets, train reservations, hotel rooms, or tour packages, nor do we process any monetary payments.
          </p>
        </section>

        {/* Section 2 */}
        <section className="p-6 rounded-lg bg-slate-900 border border-slate-800">
          <div className="flex items-center gap-2.5 text-base font-semibold text-white mb-3">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <h2>2. Safety, Medical, and Emergency Disclaimer</h2>
          </div>
          <p className="text-slate-400 text-xs leading-relaxed mb-3">
            First-aid tips and medical guidance provided by the assistant are for informational reference only and do not constitute professional medical advice, diagnosis, or treatment:
          </p>
          <ul className="list-disc pl-5 space-y-1.5 text-xs text-slate-400">
            <li>SafarSathi never prescribes specific medication dosages or prescription pharmaceutical regimens.</li>
            <li>In any medical emergency, personal danger, accident, or acute illness, contact local emergency services immediately:</li>
          </ul>
          <div className="mt-4 p-3 rounded-md bg-slate-950 border border-slate-800 flex items-center justify-around text-xs">
            <div className="text-center">
              <span className="text-slate-400 block">National Emergency</span>
              <strong className="text-white text-sm">112</strong>
            </div>
            <div className="text-center">
              <span className="text-slate-400 block">Ambulance</span>
              <strong className="text-white text-sm">108</strong>
            </div>
            <div className="text-center">
              <span className="text-slate-400 block">Women Helpline</span>
              <strong className="text-white text-sm">1091</strong>
            </div>
          </div>
        </section>

        {/* Section 3 */}
        <section className="p-6 rounded-lg bg-slate-900 border border-slate-800">
          <div className="flex items-center gap-2.5 text-base font-semibold text-white mb-3">
            <PhoneCall className="w-5 h-5 text-brand-400" />
            <h2>3. Volatile Travel Data Verification</h2>
          </div>
          <p className="text-slate-400 text-xs leading-relaxed">
            Monument opening hours, ticket entry fees, train schedules, and taxi benchmarks are subject to unannounced revisions by local authorities and municipal transport departments. While SafarSathi updates and cross-references data regularly, travelers should confirm critical timings with official ticket counters (such as ASI or IRCTC) before departure.
          </p>
        </section>
      </div>
    </div>
  );
};
