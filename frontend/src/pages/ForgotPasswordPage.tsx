import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { KeyRound, Mail, AlertCircle, Loader2 } from 'lucide-react';
import { apiPost, ApiError } from '../api/client';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await apiPost('/auth/forgot-password', { email });
      setSubmitted(true);
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        setError('Too many requests. Please wait a few moments before trying again.');
      } else {
        // Generic message prevents user enumeration
        setSubmitted(true);
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
            <KeyRound className="w-5 h-5" />
          </div>
          <h1 className="text-xl font-bold text-white">Reset your password</h1>
          <p className="mt-1 text-xs text-slate-400">
            Enter your account email to receive a password reset link.
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-md bg-red-950/50 border border-red-900/60 text-red-300 text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {submitted ? (
          <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-center space-y-3">
            <div className="w-10 h-10 rounded-md bg-brand-950 border border-brand-800 text-brand-400 mx-auto flex items-center justify-center">
              <Mail className="w-5 h-5" />
            </div>
            <h2 className="text-sm font-semibold text-white">Check your email</h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              If an active account exists for <strong className="text-white">{email}</strong>, you will receive a password reset link shortly.
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
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5" htmlFor="forgot-email">
                Account Email
              </label>
              <input
                id="forgot-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-500 text-sm focus:border-brand-500 transition-colors"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 disabled:text-slate-500 text-white font-medium text-sm flex items-center justify-center gap-2 transition-colors cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Submitting request...</span>
                </>
              ) : (
                <span>Send reset link</span>
              )}
            </button>

            <div className="pt-2 text-center">
              <Link to="/login" className="text-xs text-slate-400 hover:text-slate-200 transition-colors">
                Back to log in
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
