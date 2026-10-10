import React, { useEffect, useState } from 'react';
import { 
  Users, 
  UserPlus, 
  Trash2, 
  Phone, 
  MessageSquare, 
  Send, 
  ShieldCheck, 
  AlertCircle, 
  Lock, 
  Loader2 
} from 'lucide-react';
import { apiGet, apiPost, apiDelete, ApiError } from '../api/client';

interface Contact {
  id: string;
  name: string;
  phone: string;
  relationship?: string;
  created_at: string;
}

export const ContactsPage: React.FC = () => {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New Contact Form
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [relationship, setRelationship] = useState('Family');
  const [submitting, setSubmitting] = useState(false);

  // GPS state for SOS messages
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);

  const fetchContacts = async () => {
    try {
      const data = await apiGet<Contact[]>('/trusted-contacts');
      setContacts(Array.isArray(data) ? data : []);
    } catch {
      setError('Could not fetch trusted contacts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContacts();
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => setCoords(null)
      );
    }
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      await apiPost('/trusted-contacts', {
        name,
        phone,
        relationship,
      });
      setName('');
      setPhone('');
      await fetchContacts();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.data.detail || 'Could not add trusted contact');
      } else {
        setError('Failed to add contact');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiDelete(`/trusted-contacts/${id}`);
      setContacts((prev) => prev.filter((c) => c.id !== id));
    } catch {
      setError('Failed to delete contact');
    }
  };

  const buildSosMessage = () => {
    const locString = coords
      ? `My current GPS location is: https://maps.google.com/?q=${coords.lat},${coords.lng}`
      : 'I am traveling and need assistance.';
    return encodeURIComponent(`EMERGENCY: I am using SafarSathi emergency mode and need help. ${locString}`);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Trusted Emergency Contacts</h1>
        <p className="mt-1 text-xs text-slate-400">
          Phone numbers are encrypted at rest with AES-128 Fernet encryption. One-tap instant alerts via WhatsApp and SMS.
        </p>
      </div>

      {error && (
        <div className="p-3.5 rounded-md bg-red-950/60 border border-red-900 text-red-200 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Add Contact Card */}
      <div className="p-6 rounded-lg bg-slate-900 border border-slate-800">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <UserPlus className="w-4 h-4 text-brand-400" />
          <span>Add New Trusted Contact</span>
        </h2>

        <form onSubmit={handleAdd} className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="contact-name">
              Contact Name
            </label>
            <input
              id="contact-name"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Ramesh Sharma"
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="contact-phone">
              Phone Number (with Country Code)
            </label>
            <input
              id="contact-phone"
              type="tel"
              required
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+91 9876543210"
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="contact-rel">
              Relationship
            </label>
            <select
              id="contact-rel"
              value={relationship}
              onChange={(e) => setRelationship(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:border-brand-500"
            >
              <option value="Family">Family Member</option>
              <option value="Spouse">Spouse / Partner</option>
              <option value="Friend">Friend</option>
              <option value="Colleague">Colleague / Guide</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2 px-4 rounded-md bg-brand-600 hover:bg-brand-700 disabled:bg-slate-800 text-white font-medium text-xs flex items-center justify-center gap-2 cursor-pointer transition-colors"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Lock className="w-3.5 h-3.5" />
                  <span>Save Encrypted</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Contacts List & 1-Tap Trigger */}
      <div className="space-y-4">
        <h2 className="text-base font-semibold text-white flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Registered Contacts ({contacts.length})</span>
        </h2>

        {loading ? (
          <div className="p-8 text-center text-slate-500 text-xs">
            <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-brand-400" />
            <span>Loading contacts...</span>
          </div>
        ) : contacts.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {contacts.map((contact) => {
              const cleanPhone = contact.phone.replace(/[^0-9]/g, '');
              const waUrl = `https://wa.me/${cleanPhone}?text=${buildSosMessage()}`;
              const smsUrl = `sms:${contact.phone}?body=${buildSosMessage()}`;

              return (
                <div
                  key={contact.id}
                  className="p-5 rounded-lg bg-slate-900 border border-slate-800 flex flex-col justify-between space-y-4"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white text-sm">{contact.name}</span>
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px]">
                          {contact.relationship || 'Contact'}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 font-mono mt-1">{contact.phone}</p>
                    </div>

                    <button
                      onClick={() => handleDelete(contact.id)}
                      className="p-1.5 rounded-md hover:bg-red-950/60 text-slate-500 hover:text-red-400 transition-colors"
                      title="Delete contact"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  {/* 1-Tap Action Buttons */}
                  <div className="pt-2 border-t border-slate-800/80 flex items-center gap-2">
                    <a
                      href={waUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 py-1.5 px-3 rounded-md bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-800/80 text-emerald-200 text-xs font-medium flex items-center justify-center gap-1.5 transition-colors"
                    >
                      <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
                      <span>WhatsApp SOS</span>
                    </a>

                    <a
                      href={smsUrl}
                      className="flex-1 py-1.5 px-3 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center justify-center gap-1.5 transition-colors"
                    >
                      <Phone className="w-3.5 h-3.5 text-slate-400" />
                      <span>SMS Alert</span>
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-12 rounded-lg bg-slate-900 border border-slate-800 text-center space-y-3">
            <div className="w-12 h-12 rounded-md bg-slate-950 border border-slate-800 text-slate-500 mx-auto flex items-center justify-center">
              <Users className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-semibold text-slate-300">No trusted contacts added</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Add family or friends who can be alerted instantly with your location coordinates during an emergency.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
