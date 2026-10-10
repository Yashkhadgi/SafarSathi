"""B15: Checklist tool — smart packing list and pre-trip timeline checklist.

All functions are pure Python, defensive, and return dicts with structured data.
"""

from datetime import date, datetime, timedelta


_BASE_PACKING = {
    "documents": [
        {"item": "Govt Photo ID (Aadhaar / Voter ID / Passport / Driving Licence)", "essential": True},
        {"item": "Emergency contact numbers written on paper", "essential": True},
        {"item": "Hotel / Train / Flight booking confirmations (digital + 1 paper copy)", "essential": True},
        {"item": "Medical insurance card / policy details", "essential": False},
    ],
    "electronics": [
        {"item": "Phone and phone charger", "essential": True},
        {"item": "Power bank (10,000+ mAh)", "essential": True},
        {"item": "Earphones / Headphones", "essential": False},
        {"item": "Universal adapter / multi-plug (for older hotel sockets)", "essential": False},
    ],
    "toiletries": [
        {"item": "Toothbrush and toothpaste", "essential": True},
        {"item": "Soap / Body wash (travel size)", "essential": True},
        {"item": "Shampoo and conditioner", "essential": False},
        {"item": "Hand sanitizer and wet wipes", "essential": True},
        {"item": "Sunscreen (SPF 30+)", "essential": True},
        {"item": "Lip balm / moisturiser", "essential": False},
    ],
    "health_and_meds": [
        {"item": "Personal prescription medications (with doctor prescription)", "essential": True},
        {"item": "Basic first-aid: Band-aids, antiseptic cream, ORS packets", "essential": True},
        {"item": "Motion sickness tablets (consult doctor)", "essential": False},
        {"item": "Pain relief / fever relief (consult doctor)", "essential": False},
        {"item": "Mosquito repellent cream / spray", "essential": True},
    ],
    "clothing_basics": [
        {"item": "Comfortable walking shoes / sneakers", "essential": True},
        {"item": "Flip-flops / sandals", "essential": True},
        {"item": "Undergarments (1 per day + 2 extra)", "essential": True},
        {"item": "Socks (breathable cotton)", "essential": True},
        {"item": "Nightwear / sleepwear", "essential": True},
        {"item": "Modest clothing for temples (covering shoulders & knees)", "essential": True},
    ],
}


def smart_packing_list(
    destination: str,
    days: int = 3,
    activities: list = None,
    season: str = "",
    traveler_type: str = "",
) -> dict:
    """Generate a categorized packing checklist tailored to destination, climate, and duration.

    Args:
        destination: Destination name (e.g. 'Ladakh', 'Goa', 'Udaipur', 'Manali').
        days: Trip duration in days.
        activities: List of activities (e.g. ['beach', 'trek', 'temple', 'wildlife']).
        season: Climate or season (e.g. 'winter', 'monsoon', 'summer').
        traveler_type: 'kids', 'senior', 'women_solo', 'backpacker', etc.

    Returns:
        dict with categorized checklist items with completion checkboxes.
    """
    try:
        dest_lower = str(destination or "").strip().lower()
        days = max(1, int(days or 3))
        activities = [str(a).strip().lower() for a in (activities or [])]
        season_lower = str(season or "").strip().lower()
        traveler_lower = str(traveler_type or "").strip().lower()

        # Build categories
        import copy
        categories = copy.deepcopy(_BASE_PACKING)

        # Clothes count calculation
        tshirt_count = min(days + 1, 8)
        bottom_count = max(2, min(days // 2 + 1, 5))
        categories["clothing_basics"].insert(
            0, {"item": f"T-shirts / Tops ({tshirt_count} pcs, breathable cotton)", "essential": True}
        )
        categories["clothing_basics"].insert(
            1, {"item": f"Pants / Jeans / Trousers ({bottom_count} pcs)", "essential": True}
        )

        # Destination / Climate specific additions
        is_high_altitude = any(k in dest_lower for k in ["leh", "ladakh", "spiti", "zanskar", "kedarnath", "badrinath"])
        is_cold_hill = is_high_altitude or any(k in dest_lower for k in ["manali", "shimla", "darjeeling", "gangtok", "gulmarg", "munnar", "ooty"])
        is_beach = any(k in dest_lower for k in ["goa", "gokarna", "puri", "kochi", "andaman", "pondicherry", "varkala"]) or "beach" in activities
        is_monsoon = "monsoon" in season_lower or "rain" in season_lower
        is_summer = "summer" in season_lower or "hot" in season_lower

        dest_specific = []

        if is_high_altitude:
            dest_specific.extend([
                {"item": "Heavy thermal innerwear (top and bottom)", "essential": True},
                {"item": "Fleece jacket and windproof/waterproof outer jacket", "essential": True},
                {"item": "Warm woolen cap (covering ears) and neck gaiter", "essential": True},
                {"item": "Thermal gloves (water-resistant)", "essential": True},
                {"item": "UV protection sunglasses (polarized essential at high altitude)", "essential": True},
                {"item": "High-SPF sunscreen (SPF 50+) and heavy lip balm", "essential": True},
                {"item": "Thermos flask / insulated water bottle (for warm water)", "essential": True},
                {"item": "Altitude sickness medication (only on doctor's prescription)", "essential": True},
            ])
        elif is_cold_hill:
            dest_specific.extend([
                {"item": "Light to medium jacket / sweater", "essential": True},
                {"item": "Woolen socks (2-3 pairs)", "essential": True},
                {"item": "Shawl / light scarf", "essential": False},
                {"item": "Comfortable hiking/walking shoes with grip", "essential": True},
            ])

        if is_beach:
            dest_specific.extend([
                {"item": "Swimwear / Quick-dry beach clothes", "essential": True},
                {"item": "Beach towel / sarong", "essential": True},
                {"item": "Waterproof phone pouch", "essential": True},
                {"item": "Sun hat / cap and UV sunglasses", "essential": True},
                {"item": "Aloe vera gel / after-sun lotion", "essential": False},
                {"item": "Dry bag for wet clothes", "essential": False},
            ])

        if is_monsoon:
            dest_specific.extend([
                {"item": "Sturdy umbrella and lightweight raincoat / poncho", "essential": True},
                {"item": "Waterproof backpack cover", "essential": True},
                {"item": "Silica gel packets (for electronics in bag)", "essential": False},
                {"item": "Quick-dry synthetic clothing (avoid heavy denim)", "essential": True},
                {"item": "Extra plastic ziplock bags for documents and electronics", "essential": True},
                {"item": "Water-resistant footwear / sandals with good traction", "essential": True},
            ])

        if is_summer:
            dest_specific.extend([
                {"item": "Wide-brim hat / cotton cap", "essential": True},
                {"item": "Cotton scarf / gamcha (to cover face/neck from sun/dust)", "essential": True},
                {"item": "Reusable water bottle / hydration pack", "essential": True},
                {"item": "Cooling face wipes and glucose/electrolyte powder", "essential": True},
            ])

        # Activity specific
        activity_items = []
        if "trek" in activities or "trekking" in activities or "adventure" in activities:
            activity_items.extend([
                {"item": "Trekking shoes with ankle support", "essential": True},
                {"item": "Trekking pole / stick", "essential": False},
                {"item": "Headlamp / small torch with extra batteries", "essential": True},
                {"item": "Quick-dry athletic t-shirts and cargo pants", "essential": True},
                {"item": "Compact quick-dry microfiber towel", "essential": True},
            ])

        if "temple" in activities or "spiritual" in activities:
            activity_items.extend([
                {"item": "Traditional / modest attire (dhoti/kurta for men, saree/salwar for women where required)", "essential": True},
                {"item": "Easy slip-on footwear (frequent shoe removal at temples)", "essential": True},
                {"item": "Socks for walking on hot temple stone floors", "essential": True},
                {"item": "Small sling bag / tote for footwear tokens and flowers", "essential": False},
            ])

        # Traveler type additions
        if traveler_lower == "kids":
            categories["health_and_meds"].extend([
                {"item": "Child-specific medications & thermometer", "essential": True},
                {"item": "Snacks and sealed juice boxes for travel delays", "essential": True},
                {"item": "Change of clothes in daypack", "essential": True},
                {"item": "Small toys / colouring book for journeys", "essential": False},
            ])
        elif traveler_lower == "senior":
            categories["health_and_meds"].extend([
                {"item": "Full supply of prescription medications + 3 days buffer", "essential": True},
                {"item": "Doctor's prescription and medical summary sheet", "essential": True},
                {"item": "Folding walking stick if needed", "essential": False},
                {"item": "Comfortable orthopaedic footwear", "essential": True},
            ])

        categories["destination_and_weather_specific"] = dest_specific
        if activity_items:
            categories["activity_specific"] = activity_items

        total_items = sum(len(items) for items in categories.values())
        essential_items = sum(sum(1 for i in items if i.get("essential")) for items in categories.values())

        res = {
            "destination": destination,
            "days": days,
            "season": season or "moderate",

            "traveler_type": traveler_type or "general",
            "total_items": total_items,
            "essential_count": essential_items,
            "categories": categories,
            "tip": "Roll clothes instead of folding to save 30% luggage space and reduce wrinkles.",
        }
        res["ui"] = {
            "type": "checklist",
            "version": "1.0",
            "data": {
                "title": f"Smart Packing List — {destination} ({days} Days)",
                "destination": destination,
                "season": season or "all-season",
                "categories": [
                    {
                        "name": cat_key.replace("_", " ").title(),
                        "items": [
                            {
                                "id": f"item_{cat_key}_{idx}",
                                "label": it.get("item", ""),
                                "essential": it.get("essential", False),
                                "checked": False,
                            }
                            for idx, it in enumerate(cat_items)
                        ]
                    }
                    for cat_key, cat_items in categories.items()
                ],
                "tip": res["tip"],
            }
        }
        return res
    except Exception as exc:
        return {"error": f"Smart packing list generation failed: {exc}"}


def pre_trip_checklist(trip_start_date: str = "", destination: str = "", is_international: bool = False) -> dict:
    """Generate a timeline-based pre-trip preparation checklist (T-30, T-7, T-1, Departure Day).

    Args:
        trip_start_date: Optional ISO date 'YYYY-MM-DD'.
        destination: Trip destination name.
        is_international: True if traveling abroad or foreign tourist visiting India.

    Returns:
        dict with dated timeline items and reminders. No booking links.
    """
    try:
        start_d = None
        if trip_start_date:
            try:
                start_d = date.fromisoformat(trip_start_date.strip())
            except Exception:
                start_d = None

        dest = str(destination or "your trip").strip()

        # T-30 Days
        t30 = [
            {"task": "Verify passport validity (min 6 months validity required)", "category": "documents", "applicable": is_international},
            {"task": "Apply for e-Visa / entry permits (e.g. Protected Area Permit for Ladakh/Sikkim if needed)", "category": "documents", "applicable": True},
            {"task": "Verify flight/train ticket dates, names matching ID proofs (IRCTC / Airline)", "category": "transport", "applicable": True},
            {"task": "Book accommodation and obtain confirmation vouchers", "category": "stay", "applicable": True},
            {"task": "Check destination weather trends and seasonal closure warnings", "category": "research", "applicable": True},
            {"task": "Visit doctor for routine checkup / required vaccinations if needed", "category": "health", "applicable": True},
        ]

        # T-7 Days
        t7 = [
            {"task": "Download offline Google Maps / OSM map area for " + dest, "category": "tech", "applicable": True},
            {"task": "Photocopy IDs, tickets, and hotel vouchers; store digital scans in cloud", "category": "documents", "applicable": True},
            {"task": "Inform bank/credit card company of domestic/international travel to prevent card freeze", "category": "finance", "applicable": True},
            {"task": "Refill prescription medications for the entire trip duration + 3 days buffer", "category": "health", "applicable": True},
            {"task": "Begin packing non-daily items using the Smart Packing List", "category": "packing", "applicable": True},
            {"task": "Arrange home care: plant watering, newspaper pause, pet care", "category": "home", "applicable": True},
        ]

        # T-1 Day
        t1 = [
            {"task": "Web check-in for flights (24-48 hrs prior) or check PNR status on IRCTC", "category": "transport", "applicable": True},
            {"task": "Charge all electronics: phone, camera, power bank, headphones", "category": "tech", "applicable": True},
            {"task": "Withdraw emergency cash (small denominations: INR 100, 200, 500 notes)", "category": "finance", "applicable": True},
            {"task": "Pack toiletries, daily meds, chargers into main luggage or daypack", "category": "packing", "applicable": True},
            {"task": "Set alarm clock for departure morning with 30 min buffer", "category": "schedule", "applicable": True},
            {"task": "Share trip itinerary and emergency contacts with family/friend", "category": "safety", "applicable": True},
        ]

        # Departure Day
        t0 = [
            {"task": "Check wallet: Govt ID, credit/debit cards, cash", "category": "essentials", "applicable": True},
            {"task": "Check phone: fully charged, ticket PDF/SMS accessible offline", "category": "essentials", "applicable": True},
            {"task": "Lock all home windows, turn off LPG gas cylinder valve, unplug appliances", "category": "home", "applicable": True},
            {"task": "Reach airport (2 hrs domestic / 3 hrs international) or railway station (45 min prior)", "category": "transport", "applicable": True},
        ]

        def _format_stage(items, days_before, label):
            d_str = ""
            if start_d:
                target_date = start_d - timedelta(days=days_before)
                d_str = f" ({target_date.strftime('%d %b %Y')})"
            return {
                "timeline_label": label + d_str,
                "days_before_trip": days_before,
                "tasks": [i for i in items if i.get("applicable", True)],
            }

        stages = [
            _format_stage(t30, 30, "T-30 Days: Booking Verification & Documents"),
            _format_stage(t7, 7, "T-7 Days: Offline Maps, Packing & Finances"),
            _format_stage(t1, 1, "T-1 Day: Web Check-in, Charging & Cash"),
            _format_stage(t0, 0, "Departure Day: Final Quick-Check"),
        ]

        res = {
            "destination": dest,
            "start_date": trip_start_date or "Not specified",
            "is_international": is_international,
            "stages": stages,
            "total_tasks": sum(len(s["tasks"]) for s in stages),
            "safety_note": "Information only — verify official airline, IRCTC, and immigration rules directly.",
        }
        res["ui"] = {
            "type": "checklist",
            "version": "1.0",
            "data": {
                "title": f"Pre-Trip Timeline Checklist — {dest}",
                "destination": dest,
                "season": trip_start_date or "pre-trip",
                "categories": [
                    {
                        "name": stage["timeline_label"],
                        "items": [
                            {
                                "id": f"task_{s_idx}_{t_idx}",
                                "label": t["task"],
                                "essential": t.get("category") in ("documents", "essentials"),
                                "checked": False,
                            }
                            for t_idx, t in enumerate(stage["tasks"])
                        ]
                    }
                    for s_idx, stage in enumerate(stages)
                ],
                "tip": res["safety_note"],
            }
        }
        return res
    except Exception as exc:
        return {"error": f"Pre-trip checklist generation failed: {exc}"}

