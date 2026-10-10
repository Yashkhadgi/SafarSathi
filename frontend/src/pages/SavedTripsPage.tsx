import React, { useEffect, useState } from 'react';
import { 
  Bookmark, 
  Trash2, 
  Eye, 
  Calendar, 
  MapPin, 
  FileText, 
  Clock, 
  Loader2 
} from 'lucide-react';
import { apiGet, apiDelete } from '../api/client';

interface SavedTrip {
  id: string;
  title: string;
  destination: string;
  duration_days: number;
  current_version: number;
  created_at: string;
  updated_at: string;
  data_json: {
    days?: Array<{ day: number; slots: Array<{ place: string; duration_min?: number }> }>;
    warnings?: string[];
  };
}

export const SavedTripsPage: React.FC = () => {
  const [trips, setTrips] = useState<SavedTrip[]>([]);
  const [selectedTrip, setSelectedTrip] = useState<SavedTrip | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchTrips = async () => {
    try {
      const data = await apiGet<SavedTrip[]>('/trips');
      setTrips(Array.isArray(data) ? data : []);
    } catch {
      // Ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrips();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await apiDelete(`/trips/${id}`);
      setTrips((prev) => prev.filter((t) => t.id !== id));
      if (selectedTrip?.id === id) setSelectedTrip(null);
    } catch {
      // Ignore
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Saved Trips & Version Archives</h1>
        <p className="mt-1 text-xs text-slate-400">
          All your saved travel itineraries with full immutable version history.
        </p>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-500 text-xs">
          <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-brand-400" />
          <span>Loading saved itineraries...</span>
        </div>
      ) : trips.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Trip Cards List */}
          <div className="space-y-3 md:col-span-1">
            {trips.map((trip) => (
              <div
                key={trip.id}
                onClick={() => setSelectedTrip(trip)}
                className={`p-4 rounded-lg border text-xs cursor-pointer transition-colors ${
                  selectedTrip?.id === trip.id
                    ? 'bg-slate-900 border-brand-500 text-white shadow-md'
                    : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-sm text-white">{trip.title}</h3>
                    <div className="flex items-center gap-2 mt-1 text-slate-400 text-[11px]">
                      <span>{trip.destination}</span>
                      <span>•</span>
                      <span>{trip.duration_days} days</span>
                    </div>
                  </div>
                  <span className="px-1.5 py-0.5 rounded bg-slate-950 text-brand-300 text-[10px] font-mono">
                    v{trip.current_version}
                  </span>
                </div>

                <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                  <span>Updated: {new Date(trip.updated_at).toLocaleDateString()}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(trip.id);
                    }}
                    className="p-1 hover:text-red-400 text-slate-500 transition-colors"
                    title="Delete trip"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Detailed View */}
          <div className="md:col-span-2">
            {selectedTrip ? (
              <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <h2 className="text-base font-bold text-white">{selectedTrip.title}</h2>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Destination: {selectedTrip.destination} • {selectedTrip.duration_days} Days
                    </p>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-brand-950 border border-brand-800 text-brand-300 text-xs font-mono">
                    Version {selectedTrip.current_version}
                  </span>
                </div>

                {/* Day-by-Day Slots */}
                <div className="space-y-4">
                  {selectedTrip.data_json?.days?.map((day) => (
                    <div key={day.day} className="p-4 rounded-md bg-slate-950 border border-slate-800 space-y-2">
                      <span className="font-semibold text-white text-xs block">Day {day.day}</span>
                      <div className="space-y-1.5 pl-2">
                        {day.slots?.map((slot, sIdx) => (
                          <div key={sIdx} className="text-xs text-slate-300 flex items-center justify-between">
                            <span>• {slot.place}</span>
                            {slot.duration_min && (
                              <span className="text-slate-500 text-[11px]">{slot.duration_min} min</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="p-12 rounded-lg bg-slate-900 border border-slate-800 text-center text-xs text-slate-500">
                Select an itinerary from the list to preview details and version history.
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="p-12 rounded-lg bg-slate-900 border border-slate-800 text-center space-y-3">
          <div className="w-12 h-12 rounded-md bg-slate-950 border border-slate-800 text-slate-500 mx-auto flex items-center justify-center">
            <Bookmark className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-slate-300">No saved itineraries found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Build a plan in the Itinerary Planner and it will appear here automatically.
          </p>
        </div>
      )}
    </div>
  );
};
