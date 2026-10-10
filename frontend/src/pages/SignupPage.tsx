import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus, AlertCircle, CheckCircle2, Loader2, Mail } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ApiError } from '../api/client';

export const SignupPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const { signup, loginAsDemo } = useAuth();
  const navigate = useNavigate();

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);

    try {
      const res = await signup(email, password);
      setSuccessMessage(res.message || 'Verification email sent. Please check your inbox.');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.data.detail || 'Signup failed. This email may already be in use.');
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md p-8 rounded-lg bg-slate-900 border border-slate-800 shadow-xl">
        <div className="mb-6 text-center">
          <div className="w-10 h-10 rounded-md bg-brand-600/10 border border-brand-500/20 text-brand-400 mx-auto flex items-center justify-center mb-3">
            <UserPlus className="w-5 h-5" />
          </div>
          <h1 className="text-xl font-bold text-white">Create your account</h1>
          <p className="mt-1 text-xs text-slate-400">
            Keep your itineraries synchronized across devices safely.
          </p>
        </div>

        {successMessage ? (
          <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-center space-y-3">
            <div className="w-10 h-10 rounded-md bg-emerald-950 border border-emerald-800 text-emerald-400 mx-auto flex items-center justify-center">
              <Mail className="w-5 h-5" />
            </div>
            <h2 className="text-sm font-semibold text-white">Verify your email address</h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              We sent a verification link to <strong className="text-white">{email}</strong>.
            </p>
            <p className="text-xs text-slate-500">
              In development mode, copy the link printed in your terminal console.
            </p>
            <div className="pt-2">
              <Link
                to="/login"
                className="inline-block py-2 px-4 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
              >
                Return to log in
              </Link>
            </div>
          </div>
        ) : (
          <>
            {error && (
              <div className="mb-4 p-3 rounded-md bg-red-950/50 border border-red-900/60 text-red-300 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5" htmlFor="signup-email">
                  Email Address
                </label>
                <input
                  id="signup-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-500 text-sm focus:border-brand-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5" htmlFor="signup-password">
                  Password (Minimum 8 characters)
                </label>
                <input
                  id="signup-password"
                  type="password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-500 text-sm focus:border-brand-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5" htmlFor="signup-confirm-password">
                  Confirm Password
                </label>
                <input
                  id="signup-confirm-password"
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-500 text-sm focus:border-brand-500 transition-colors"
                />
              </div>

              <div className="p-3 rounded-md bg-slate-950 border border-slate-800/80 text-[11px] text-slate-400 space-y-1">
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                  <span>Argon2id password protection</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                  <span>No commercial marketing emails</span>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || demoLoading}
                className="w-full py-2.5 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 disabled:text-slate-500 text-white font-medium text-sm flex items-center justify-center gap-2 transition-colors cursor-pointer"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Registering account...</span>
                  </>
                ) : (
                  <span>Create account</span>
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
              <span>Already have an account? </span>
              <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium transition-colors">
                Log in
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
