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
  Loader2, 
  User, 
  Users, 
  Globe, 
  Lock, 
  Phone, 
  Send, 
  Plus, 
  Save 
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiGet, apiPost, apiPut, apiDelete, ApiError } from '../api/client';
import { useAuth } from '../context/AuthContext';

interface SessionItem {
  id: string;
  ip_address?: string;
  user_agent?: string;
  device_label?: string;
  last_seen_at: string;
  created_at: string;
}

interface Contact {
  id: string;
  name: string;
  phone: string;
  relationship?: string;
  created_at: string;
}

interface ProfileData {
  home_city?: string;
  diet_preference?: string;
  allergies?: string[];
  travel_style?: string;
  budget_range?: string;
  mobility_notes?: string;
  interests?: string[];
  consent_location?: boolean;
  consent_contacts?: boolean;
}

export const SettingsPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'profile' | 'contacts' | 'language' | 'security' | 'privacy'>('profile');

  // Profile State
  const [homeCity, setHomeCity] = useState('');
  const [diet, setDiet] = useState('all');
  const [allergiesInput, setAllergiesInput] = useState('');
  const [travelStyle, setTravelStyle] = useState('normal');
  const [budgetRange, setBudgetRange] = useState('mid');
  const [mobilityNotes, setMobilityNotes] = useState('');
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState(false);

  // Contacts State
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [contactsLoading, setContactsLoading] = useState(true);
  const [contactName, setContactName] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [contactRelation, setContactRelation] = useState('Family');
  const [contactSubmitting, setContactSubmitting] = useState(false);
  const [contactError, setContactError] = useState<string | null>(null);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);

  // Language State
  const [preferredLanguage, setPreferredLanguage] = useState('hi');
  const [speechSpeed, setSpeechSpeed] = useState('1.0');

  // Password Change State
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [pwSuccess, setPwSuccess] = useState(false);
  const [pwLoading, setPwLoading] = useState(false);
  const [pwError, setPwError] = useState<string | null>(null);

  // Sessions State
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [sessionLoading, setSessionLoading] = useState(true);

  // Privacy State
  const [consentLocation, setConsentLocation] = useState(false);
  const [consentContacts, setConsentContacts] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Fetch initial data
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const data = await apiGet<ProfileData>('/profile');
        if (data) {
          setHomeCity(data.home_city || '');
          setDiet(data.diet_preference || 'all');
          setAllergiesInput(Array.isArray(data.allergies) ? data.allergies.join(', ') : '');
          setTravelStyle(data.travel_style || 'normal');
          setBudgetRange(data.budget_range || 'mid');
          setMobilityNotes(data.mobility_notes || '');
          setConsentLocation(Boolean(data.consent_location));
          setConsentContacts(Boolean(data.consent_contacts));
        }
      } catch {
        // Fallback
      }
    };

    const loadContacts = async () => {
      try {
        const data = await apiGet<Contact[]>('/trusted-contacts');
        setContacts(Array.isArray(data) ? data : []);
      } catch {
        // Fallback
      } finally {
        setContactsLoading(false);
      }
    };

    const loadSessions = async () => {
      try {
        const data = await apiGet<SessionItem[]>('/auth/sessions');
        setSessions(Array.isArray(data) ? data : []);
      } catch {
        // Fallback
      } finally {
        setSessionLoading(false);
      }
    };

    loadProfile();
    loadContacts();
    loadSessions();

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => setCoords(null)
      );
    }
  }, []);

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileSaving(true);
    setProfileSuccess(false);

    const allergies = allergiesInput
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

    try {
      await apiPut('/profile', {
        home_city: homeCity,
        diet_preference: diet,
        allergies,
        travel_style: travelStyle,
        budget_range: budgetRange,
        mobility_notes: mobilityNotes,
        consent_location: consentLocation,
        consent_contacts: consentContacts,
      });
      setProfileSuccess(true);
      setTimeout(() => setProfileSuccess(false), 4000);
    } catch {
      // Error
    } finally {
      setProfileSaving(false);
    }
  };

  const handleAddContact = async (e: React.FormEvent) => {
    e.preventDefault();
    setContactError(null);
    setContactSubmitting(true);

    try {
      const created = await apiPost<Contact>('/trusted-contacts', {
        name: contactName,
        phone: contactPhone,
        relationship: contactRelation,
      });
      setContacts((prev) => [created, ...prev]);
      setContactName('');
      setContactPhone('');
    } catch (err) {
      if (err instanceof ApiError) {
        setContactError(err.data.detail || 'Could not save contact.');
      } else {
        setContactError('Failed to add contact.');
      }
    } finally {
      setContactSubmitting(false);
    }
  };

  const handleDeleteContact = async (id: string) => {
    try {
      await apiDelete(`/trusted-contacts/${id}`);
      setContacts((prev) => prev.filter((c) => c.id !== id));
    } catch {
      // Error
    }
  };

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
      // Error
    }
  };

  const handleLogoutAll = async () => {
    try {
      await apiPost('/auth/logout-all');
      await logout();
      navigate('/login');
    } catch {
      // Error
    }
  };

  const handleExportData = async () => {
    try {
      const data = await apiGet<unknown>('/auth/export-data');
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `safarsathi_user_data_${new Date().toISOString().slice(0, 10)}.json`;
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
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Settings & Preferences</h1>
        <p className="mt-1 text-xs text-slate-400">
          Configure your travel profile, encrypted emergency contacts, security sessions, and privacy.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 space-x-2">
        {[
          { id: 'profile', label: 'Traveler Profile', icon: User },
          { id: 'contacts', label: 'Trusted Contacts', icon: Users },
          { id: 'language', label: 'Language & Audio', icon: Globe },
          { id: 'security', label: 'Security & Devices', icon: Smartphone },
          { id: 'privacy', label: 'Privacy & Data', icon: ShieldCheck },
        ].map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-colors cursor-pointer ${
                active
                  ? 'border-brand-500 text-brand-400 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Profile */}
      {activeTab === 'profile' && (
        <form onSubmit={handleProfileSave} className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-6">
          {profileSuccess && (
            <div className="p-3 rounded-md bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>Travel preferences updated successfully.</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="set-home-city">
                Home City (Origin for transit tools)
              </label>
              <input
                id="set-home-city"
                type="text"
                value={homeCity}
                onChange={(e) => setHomeCity(e.target.value)}
                placeholder="e.g. Nagpur, Delhi, Bengaluru"
                className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="set-diet">
                Dietary Preference
              </label>
              <select
                id="set-diet"
                value={diet}
                onChange={(e) => setDiet(e.target.value)}
                className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
              >
                <option value="all">No strict dietary restrictions</option>
                <option value="veg">Vegetarian (Strict)</option>
                <option value="vegan">Vegan (Plant-based)</option>
                <option value="jain">Jain (No root vegetables/onion/garlic)</option>
                <option value="halal">Halal Certified</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="set-allergies">
                Food Allergies (Comma separated)
              </label>
              <input
                id="set-allergies"
                type="text"
                value={allergiesInput}
                onChange={(e) => setAllergiesInput(e.target.value)}
                placeholder="e.g. Peanuts, Gluten, Dairy"
                className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="set-budget">
                Default Budget Tier
              </label>
              <select
                id="set-budget"
                value={budgetRange}
                onChange={(e) => setBudgetRange(e.target.value)}
                className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
              >
                <option value="budget">Budget (Hostels, public transit, street food)</option>
                <option value="mid">Mid-range (3-star hotels, cabs, restaurants)</option>
                <option value="luxury">Luxury (Heritage resorts, private chauffeur)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="set-mobility">
              Mobility & Accessibility Notes
            </label>
            <textarea
              id="set-mobility"
              rows={2}
              value={mobilityNotes}
              onChange={(e) => setMobilityNotes(e.target.value)}
              placeholder="e.g. Wheelchair access needed, avoid steep stair climbs, traveling with elderly"
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <button
            type="submit"
            disabled={profileSaving}
            className="py-2.5 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium flex items-center gap-2 transition-colors cursor-pointer"
          >
            {profileSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            <span>Save Traveler Profile</span>
          </button>
        </form>
      )}

      {/* Tab 2: Trusted Contacts */}
      {activeTab === 'contacts' && (
        <div className="space-y-6">
          <form onSubmit={handleAddContact} className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Plus className="w-4 h-4 text-brand-400" />
              <span>Add Emergency Contact (Encrypted at Rest)</span>
            </h2>

            {contactError && (
              <div className="p-3 rounded-md bg-red-950/60 border border-red-900 text-red-200 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{contactError}</span>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="con-name">Full Name</label>
                <input
                  id="con-name"
                  type="text"
                  required
                  value={contactName}
                  onChange={(e) => setContactName(e.target.value)}
                  placeholder="e.g. Ramesh Sharma"
                  className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="con-phone">Phone Number</label>
                <input
                  id="con-phone"
                  type="tel"
                  required
                  value={contactPhone}
                  onChange={(e) => setContactPhone(e.target.value)}
                  placeholder="+91 98765 43210"
                  className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="con-rel">Relationship</label>
                <select
                  id="con-rel"
                  value={contactRelation}
                  onChange={(e) => setContactRelation(e.target.value)}
                  className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
                >
                  <option value="Family">Family</option>
                  <option value="Spouse / Partner">Spouse / Partner</option>
                  <option value="Friend">Friend</option>
                  <option value="Guardian">Guardian</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={contactSubmitting}
              className="py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              {contactSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
              <span>Save Contact</span>
            </button>
          </form>

          {/* Contact List */}
          <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
            <h2 className="text-sm font-semibold text-white">Your Saved Contacts ({contacts.length})</h2>
            {contactsLoading ? (
              <div className="py-6 flex justify-center text-slate-500">
                <Loader2 className="w-5 h-5 animate-spin" />
              </div>
            ) : contacts.length === 0 ? (
              <p className="text-xs text-slate-400">No emergency contacts saved yet.</p>
            ) : (
              <div className="space-y-3">
                {contacts.map((c) => {
                  const mapLink = coords ? `https://maps.google.com/?q=${coords.lat},${coords.lng}` : '';
                  const sosMsg = encodeURIComponent(
                    `EMERGENCY ALERT: I need immediate assistance. My last reported location is: ${mapLink || 'GPS unavailable'}. Sent via SafarSathi.`
                  );
                  const cleanPhone = c.phone.replace(/[^0-9]/g, '');
                  const waUrl = `https://wa.me/${cleanPhone}?text=${sosMsg}`;
                  const smsUrl = `sms:${cleanPhone}?body=${sosMsg}`;

                  return (
                    <div key={c.id} className="p-3 rounded-md bg-slate-950 border border-slate-800 flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <strong className="text-xs text-white">{c.name}</strong>
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                            {c.relationship || 'Contact'}
                          </span>
                        </div>
                        <span className="text-xs text-slate-400 font-mono block mt-0.5">{c.phone}</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <a
                          href={waUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-2.5 py-1 rounded bg-emerald-950 hover:bg-emerald-900 border border-emerald-800 text-emerald-300 text-[11px] font-medium flex items-center gap-1 transition-colors"
                        >
                          <Send className="w-3 h-3" />
                          <span>WhatsApp SOS</span>
                        </a>
                        <a
                          href={smsUrl}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium flex items-center gap-1 transition-colors"
                        >
                          <Phone className="w-3 h-3" />
                          <span>SMS</span>
                        </a>
                        <button
                          onClick={() => handleDeleteContact(c.id)}
                          className="p-1 text-slate-500 hover:text-red-400 transition-colors"
                          title="Delete contact"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Language & Audio */}
      {activeTab === 'language' && (
        <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-6">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Globe className="w-4 h-4 text-brand-400" />
            <span>Regional Language & Audio Settings</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="lang-select">
                Default Regional Translation Language
              </label>
              <select
                id="lang-select"
                value={preferredLanguage}
                onChange={(e) => setPreferredLanguage(e.target.value)}
                className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
              >
                <option value="hi">Hindi (हिन्दी)</option>
                <option value="mr">Marathi (मराठी)</option>
                <option value="bn">Bengali (বাংলা)</option>
                <option value="ta">Tamil (தமிழ்)</option>
                <option value="te">Telugu (తెలుగు)</option>
                <option value="gu">Gujarati (ગુજરાતી)</option>
                <option value="kn">Kannada (ಕನ್ನಡ)</option>
                <option value="ml">Malayalam (മലയാളം)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="speech-rate">
                Phrase Audio Playback Speed
              </label>
              <select
                id="speech-rate"
                value={speechSpeed}
                onChange={(e) => setSpeechSpeed(e.target.value)}
                className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
              >
                <option value="0.8">0.8x (Slower, clear pronunciation)</option>
                <option value="1.0">1.0x (Normal)</option>
                <option value="1.2">1.2x (Faster)</option>
              </select>
            </div>
          </div>
          <p className="text-xs text-slate-400">
            Audio pronunciation uses native high-fidelity browser speech synthesis with automatic fallback.
          </p>
        </div>
      )}

      {/* Tab 4: Security & Devices */}
      {activeTab === 'security' && (
        <div className="space-y-6">
          {/* Password Change */}
          <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <KeyRound className="w-4 h-4 text-brand-400" />
              <span>Change Account Password</span>
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

            <form onSubmit={handlePasswordChange} className="space-y-3 max-w-md">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="cur-pass-tab">Current Password</label>
                <input
                  id="cur-pass-tab"
                  type="password"
                  required
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="new-pass-tab">New Password (Min 8 chars)</label>
                <input
                  id="new-pass-tab"
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

          {/* Active Sessions */}
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
                Revoke all other devices
              </button>
            </div>

            {sessionLoading ? (
              <div className="py-4 flex justify-center text-slate-500">
                <Loader2 className="w-5 h-5 animate-spin" />
              </div>
            ) : sessions.length === 0 ? (
              <p className="text-xs text-slate-400">No other active devices.</p>
            ) : (
              <div className="space-y-2">
                {sessions.map((s) => (
                  <div key={s.id} className="p-3 rounded-md bg-slate-950 border border-slate-800 flex items-center justify-between text-xs">
                    <div>
                      <strong className="text-slate-200 block">{s.device_label || 'Web Session'}</strong>
                      <span className="text-[11px] text-slate-500">IP: {s.ip_address || 'unknown'}</span>
                    </div>
                    <button
                      onClick={() => handleRevokeSession(s.id)}
                      className="px-2.5 py-1 rounded border border-red-900/60 text-red-400 hover:bg-red-950 text-[11px] transition-colors"
                    >
                      Revoke
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 5: Privacy & Data */}
      {activeTab === 'privacy' && (
        <div className="space-y-6">
          <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <FileDown className="w-4 h-4 text-brand-400" />
              <span>Export Account Data</span>
            </h2>
            <p className="text-xs text-slate-400">
              Download a complete JSON export of your profile, trip itineraries, and emergency contacts.
            </p>
            <button
              onClick={handleExportData}
              className="py-2 px-4 rounded-md border border-slate-700 hover:bg-slate-800 text-slate-200 text-xs font-medium flex items-center gap-2 transition-colors cursor-pointer"
            >
              <FileDown className="w-4 h-4 text-brand-400" />
              <span>Download JSON Archive</span>
            </button>
          </div>

          {/* Delete Account */}
          <div className="p-6 rounded-lg bg-red-950/20 border border-red-900/60 space-y-4">
            <h2 className="text-sm font-semibold text-red-300 flex items-center gap-2">
              <Trash2 className="w-4 h-4 text-red-400" />
              <span>Permanently Delete Account</span>
            </h2>
            <p className="text-xs text-red-200/80">
              This action permanently purges your credentials, encrypted contacts, chat histories, and saved trip versions from the server.
            </p>
            <button
              onClick={() => setShowDeleteModal(true)}
              className="py-2 px-4 rounded-md bg-red-900/80 hover:bg-red-800 text-white text-xs font-semibold transition-colors cursor-pointer"
            >
              Delete My Account
            </button>
          </div>

          {/* Delete Account Modal */}
          {showDeleteModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80">
              <div className="w-full max-w-md p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
                <h3 className="text-sm font-bold text-white">Confirm Account Deletion</h3>
                <p className="text-xs text-slate-400">
                  Please enter your password to permanently delete your account and all associated travel records.
                </p>

                {deleteError && (
                  <div className="p-2.5 rounded bg-red-950 border border-red-900 text-red-200 text-xs">
                    {deleteError}
                  </div>
                )}

                <form onSubmit={handleDeleteAccount} className="space-y-3">
                  <input
                    type="password"
                    required
                    value={deletePassword}
                    onChange={(e) => setDeletePassword(e.target.value)}
                    placeholder="Enter password"
                    className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-red-500"
                  />
                  <div className="flex items-center justify-end gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => setShowDeleteModal(false)}
                      className="px-3 py-1.5 rounded-md text-xs text-slate-400 hover:text-white"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={deleteLoading}
                      className="px-4 py-1.5 rounded-md bg-red-600 hover:bg-red-700 text-white text-xs font-medium"
                    >
                      {deleteLoading ? 'Deleting...' : 'Permanently Delete'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
