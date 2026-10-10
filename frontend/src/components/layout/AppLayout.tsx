import React, { useState } from 'react';
import { 
  ShieldAlert, 
  Compass, 
  MapPin, 
  Calendar, 
  DollarSign, 
  Navigation, 
  Users, 
  Settings, 
  MessageSquare, 
  Bookmark, 
  CloudSun, 
  BookOpen, 
  Luggage, 
  FileDown, 
  LogOut, 
  PhoneCall, 
  AlertTriangle, 
  X 
} from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sosModalOpen, setSosModalOpen] = useState(false);

  const navItems = [
    { label: 'Travel Assistant', path: '/app', icon: MessageSquare },
    { label: 'Saved Trips', path: '/app/trips', icon: Bookmark },
    { label: 'Settings & Profile', path: '/app/settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100">
      {/* Sidebar Navigation */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/90 flex flex-col shrink-0">
        {/* Brand */}
        <div className="h-16 px-4 border-b border-slate-800 flex items-center justify-between">
          <Link to="/app" className="flex items-center gap-2 text-slate-100 font-semibold text-base hover:text-brand-400 transition-colors">
            <div className="w-8 h-8 rounded-md bg-brand-600 flex items-center justify-center text-white">
              <Compass className="w-5 h-5" />
            </div>
            <span>SafarSathi</span>
          </Link>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">v2.0</span>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = location.pathname === item.path || (item.path === '/app' && location.pathname === '/');
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-md text-xs font-medium transition-colors ${
                  active
                    ? 'bg-brand-600 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="truncate">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* SOS Quick Button & User Profile */}
        <div className="p-3 border-t border-slate-800 space-y-2">
          <button
            onClick={() => setSosModalOpen(true)}
            className="w-full py-2 px-3 rounded-md bg-red-950/80 hover:bg-red-900 border border-red-800 text-red-200 text-xs font-semibold flex items-center justify-center gap-2 transition-colors cursor-pointer"
          >
            <ShieldAlert className="w-4 h-4 text-red-400" />
            <span>Emergency SOS (112)</span>
          </button>

          <div className="pt-2 flex items-center justify-between text-xs text-slate-400">
            <span className="truncate max-w-[140px]" title={user?.email}>{user?.email}</span>
            <button
              onClick={() => { logout(); navigate('/login'); }}
              className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
              title="Log out"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top Emergency Notice Bar */}
        <div className="bg-slate-900 border-b border-slate-800 text-[11px] px-6 py-2 flex items-center justify-between text-slate-400">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>All travel data verified with source dates. Zero commercial commissions.</span>
          </div>
          <div className="flex items-center gap-4">
            <span>National Emergency: <strong className="text-slate-200">112</strong></span>
            <span>Ambulance: <strong className="text-slate-200">108</strong></span>
          </div>
        </div>

        {/* Page Content */}
        <div className="flex-1 p-6 max-w-6xl w-full mx-auto">
          {children}
        </div>
      </main>

      {/* Persistent SOS Modal */}
      {sosModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-lg bg-slate-900 border border-red-800 p-6 shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2.5 text-red-400 font-bold text-lg">
                <AlertTriangle className="w-6 h-6" />
                <span>Emergency SOS Mode</span>
              </div>
              <button
                onClick={() => setSosModalOpen(false)}
                className="p-1 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs text-slate-300">
              <p className="text-slate-400">
                If you or someone nearby is in immediate danger, contact official Indian emergency response services:
              </p>

              <div className="grid grid-cols-2 gap-3">
                <a
                  href="tel:112"
                  className="p-4 rounded-md bg-red-950 border border-red-800 hover:bg-red-900 flex flex-col items-center justify-center gap-1 text-center transition-colors"
                >
                  <PhoneCall className="w-5 h-5 text-red-400" />
                  <span className="text-sm font-bold text-white">Call 112</span>
                  <span className="text-[10px] text-red-300">National Emergency (All in One)</span>
                </a>

                <a
                  href="tel:108"
                  className="p-4 rounded-md bg-slate-950 border border-slate-800 hover:bg-slate-800 flex flex-col items-center justify-center gap-1 text-center transition-colors"
                >
                  <PhoneCall className="w-5 h-5 text-amber-400" />
                  <span className="text-sm font-bold text-white">Call 108</span>
                  <span className="text-[10px] text-slate-400">Medical Ambulance</span>
                </a>

                <a
                  href="tel:1091"
                  className="p-4 rounded-md bg-slate-950 border border-slate-800 hover:bg-slate-800 flex flex-col items-center justify-center gap-1 text-center transition-colors"
                >
                  <PhoneCall className="w-5 h-5 text-blue-400" />
                  <span className="text-sm font-bold text-white">Call 1091</span>
                  <span className="text-[10px] text-slate-400">Women Helpline</span>
                </a>

                <a
                  href="tel:1363"
                  className="p-4 rounded-md bg-slate-950 border border-slate-800 hover:bg-slate-800 flex flex-col items-center justify-center gap-1 text-center transition-colors"
                >
                  <PhoneCall className="w-5 h-5 text-emerald-400" />
                  <span className="text-sm font-bold text-white">Call 1363</span>
                  <span className="text-[10px] text-slate-400">Tourist Helpline (Govt of India)</span>
                </a>
              </div>

              <div className="p-3 rounded-md bg-slate-950 border border-slate-800 text-[11px] text-slate-400">
                <strong className="text-slate-200 block mb-1">Key Hindi Emergency Phrases:</strong>
                <ul className="list-disc pl-4 space-y-0.5">
                  <li><strong>Mujhe madad chahiye:</strong> I need help</li>
                  <li><strong>Doctor ko bulao:</strong> Call a doctor</li>
                  <li><strong>Police ko bulao:</strong> Call the police</li>
                  <li><strong>Yahan durghatna hui hai:</strong> There has been an accident here</li>
                </ul>
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between">
              <Link
                to="/app/contacts"
                onClick={() => setSosModalOpen(false)}
                className="text-xs text-brand-400 hover:underline"
              >
                Send alert to Trusted Contacts
              </Link>
              <button
                onClick={() => setSosModalOpen(false)}
                className="py-2 px-4 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
              >
                Close SOS
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
