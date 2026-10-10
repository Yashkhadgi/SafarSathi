import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { apiPost, ApiError } from '../api/client';

export const VerifyEmailPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setErrorMessage('No verification token provided in the URL.');
      return;
    }

    const verify = async () => {
      try {
        await apiPost('/auth/verify-email', { token });
        setStatus('success');
      } catch (err) {
        setStatus('error');
        if (err instanceof ApiError) {
          setErrorMessage(err.data.detail || 'The verification link is invalid or has expired.');
        } else {
          setErrorMessage('Could not verify email. Please try again.');
        }
      }
    };

    verify();
  }, [token]);

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md p-8 rounded-lg bg-slate-900 border border-slate-800 shadow-xl text-center">
        {status === 'loading' && (
          <div className="space-y-4">
            <Loader2 className="w-10 h-10 animate-spin text-brand-400 mx-auto" />
            <h1 className="text-lg font-semibold text-white">Verifying email address...</h1>
            <p className="text-xs text-slate-400">Please wait while we confirm your account security token.</p>
          </div>
        )}

        {status === 'success' && (
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-md bg-emerald-950 border border-emerald-800 text-emerald-400 mx-auto flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h1 className="text-xl font-bold text-white">Email Verified Successfully</h1>
            <p className="text-xs text-slate-300">
              Your SafarSathi account is now active and ready to use.
            </p>
            <div className="pt-4">
              <Link
                to="/login"
                className="inline-block w-full py-2.5 px-4 rounded-md bg-brand-600 hover:bg-brand-700 text-white font-medium text-sm transition-colors"
              >
                Proceed to Log In
              </Link>
            </div>
          </div>
        )}

        {status === 'error' && (
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-md bg-red-950 border border-red-800 text-red-400 mx-auto flex items-center justify-center">
              <AlertCircle className="w-6 h-6" />
            </div>
            <h1 className="text-xl font-bold text-white">Verification Failed</h1>
            <p className="text-xs text-red-300">{errorMessage}</p>
            <div className="pt-4 flex flex-col gap-2">
              <Link
                to="/login"
                className="inline-block py-2.5 px-4 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm transition-colors"
              >
                Go to Login
              </Link>
              <Link
                to="/signup"
                className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
              >
                Request a new account
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
