import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { PublicLayout } from './components/layout/PublicLayout';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { VerifyEmailPage } from './pages/VerifyEmailPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';
import { PrivacyPolicyPage } from './pages/PrivacyPolicyPage';
import { TermsPage } from './pages/TermsPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { Loader2, MessageSquare, LogOut, Compass } from 'lucide-react';

const queryClient = new QueryClient();

// Protected Route Guard
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Simple App Shell Placeholder for F4 (expanded in F5)
const AppShellPlaceholder: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      <header className="h-14 border-b border-slate-800 bg-slate-900 px-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-brand-600 flex items-center justify-center text-white">
            <Compass className="w-4 h-4" />
          </div>
          <span className="font-semibold text-sm">SafarSathi Assistant</span>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <span className="text-slate-400">{user?.email}</span>
          <button
            onClick={() => logout()}
            className="flex items-center gap-1 px-2.5 py-1 rounded-md border border-slate-700 hover:bg-slate-800 text-slate-300 transition-colors cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Log out</span>
          </button>
        </div>
      </header>
      <main className="flex-1 max-w-4xl mx-auto w-full p-6 flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-md bg-brand-950 border border-brand-800 text-brand-400 flex items-center justify-center mb-4">
          <MessageSquare className="w-6 h-6" />
        </div>
        <h1 className="text-xl font-bold text-white">Welcome, {user?.email}</h1>
        <p className="mt-2 text-xs text-slate-400 max-w-md">
          Authentication and account foundation initialized. Chat stream, trip planner, and offline emergency hub are connected in the upcoming Step F5.
        </p>
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Layout Routes */}
            <Route element={<PublicLayout />}>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/signup" element={<SignupPage />} />
              <Route path="/verify-email" element={<VerifyEmailPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
              <Route path="/privacy" element={<PrivacyPolicyPage />} />
              <Route path="/terms" element={<TermsPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Route>

            {/* Authenticated Routes */}
            <Route
              path="/app/*"
              element={
                <ProtectedRoute>
                  <AppShellPlaceholder />
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
