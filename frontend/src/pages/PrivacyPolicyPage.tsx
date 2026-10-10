import React from 'react';
import { ShieldCheck, Lock, Trash2, EyeOff, Server } from 'lucide-react';

export const PrivacyPolicyPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <div className="mb-10 pb-6 border-b border-slate-800">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-slate-900 border border-slate-800 text-xs text-brand-400 mb-3">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Last Updated: October 2024</span>
        </div>
        <h1 className="text-3xl font-bold text-white">Privacy Policy</h1>
        <p className="mt-2 text-sm text-slate-400">
          How SafarSathi handles your account data, chat logs, itineraries, and trusted emergency contacts.
        </p>
      </div>

      <div className="space-y-8 text-sm text-slate-300 leading-relaxed">
        {/* Section 1 */}
        <section className="p-6 rounded-lg bg-slate-900 border border-slate-800">
          <div className="flex items-center gap-2.5 text-base font-semibold text-white mb-3">
            <Lock className="w-5 h-5 text-brand-400" />
            <h2>1. Data Collection and Encryption</h2>
          </div>
          <p className="text-slate-400 text-xs leading-relaxed mb-3">
            We collect only the minimum information necessary to provide travel guidance and safety features:
          </p>
          <ul className="list-disc pl-5 space-y-1.5 text-xs text-slate-400">
            <li><strong className="text-slate-200">Account Credentials:</strong> Email addresses and passwords. Passwords are never stored in plaintext; they are hashed using Argon2id with salted PBKDF2 fallback.</li>
            <li><strong className="text-slate-200">Trusted Contacts:</strong> Phone numbers entered for emergency alerts are encrypted at rest using AES-128-CBC authenticated encryption (Fernet) before writing to the database.</li>
            <li><strong className="text-slate-200">Travel Preferences:</strong> Diet, allergies, and mobility requirements you choose to save in your profile.</li>
            <li><strong className="text-slate-200">Trip Itineraries and Chats:</strong> Saved plans and message history associated with your user account.</li>
          </ul>
        </section>

        {/* Section 2 */}
        <section className="p-6 rounded-lg bg-slate-900 border border-slate-800">
          <div className="flex items-center gap-2.5 text-base font-semibold text-white mb-3">
            <EyeOff className="w-5 h-5 text-brand-400" />
            <h2>2. No Third-Party Selling or Advertising</h2>
          </div>
          <p className="text-slate-400 text-xs leading-relaxed">
            SafarSathi does not sell, rent, or monetize your personal travel data. We do not integrate advertising trackers, behavioral profiling pixels, or sponsored merchant listings. All hotel, transport, and monument recommendations are strictly informational without affiliate commissions.
          </p>
        </section>

        {/* Section 3 */}
        <section className="p-6 rounded-lg bg-slate-900 border border-slate-800">
          <div className="flex items-center gap-2.5 text-base font-semibold text-white mb-3">
            <Trash2 className="w-5 h-5 text-brand-400" />
            <h2>3. Complete Account Deletion (Right to be Forgotten)</h2>
          </div>
          <p className="text-slate-400 text-xs leading-relaxed mb-3">
            When you request account deletion from your account settings:
          </p>
          <ul className="list-disc pl-5 space-y-1.5 text-xs text-slate-400">
            <li>All associated conversations and messages are deleted immediately.</li>
            <li>All saved trips, versions, and feedback records are purged via database cascade.</li>
            <li>All encrypted trusted contacts are permanently removed.</li>
            <li>No orphaned user records or shadow profiles remain in our primary database.</li>
          </ul>
        </section>

        {/* Section 4 */}
        <section className="p-6 rounded-lg bg-slate-900 border border-slate-800">
          <div className="flex items-center gap-2.5 text-base font-semibold text-white mb-3">
            <Server className="w-5 h-5 text-brand-400" />
            <h2>4. Security and Session Management</h2>
          </div>
          <p className="text-slate-400 text-xs leading-relaxed">
            Authentication sessions use secure, HTTP-only, SameSite cookies with rotating 30-day refresh tokens. Brute-force protection limits failed login attempts to 5 before triggering a temporary lockout. You can view all active sessions and revoke devices at any time from your account settings.
          </p>
        </section>
      </div>
    </div>
  );
};
