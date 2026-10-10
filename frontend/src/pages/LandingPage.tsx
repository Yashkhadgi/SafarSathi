import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldAlert, 
  MapPin, 
  Languages, 
  Banknote, 
  CalendarDays, 
  Lock, 
  CheckCircle2, 
  ArrowRight 
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div>
      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-4 py-16 md:py-24 border-b border-slate-800">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-slate-900 border border-slate-800 text-xs text-slate-300 mb-6">
            <span className="w-2 h-2 rounded-full bg-brand-500"></span>
            <span>Independent travel intelligence for India</span>
          </div>

          <h1 className="text-3xl md:text-5xl font-bold tracking-tight text-white leading-tight">
            Factual travel planning, safety alerts, and local guides for India.
          </h1>

          <p className="mt-6 text-lg text-slate-400 leading-relaxed">
            SafarSathi provides verified monument timings, fair transport fares, regional language phrasebooks, and scam warnings across Indian states. No ads, no booking markups, and no commercial commissions.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link
              to="/signup"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-brand-600 hover:bg-brand-700 text-white font-medium text-sm transition-colors"
            >
              <span>Create free account</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/login"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md border border-slate-700 hover:bg-slate-900 text-slate-200 font-medium text-sm transition-colors"
            >
              <span>Log in to existing session</span>
            </Link>
          </div>

          {/* Key Facts Checklist */}
          <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-4 pt-8 border-t border-slate-900">
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-brand-400 mt-0.5 shrink-0" />
              <p className="text-xs text-slate-400">
                <strong className="text-slate-200 block">Verified sources</strong>
                Every fare, entry fee, and timing references verification dates.
              </p>
            </div>
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-brand-400 mt-0.5 shrink-0" />
              <p className="text-xs text-slate-400">
                <strong className="text-slate-200 block">No booking commission</strong>
                Pure assistance without flight, train, or hotel sales.
              </p>
            </div>
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-brand-400 mt-0.5 shrink-0" />
              <p className="text-xs text-slate-400">
                <strong className="text-slate-200 block">Zero data selling</strong>
                Encrypted trusted contacts, strict data isolation, full deletion.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="max-w-6xl mx-auto px-4 py-16">
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-white">What SafarSathi does</h2>
          <p className="mt-2 text-sm text-slate-400">
            Six practical tools designed specifically for traveling in Indian cities and rural regions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-md bg-slate-800 flex items-center justify-center text-brand-400 mb-4">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Scam and Safety Alerts</h3>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                Detailed warnings for known tourist scams around railway stations, fake ticket agents, prepaid taxi counters, and gem shops.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800/60 text-xs text-slate-500">
              Covers 15+ high-footfall tourist hubs
            </div>
          </div>

          {/* Card 2 */}
          <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-md bg-slate-800 flex items-center justify-center text-brand-400 mb-4">
                <Banknote className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Fair Price Benchmarks</h3>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                Realistic auto-rickshaw meter rates, airport taxi ranges, and monument entry fee tables for domestic and foreign visitors.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800/60 text-xs text-slate-500">
              Official ASI rates and state transport tariffs
            </div>
          </div>

          {/* Card 3 */}
          <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-md bg-slate-800 flex items-center justify-center text-brand-400 mb-4">
                <Languages className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Regional Phrasebooks</h3>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                Essential travel and emergency phrases in 8 regional languages including Hindi, Tamil, Telugu, Bengali, Kannada, and Malayalam.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800/60 text-xs text-slate-500">
              Offline phrases with pronunciation guides
            </div>
          </div>

          {/* Card 4 */}
          <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-md bg-slate-800 flex items-center justify-center text-brand-400 mb-4">
                <CalendarDays className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Itinerary Optimizer</h3>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                Geographic clustering and opening-day verification to ensure you do not arrive at closed monuments on Mondays or Fridays.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800/60 text-xs text-slate-500">
              Haversine distance math in Python
            </div>
          </div>

          {/* Card 5 */}
          <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-md bg-slate-800 flex items-center justify-center text-brand-400 mb-4">
                <MapPin className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Offline Emergency Directory</h3>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                One-tap access to national SOS (112), tourist police numbers, and verified major hospital addresses without requiring internet.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800/60 text-xs text-slate-500">
              Static cache runs even during poor network
            </div>
          </div>

          {/* Card 6 */}
          <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-md bg-slate-800 flex items-center justify-center text-brand-400 mb-4">
                <Lock className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Privacy and Data Isolation</h3>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                Trusted contact phone numbers are encrypted at rest with Fernet. Account deletion removes every message and trip instantly.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800/60 text-xs text-slate-500">
              Argon2id passwords, rotating session tokens
            </div>
          </div>
        </div>
      </section>

      {/* Honest Commitment Section */}
      <section className="bg-slate-900 border-t border-slate-800 py-16">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-xl font-bold text-white">Our Product Principles</h2>
          <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4 text-left">
            <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs text-slate-400">
              <strong className="text-slate-200 block text-sm mb-1">No Fake Reviews or Testimonials</strong>
              We do not post invented user counts, fabricated ratings, or promotional endorsements.
            </div>
            <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs text-slate-400">
              <strong className="text-slate-200 block text-sm mb-1">No Third-Party Tracking</strong>
              We do not embed third-party advertising pixels or sell telemetry data to data brokers.
            </div>
            <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs text-slate-400">
              <strong className="text-slate-200 block text-sm mb-1">Clear Medical Disclaimers</strong>
              First-aid tips are for reference only. We never provide drug dosages and always point to emergency services.
            </div>
            <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs text-slate-400">
              <strong className="text-slate-200 block text-sm mb-1">Open Data Export</strong>
              You can export all your chat transcripts, itineraries, and profile settings in JSON format at any time.
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
