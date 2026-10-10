import React from 'react';
import { 
  MapPin, 
  Star, 
  Clock, 
  ExternalLink, 
  Utensils, 
  Landmark, 
  Building2 
} from 'lucide-react';

export interface NearbyPlaceItem {
  name: string;
  address?: string;
  distance_km?: number;
  distance_meters?: number;
  rating?: number;
  open_now?: boolean | string;
  latitude?: number;
  longitude?: number;
}

export interface NearMeData {
  category?: string;
  places: NearbyPlaceItem[];
  city_or_coords?: string;
  last_verified?: string;
}

interface NearMeCardProps {
  data: NearMeData;
  onSendMessage?: (message: string) => void;
}

export const NearMeCard: React.FC<NearMeCardProps> = ({ data, onSendMessage }) => {
  const formatDistance = (p: NearbyPlaceItem) => {
    if (p.distance_km !== undefined) {
      return `${p.distance_km} km away`;
    }
    if (p.distance_meters !== undefined) {
      return p.distance_meters > 1000 
        ? `${(p.distance_meters / 1000).toFixed(1)} km away` 
        : `${p.distance_meters}m away`;
    }
    return 'Nearby';
  };

  return (
    <div className="w-full my-3 rounded-lg border border-slate-700 bg-slate-900 text-slate-100 shadow-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-slate-800/80 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <MapPin className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100 capitalize">
              Nearby {data.category || 'Places & Amenities'}
            </h4>
            <p className="text-[11px] text-slate-400">Verified radius lookup</p>
          </div>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
          {data.places?.length || 0} Found
        </span>
      </div>

      {/* Places List */}
      <div className="p-4 space-y-2.5">
        {data.places?.map((place, idx) => (
          <div 
            key={idx}
            className="p-3 rounded-md bg-slate-800/50 border border-slate-700/70 hover:border-slate-600 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-2"
          >
            <div className="space-y-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-200 truncate">{place.name}</span>
                {place.rating !== undefined && place.rating > 0 && (
                  <span className="flex items-center gap-0.5 text-[10px] px-1.5 py-0.2 rounded bg-amber-950/60 border border-amber-800/80 text-amber-300">
                    <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                    {place.rating}
                  </span>
                )}
              </div>
              {place.address && (
                <p className="text-[11px] text-slate-400 truncate">{place.address}</p>
              )}
            </div>

            <div className="flex items-center gap-3 shrink-0 text-xs">
              <span className="text-[11px] font-mono text-slate-300 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                {formatDistance(place)}
              </span>
              {place.open_now !== undefined && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                  place.open_now === true || place.open_now === 'true'
                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    : 'bg-slate-800 text-slate-400'
                }`}>
                  {place.open_now === true || place.open_now === 'true' ? 'Open now' : 'Verify hours'}
                </span>
              )}
            </div>
          </div>
        ))}

        {(!data.places || data.places.length === 0) && (
          <div className="py-6 text-center text-xs text-slate-400">
            No nearby places found for this category.
          </div>
        )}

        {/* Quick Follow-up Actions */}
        {onSendMessage && data.places && data.places.length > 0 && (
          <div className="pt-2 flex flex-wrap gap-2">
            <button
              onClick={() => onSendMessage(`Tell me more about visiting ${data.places[0]?.name}`)}
              className="px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
            >
              Info on {data.places[0]?.name.slice(0, 18)}...
            </button>
            <button
              onClick={() => onSendMessage(`Show pure vegetarian restaurants near me`)}
              className="px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
            >
              Find veg food nearby
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
