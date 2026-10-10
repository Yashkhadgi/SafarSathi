import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LogIn, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ApiError } from '../api/client';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const { login, loginAsDemo } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login(email, password);
      navigate('/app');
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 429) {
          setError(err.data.detail || 'Too many attempts. Account temporarily locked for 5 minutes.');
        } else {
          setError(err.data.detail || 'Invalid email or password.');
        }
      } else {
        setError('An unexpected error occurred. Please check your connection.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError(null);
    setDemoLoading(true);
    try {
      await loginAsDemo();
      navigate('/app');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.data.detail || 'Could not access demo account.');
      } else {
        setError('Unexpected error accessing demo mode.');
      }
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md p-8 rounded-lg bg-slate-900 border border-slate-800 shadow-xl">
        <div className="mb-6 text-center">
          <div className="w-10 h-10 rounded-md bg-brand-600/10 border border-brand-500/20 text-brand-400 mx-auto flex items-center justify-center mb-3">
            <LogIn className="w-5 h-5" />
          </div>
          <h1 className="text-xl font-bold text-white">Log in to SafarSathi</h1>
          <p className="mt-1 text-xs text-slate-400">
            Access your saved itineraries, trip versions, and preferences.
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-md bg-red-950/50 border border-red-900/60 text-red-300 text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5" htmlFor="login-email">
              Email Address
            </label>
            <input
              id="login-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-500 text-sm focus:border-brand-500 transition-colors"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-medium text-slate-300" htmlFor="login-password">
                Password
              </label>
              <Link to="/forgot-password" className="text-xs text-brand-400 hover:text-brand-300 transition-colors">
                Forgot password?
              </Link>
            </div>
            <input
              id="login-password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-500 text-sm focus:border-brand-500 transition-colors"
            />
          </div>

          <button
            type="submit"
            disabled={loading || demoLoading}
            className="w-full py-2.5 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 disabled:text-slate-500 text-white font-medium text-sm flex items-center justify-center gap-2 transition-colors cursor-pointer"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Authenticating...</span>
              </>
            ) : (
              <span>Log in</span>
            )}
          </button>
        </form>

        <div className="relative my-5">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-800" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-slate-900 px-2 text-slate-500">Quick Testing</span>
          </div>
        </div>

        <button
          type="button"
          onClick={handleDemoLogin}
          disabled={loading || demoLoading}
          className="w-full py-2.5 px-4 rounded-md bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-100 font-medium text-sm flex items-center justify-center gap-2 transition-colors cursor-pointer border border-slate-700"
        >
          {demoLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Entering Demo Mode...</span>
            </>
          ) : (
            <span>Explore as Demo Traveler (1-Click)</span>
          )}
        </button>

        <div className="mt-6 pt-6 border-t border-slate-800 text-center text-xs text-slate-400">
          <span>Do not have an account? </span>
          <Link to="/signup" className="text-brand-400 hover:text-brand-300 font-medium transition-colors">
            Sign up
          </Link>
        </div>
      </div>
    </div>
  );
};
