import React, { useEffect, useState } from 'react';
import { 
  Settings, 
  KeyRound, 
  ShieldCheck, 
  Smartphone, 
  FileDown, 
  Trash2, 
  AlertCircle, 
  CheckCircle2, 
  Loader2 
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiGet, apiPost, apiDelete, ApiError } from '../api/client';
import { useAuth } from '../context/AuthContext';

interface SessionItem {
  id: string;
  ip_address?: string;
  user_agent?: string;
  device_label?: string;
  last_seen_at: string;
  created_at: string;
}

export const SettingsPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Password Change State
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [pwSuccess, setPwSuccess] = useState(false);
  const [pwLoading, setPwLoading] = useState(false);
  const [pwError, setPwError] = useState<string | null>(null);

  // Sessions State
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [sessionLoading, setSessionLoading] = useState(true);

  // Delete Account State
  const [deletePassword, setDeletePassword] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const fetchSessions = async () => {
    try {
      const data = await apiGet<SessionItem[]>('/auth/sessions');
      setSessions(Array.isArray(data) ? data : []);
    } catch {
      // Ignore session fetch error
    } finally {
      setSessionLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwError(null);
    setPwSuccess(false);

    if (newPassword.length < 8) {
      setPwError('New password must be at least 8 characters long.');
      return;
    }

    setPwLoading(true);

    try {
      await apiPost('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPwSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
    } catch (err) {
      if (err instanceof ApiError) {
        setPwError(err.data.detail || 'Current password incorrect.');
      } else {
        setPwError('Failed to change password.');
      }
    } finally {
      setPwLoading(false);
    }
  };

  const handleRevokeSession = async (id: string) => {
    try {
      await apiDelete(`/auth/sessions/${id}`);
      setSessions((prev) => prev.filter((s) => s.id !== id));
    } catch {
      // Ignore revoke error
    }
  };

  const handleLogoutAll = async () => {
    try {
      await apiPost('/auth/logout-all');
      await logout();
      navigate('/login');
    } catch {
      // Ignore
    }
  };

  const handleExportData = async () => {
    try {
      const data = await apiGet<unknown>('/auth/export-data');
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `safarsathi_export_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert('Could not export account data');
    }
  };

  const handleDeleteAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    setDeleteError(null);
    setDeleteLoading(true);

    try {
      await apiPost('/auth/account/delete', { password: deletePassword });
      await logout();
      navigate('/login');
    } catch (err) {
      if (err instanceof ApiError) {
        setDeleteError(err.data.detail || 'Incorrect password.');
      } else {
        setDeleteError('Failed to delete account.');
      }
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Account & Privacy Settings</h1>
        <p className="mt-1 text-xs text-slate-400">
          Manage your credentials, active login devices, data exports, and permanent deletion.
        </p>
      </div>

      {/* Account Info Card */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-brand-400" />
          <span>Account Overview</span>
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-slate-400 block">Registered Email</span>
            <strong className="text-slate-200">{user?.email}</strong>
          </div>
          <div>
            <span className="text-slate-400 block">Account Status</span>
            <span className="inline-block px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-300 text-[10px] font-medium">
              Verified & Active
            </span>
          </div>
        </div>
      </div>

      {/* Password Change Card */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <KeyRound className="w-4 h-4 text-brand-400" />
          <span>Change Password</span>
        </h2>

        {pwSuccess && (
          <div className="p-3 rounded-md bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>Password updated successfully.</span>
          </div>
        )}

        {pwError && (
          <div className="p-3 rounded-md bg-red-950/60 border border-red-900 text-red-200 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{pwError}</span>
          </div>
        )}

        <form onSubmit={handlePasswordChange} className="space-y-4 max-w-md">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="cur-pass">
              Current Password
            </label>
            <input
              id="cur-pass"
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="new-pass">
              New Password (Min 8 chars)
            </label>
            <input
              id="new-pass"
              type="password"
              required
              minLength={8}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <button
            type="submit"
            disabled={pwLoading}
            className="py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium transition-colors cursor-pointer"
          >
            {pwLoading ? 'Updating...' : 'Update Password'}
          </button>
        </form>
      </div>

      {/* Active Login Sessions */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Smartphone className="w-4 h-4 text-brand-400" />
            <span>Active Login Sessions</span>
          </h2>

          <button
            onClick={handleLogoutAll}
            className="px-3 py-1 rounded-md border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-medium transition-colors"
          >
            Log Out All Other Devices
          </button>
        </div>

        {sessionLoading ? (
          <div className="p-4 text-center text-xs text-slate-500">Loading sessions...</div>
        ) : sessions.length > 0 ? (
          <div className="space-y-2">
            {sessions.map((s) => (
              <div key={s.id} className="p-3.5 rounded-md bg-slate-950 border border-slate-800 flex items-center justify-between text-xs">
                <div>
                  <div className="font-semibold text-slate-200">
                    {s.device_label || 'Web Browser'}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    IP: {s.ip_address || 'Localhost'} • Last active: {new Date(s.last_seen_at).toLocaleTimeString()}
                  </div>
                </div>

                <button
                  onClick={() => handleRevokeSession(s.id)}
                  className="px-2.5 py-1 rounded-md border border-slate-800 hover:bg-red-950/60 hover:text-red-300 text-slate-400 text-xs transition-colors"
                >
                  Revoke
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500">Only your current device session is active.</p>
        )}
      </div>

      {/* Export Data Package */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <FileDown className="w-4 h-4 text-brand-400" />
          <span>Export All Data (GDPR / Indian DPDP Compliant)</span>
        </h2>
        <p className="text-xs text-slate-400 leading-relaxed">
          Download a full archive of your profile preferences, saved itineraries, chat history, and feedback in standard JSON format.
        </p>
        <button
          onClick={handleExportData}
          className="py-2 px-4 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-2 transition-colors cursor-pointer"
        >
          <FileDown className="w-4 h-4" />
          <span>Download JSON Export</span>
        </button>
      </div>

      {/* Permanent Account Deletion */}
      <div className="p-6 rounded-lg bg-red-950/30 border border-red-900/60 space-y-3">
        <h2 className="text-sm font-semibold text-red-200 flex items-center gap-2">
          <Trash2 className="w-4 h-4 text-red-400" />
          <span>Permanently Delete Account</span>
        </h2>
        <p className="text-xs text-red-300/80 leading-relaxed">
          This immediately cascades and permanently deletes all conversations, messages, saved trips, and encrypted trusted contacts from our primary database. This action cannot be undone.
        </p>
        <button
          onClick={() => setShowDeleteModal(true)}
          className="py-2 px-4 rounded-md bg-red-900 hover:bg-red-800 text-white text-xs font-medium transition-colors cursor-pointer"
        >
          Delete My Account
        </button>
      </div>

      {/* Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md rounded-lg bg-slate-900 border border-red-800 p-6 space-y-4">
            <h3 className="text-sm font-bold text-white">Confirm Permanent Deletion</h3>
            <p className="text-xs text-slate-300">
              Please enter your password to confirm that you want to delete your account and all associated data.
            </p>

            {deleteError && (
              <div className="p-2.5 rounded-md bg-red-950 border border-red-900 text-red-200 text-xs">
                {deleteError}
              </div>
            )}

            <form onSubmit={handleDeleteAccount} className="space-y-4">
              <input
                type="password"
                required
                value={deletePassword}
                onChange={(e) => setDeletePassword(e.target.value)}
                placeholder="Enter your password"
                className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-red-500"
              />

              <div className="flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowDeleteModal(false)}
                  className="py-1.5 px-3 rounded-md bg-slate-800 text-slate-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={deleteLoading}
                  className="py-1.5 px-4 rounded-md bg-red-600 hover:bg-red-700 text-white text-xs font-semibold cursor-pointer"
                >
                  {deleteLoading ? 'Deleting...' : 'Permanently Delete'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
