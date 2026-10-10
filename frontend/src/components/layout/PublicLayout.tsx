import React from 'react';
import { Link, Outlet } from 'react-router-dom';
import { Compass, ShieldAlert, LogIn, UserPlus, PhoneCall } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const PublicLayout: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Top Banner for Emergency Access */}
      <div className="bg-slate-900 border-b border-slate-800 text-xs px-4 py-1.5 flex items-center justify-between">
        <div className="flex items-center gap-2 text-slate-400">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-500" />
          <span>India Emergency Numbers: <strong>112</strong> (All), <strong>108</strong> (Ambulance), <strong>1091</strong> (Women Helpline)</span>
        </div>
        <div className="flex items-center gap-4 text-slate-400">
          <span>Non-commercial travel assistant</span>
        </div>
      </div>

      {/* Main Header */}
      <header className="sticky top-0 z-40 bg-slate-950/90 backdrop-blur border-b border-slate-800">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 text-slate-100 font-semibold text-lg hover:text-brand-400 transition-colors">
            <div className="w-8 h-8 rounded-md bg-brand-600 flex items-center justify-center text-white">
              <Compass className="w-5 h-5" />
            </div>
            <span>SafarSathi</span>
          </Link>

          <nav className="flex items-center gap-6 text-sm">
            <Link to="/#features" className="text-slate-400 hover:text-slate-100 transition-colors">
              Features
            </Link>
            <Link to="/privacy" className="text-slate-400 hover:text-slate-100 transition-colors">
              Privacy
            </Link>
            <Link to="/terms" className="text-slate-400 hover:text-slate-100 transition-colors">
              Terms
            </Link>
            
            {user ? (
              <Link
                to="/app"
                className="px-3.5 py-1.5 rounded-md bg-brand-600 hover:bg-brand-700 text-white font-medium text-sm transition-colors"
              >
                Go to App
              </Link>
            ) : (
              <div className="flex items-center gap-3">
                <Link
                  to="/login"
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-slate-700 hover:bg-slate-800 text-slate-200 text-sm font-medium transition-colors"
                >
                  <LogIn className="w-4 h-4 text-slate-400" />
                  <span>Log in</span>
                </Link>
                <Link
                  to="/signup"
                  className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium transition-colors"
                >
                  <UserPlus className="w-4 h-4" />
                  <span>Sign up</span>
                </Link>
              </div>
            )}
          </nav>
        </div>
      </header>

      {/* Page Content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Honest Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 text-slate-400 text-xs py-8">
        <div className="max-w-6xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            <p className="font-medium text-slate-300">SafarSathi Travel Assistant</p>
            <p className="mt-1 text-slate-500">
              Factual India travel advice, verified knowledge base, and safety tools. No bookings, no payments, no sponsored listings.
            </p>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/privacy" className="hover:text-slate-200 transition-colors">
              Privacy Policy
            </Link>
            <Link to="/terms" className="hover:text-slate-200 transition-colors">
              Terms and Conditions
            </Link>
            <a href="tel:112" className="flex items-center gap-1 text-amber-500 hover:underline">
              <PhoneCall className="w-3.5 h-3.5" />
              <span>SOS: 112</span>
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};
