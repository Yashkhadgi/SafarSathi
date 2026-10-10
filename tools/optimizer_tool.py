"""B14: Multi-city optimizer — nearest-neighbour TSP and day allocation.

Uses haversine distance (pure Python stdlib). No external Maps API for ordering.
"""

import math


# Known city coordinates (lat, lon)
_CITY_COORDS = {
    "agra": (27.1767, 78.0081),
    "ahmedabad": (23.0225, 72.5714),
    "amritsar": (31.6340, 74.8723),
    "aurangabad": (19.8762, 75.3433),
    "badrinath": (30.7433, 79.4938),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "bhopal": (23.2599, 77.4126),
    "bhubaneswar": (20.2961, 85.8245),
    "chandigarh": (30.7333, 76.7794),
    "chennai": (13.0827, 80.2707),
    "cochin": (9.9312, 76.2673),
    "coimbatore": (11.0168, 76.9558),
    "darjeeling": (27.0360, 88.2627),
    "delhi": (28.6139, 77.2090),
    "goa": (15.2993, 74.1240),
    "gurugram": (28.4595, 77.0266),
    "guwahati": (26.1445, 91.7362),
    "hampi": (15.3350, 76.4600),
    "haridwar": (29.9457, 78.1642),
    "hyderabad": (17.3850, 78.4867),
    "indore": (22.7196, 75.8577),
    "jaipur": (26.9124, 75.7873),
    "jaisalmer": (26.9157, 70.9083),
    "jodhpur": (26.2389, 73.0243),
    "kedarnath": (30.7352, 79.0669),
    "kochi": (9.9312, 76.2673),
    "kolkata": (22.5726, 88.3639),
    "leh": (34.1526, 77.5771),
    "lucknow": (26.8467, 80.9462),
    "madurai": (9.9252, 78.1198),
    "manali": (32.2432, 77.1892),
    "munnar": (10.0889, 77.0595),
    "mumbai": (19.0760, 72.8777),
    "mysore": (12.2958, 76.6394),
    "mysuru": (12.2958, 76.6394),
    "nagpur": (21.1458, 79.0882),
    "nashik": (19.9975, 73.7898),
    "new delhi": (28.6139, 77.2090),
    "noida": (28.5355, 77.3910),
    "ooty": (11.4102, 76.6950),
    "panaji": (15.4989, 73.8278),
    "patna": (25.5941, 85.1376),
    "pondicherry": (11.9416, 79.8083),
    "puducherry": (11.9416, 79.8083),
    "pune": (18.5204, 73.8567),
    "puri": (19.8135, 85.8312),
    "pushkar": (26.4897, 74.5511),
    "rishikesh": (30.0869, 78.2676),
    "shimla": (31.1048, 77.1734),
    "shirdi": (19.7656, 74.4773),
    "srinagar": (34.0836, 74.7973),
    "tamil nadu": (11.1271, 78.6569),
    "tirupati": (13.6288, 79.4192),
    "trivandrum": (8.5241, 76.9366),
    "thiruvananthapuram": (8.5241, 76.9366),
    "udaipur": (24.5854, 73.7125),
    "varanasi": (25.3176, 82.9739),
    "vijayawada": (16.5062, 80.6480),
    "visakhapatnam": (17.6868, 83.2185),
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km (Python stdlib only)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _resolve_coords(city: str):
    """Return (lat, lon) for a city or None if unknown."""
    return _CITY_COORDS.get(city.strip().casefold())


def _nearest_neighbour_tsp(cities_coords: list, start_idx: int = 0):
    """Run nearest-neighbour TSP heuristic.

    Args:
        cities_coords: list of (city_name, lat, lon)
        start_idx: index to start from (corresponds to origin city)

    Returns:
        (ordered list of city dicts, total km float)
    """
    remaining = list(range(len(cities_coords)))
    current = start_idx
    remaining.remove(current)
    order = [current]
    total_km = 0.0

    while remaining:
        _, lat1, lon1 = cities_coords[current]
        best_idx = None
        best_dist = float("inf")
        for idx in remaining:
            _, lat2, lon2 = cities_coords[idx]
            d = _haversine_km(lat1, lon1, lat2, lon2)
            if d < best_dist:
                best_dist = d
                best_idx = idx
        order.append(best_idx)
        total_km += best_dist
        current = best_idx
        remaining.remove(best_idx)

    return order, total_km


def optimize_route(cities: list, origin: str, total_days: int) -> dict:
    """Optimize a multi-city route using nearest-neighbour TSP and proportional day allocation.

    Uses haversine distance (pure Python). No Maps API required.

    Args:
        cities: List of city names to visit.
        origin: Departure city (start of trip).
        total_days: Total trip duration in days.

    Returns:
        dict with optimized order, inter-city distances, day allocations, and total km.
    """
    try:
        cities = [str(c).strip() for c in (cities or []) if str(c).strip()]
        origin = str(origin or "").strip()
        total_days = int(total_days or len(cities) * 2)

        if not cities:
            return {"error": "At least one city is required"}
        if total_days <= 0:
            return {"error": "total_days must be positive"}
        if not origin:
            return {"error": "Origin city is required"}

        # Resolve coords — include origin as first point
        all_cities = [origin] + [c for c in cities if c.casefold() != origin.casefold()]
        all_cities = list(dict.fromkeys(all_cities))  # deduplicate, preserving order attempt

        city_coords_list = []
        unknown = []
        for c in all_cities:
            coords = _resolve_coords(c)
            if coords:
                city_coords_list.append((c, coords[0], coords[1]))
            else:
                unknown.append(c)

        if len(city_coords_list) < 2:
            return {
                "error": f"Not enough known city coordinates to optimize. Unknown cities: {unknown}",
                "known_cities": list(_CITY_COORDS.keys())[:20],
            }

        # Nearest neighbour from origin (index 0)
        order_indices, total_km = _nearest_neighbour_tsp(city_coords_list, start_idx=0)
        ordered_cities = [city_coords_list[i][0] for i in order_indices]

        # Allocate days proportionally based on distance to next city
        # Skip origin in allocation (it's the departure point)
        visit_cities = ordered_cities[1:] if ordered_cities[0].casefold() == origin.casefold() else ordered_cities
        if not visit_cities:
            visit_cities = ordered_cities

        n = len(visit_cities)
        base_days = total_days // n
        extra_days = total_days % n
        day_allocations = []
        for i, city in enumerate(visit_cities):
            alloc = base_days + (1 if i < extra_days else 0)
            day_allocations.append({"city": city, "days_allocated": alloc})

        # Build inter-city legs with distances
        legs = []
        for i in range(len(ordered_cities) - 1):
            c1, lat1, lon1 = city_coords_list[order_indices[i]]
            c2, lat2, lon2 = city_coords_list[order_indices[i + 1]]
            d = round(_haversine_km(lat1, lon1, lat2, lon2))
            legs.append({
                "from": c1,
                "to": c2,
                "distance_km_approx": d,
                "note": "approx haversine straight-line distance — actual road distance will differ",
            })

        warnings = []
        if unknown:
            warnings.append(f"Unknown cities (no coordinates in DB): {unknown}. These were excluded from optimization.")
        if len(city_coords_list) < len(all_cities):
            warnings.append("Route optimized only for cities with known coordinates.")

        return {
            "origin": origin,
            "optimized_order": ordered_cities,
            "day_allocations": day_allocations,
            "inter_city_legs": legs,
            "total_km_approx": round(total_km),
            "total_days": total_days,
            "algorithm": "nearest-neighbour TSP heuristic (haversine distances)",
            "disclaimer": "Distances are approximate straight-line (haversine) values. Actual road distances and travel times will differ significantly, especially in mountainous regions. Verify with Google Maps or IRCTC.",
            "warnings": warnings,
        }
    except Exception as exc:
        return {"error": f"Route optimization failed: {exc}"}
