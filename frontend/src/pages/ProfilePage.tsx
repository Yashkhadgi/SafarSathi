import React, { useEffect, useState } from 'react';
import { 
  User, 
  Heart, 
  MapPin, 
  Utensils, 
  Accessibility, 
  ShieldCheck, 
  Save, 
  CheckCircle2, 
  AlertCircle, 
  Loader2 
} from 'lucide-react';
import { apiGet, apiPut, ApiError } from '../api/client';

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

export const ProfilePage: React.FC = () => {
  const [homeCity, setHomeCity] = useState('');
  const [diet, setDiet] = useState('all');
  const [allergiesInput, setAllergiesInput] = useState('');
  const [travelStyle, setTravelStyle] = useState('normal');
  const [budgetRange, setBudgetRange] = useState('mid');
  const [mobilityNotes, setMobilityNotes] = useState('');
  const [consentLocation, setConsentLocation] = useState(false);
  const [consentContacts, setConsentContacts] = useState(false);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
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
        // Soft error
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaving(true);
    setSavedSuccess(false);

    const allergies = allergiesInput
      .split(',')
      .map((a) => a.trim())
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
      setSavedSuccess(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.data.detail || 'Could not update profile');
      } else {
        setError('Failed to update profile');
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Traveler Profile & Dietary Preferences</h1>
        <p className="mt-1 text-xs text-slate-400">
          Preferences are automatically injected into AI itineraries and food recommendations.
        </p>
      </div>

      {savedSuccess && (
        <div className="p-3.5 rounded-md bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>Profile preferences saved successfully.</span>
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-md bg-red-950/60 border border-red-900 text-red-200 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="prof-home">
              Home City
            </label>
            <input
              id="prof-home"
              type="text"
              value={homeCity}
              onChange={(e) => setHomeCity(e.target.value)}
              placeholder="e.g. Mumbai, Bengaluru"
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="prof-diet">
              Dietary Preference
            </label>
            <select
              id="prof-diet"
              value={diet}
              onChange={(e) => setDiet(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            >
              <option value="all">All Foods (Vegetarian & Non-Veg)</option>
              <option value="veg">Pure Vegetarian (No meat/eggs)</option>
              <option value="vegan">Vegan (Plant-based only)</option>
              <option value="jain">Jain (No root vegetables, onion, garlic)</option>
              <option value="halal">Halal certified</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="prof-allergies">
              Food Allergies (Comma separated)
            </label>
            <input
              id="prof-allergies"
              type="text"
              value={allergiesInput}
              onChange={(e) => setAllergiesInput(e.target.value)}
              placeholder="e.g. Peanuts, Shellfish, Dairy, Gluten"
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="prof-pace">
              Preferred Travel Pace
            </label>
            <select
              id="prof-pace"
              value={travelStyle}
              onChange={(e) => setTravelStyle(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            >
              <option value="relaxed">Relaxed (Slow paced, 2 stops/day)</option>
              <option value="normal">Normal (Balanced, 3 stops/day)</option>
              <option value="packed">Packed (Fast exploration, 4 stops/day)</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="prof-mobility">
            Mobility & Physical Access Notes
          </label>
          <textarea
            id="prof-mobility"
            rows={2}
            value={mobilityNotes}
            onChange={(e) => setMobilityNotes(e.target.value)}
            placeholder="e.g. Wheelchair access required, avoid steep steps, traveling with toddler"
            className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
          />
        </div>

        {/* Consents */}
        <div className="pt-4 border-t border-slate-800 space-y-3">
          <h3 className="text-xs font-semibold text-white">Privacy and Device Consents</h3>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={consentLocation}
              onChange={(e) => setConsentLocation(e.target.checked)}
              className="w-4 h-4 rounded border-slate-800 bg-slate-950 text-brand-600 focus:ring-0"
            />
            <span className="text-xs text-slate-300">
              Allow location lookup for Near Me recommendations and emergency GPS dispatch.
            </span>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={consentContacts}
              onChange={(e) => setConsentContacts(e.target.checked)}
              className="w-4 h-4 rounded border-slate-800 bg-slate-950 text-brand-600 focus:ring-0"
            />
            <span className="text-xs text-slate-300">
              Allow storing encrypted trusted contact numbers for one-tap emergency SMS/WhatsApp alerts.
            </span>
          </label>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="py-2.5 px-5 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white text-xs font-medium flex items-center gap-2 cursor-pointer transition-colors"
        >
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Saving Preferences...</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              <span>Save Profile</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};
