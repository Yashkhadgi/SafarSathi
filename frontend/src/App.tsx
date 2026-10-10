import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { PublicLayout } from './components/layout/PublicLayout';
import { AppLayout } from './components/layout/AppLayout';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { VerifyEmailPage } from './pages/VerifyEmailPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';
import { PrivacyPolicyPage } from './pages/PrivacyPolicyPage';
import { TermsPage } from './pages/TermsPage';
import { NotFoundPage } from './pages/NotFoundPage';

// Authenticated P0 and P1 Pages
import { ChatPage } from './pages/ChatPage';
import { ItineraryPage } from './pages/ItineraryPage';
import { BudgetPage } from './pages/BudgetPage';
import { TransportPage } from './pages/TransportPage';
import { ContactsPage } from './pages/ContactsPage';
import { SettingsPage } from './pages/SettingsPage';
import { ProfilePage } from './pages/ProfilePage';
import { SavedTripsPage } from './pages/SavedTripsPage';
import { WeatherHoursNearMePage } from './pages/WeatherHoursNearMePage';
import { PhrasebookPage } from './pages/PhrasebookPage';
import { SafetyGuidePage } from './pages/SafetyGuidePage';
import { FairPricingPage } from './pages/FairPricingPage';
import { TransportStayPage } from './pages/TransportStayPage';
import { CultureFoodPage } from './pages/CultureFoodPage';
import { PlanningOptimizerPage } from './pages/PlanningOptimizerPage';
import { ChecklistsPage } from './pages/ChecklistsPage';
import { ExportPage } from './pages/ExportPage';
import { Loader2 } from 'lucide-react';

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

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Routes */}
            <Route element={<PublicLayout />}>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/signup" element={<SignupPage />} />
              <Route path="/verify-email" element={<VerifyEmailPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
              <Route path="/privacy" element={<PrivacyPolicyPage />} />
              <Route path="/terms" element={<TermsPage />} />
              <Route path="/404" element={<NotFoundPage />} />
            </Route>

            {/* Authenticated Routes with App Layout */}
            <Route
              path="/app"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ChatPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/itinerary"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ItineraryPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/budget"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <BudgetPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/transport"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <TransportPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/contacts"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ContactsPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/settings"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <SettingsPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/profile"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ProfilePage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/trips"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <SavedTripsPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/realtime"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <WeatherHoursNearMePage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/phrasebook"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <PhrasebookPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/safety"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <SafetyGuidePage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/fair-prices"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <FairPricingPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/transit-stay"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <TransportStayPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/culture"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <CultureFoodPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/planner"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <PlanningOptimizerPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/checklists"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ChecklistsPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/export"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ExportPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />

            {/* Catch-all 404 */}
            <Route path="*" element={<Navigate to="/404" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
