import React, { useState } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { KeyRound, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { apiPost, ApiError } from '../api/client';

export const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');

    if (!token) {
      setStatus('error');
      setErrorMessage('Missing password reset token in URL.');
      return;
    }

    if (newPassword.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    setLoading(true);

    try {
      await apiPost('/auth/reset-password', {
        token,
        new_password: newPassword,
      });
      setStatus('success');
      setTimeout(() => navigate('/login'), 3000);
    } catch (err) {
      setStatus('error');
      if (err instanceof ApiError) {
        setErrorMessage(err.data.detail || 'Reset token is invalid or has expired.');
      } else {
        setErrorMessage('Failed to reset password. Please try again.');
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
          <h1 className="text-xl font-bold text-white">Choose a new password</h1>
          <p className="mt-1 text-xs text-slate-400">
            Enter a strong new password for your account.
          </p>
        </div>

        {status === 'success' ? (
          <div className="p-4 rounded-md bg-slate-950 border border-slate-800 text-center space-y-3">
            <div className="w-10 h-10 rounded-md bg-emerald-950 border border-emerald-800 text-emerald-400 mx-auto flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <h2 className="text-sm font-semibold text-white">Password Updated</h2>
            <p className="text-xs text-slate-300">
              Your password has been changed. Redirecting to login page...
            </p>
            <div className="pt-2">
              <Link
                to="/login"
                className="inline-block py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 text-white text-xs font-medium transition-colors"
              >
                Log In Now
              </Link>
            </div>
          </div>
        ) : (
          <>
            {errorMessage && (
              <div className="mb-4 p-3 rounded-md bg-red-950/50 border border-red-900/60 text-red-300 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{errorMessage}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5" htmlFor="new-password">
                  New Password (Minimum 8 characters)
                </label>
                <input
                  id="new-password"
                  type="password"
                  required
                  minLength={8}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-500 text-sm focus:border-brand-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5" htmlFor="confirm-new-password">
                  Confirm New Password
                </label>
                <input
                  id="confirm-new-password"
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
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
                    <span>Updating password...</span>
                  </>
                ) : (
                  <span>Reset password</span>
                )}
              </button>

              <div className="pt-2 text-center">
                <Link to="/login" className="text-xs text-slate-400 hover:text-slate-200 transition-colors">
                  Cancel and log in
                </Link>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
};
