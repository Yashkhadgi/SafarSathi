"""Smoke test for P1 Batch B16: Itinerary Export (Text/WhatsApp, iCalendar .ics, PDF)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.export_tool import (
    export_itinerary,
    export_itinerary_text,
    export_itinerary_ics,
    export_itinerary_pdf,
)
from tools.registry import execute_tool

mock_trip = {
    "trip_id": "test-trip-123",
    "destination": "Udaipur",
    "travelers": 2,
    "pace": "relaxed",
    "start_date": "2026-11-20",
    "days": [
        {
            "day": 1,
            "theme": "Old City Heritage",
            "slots": [
                {
                    "time": "09:00",
                    "place": "City Palace",
                    "duration_min": 120,
                    "notes": "Open 9:30am-5:30pm daily",
                },
                {
                    "time": "14:00",
                    "place": "Jagdish Temple",
                    "duration_min": 60,
                    "notes": "Open 5am-10pm daily; dress modestly",
                },
            ],
        },
        {
            "day": 2,
            "theme": "Lakes & Sunset",
            "slots": [
                {
                    "time": "10:00",
                    "place": "Saheliyon Ki Bari",
                    "duration_min": 90,
                    "notes": "Open 8am-8pm daily",
                },
                {
                    "time": "16:30",
                    "place": "Lake Pichola Boat Ride",
                    "duration_min": 90,
                    "notes": "Sunset boat rides start 17:00",
                },
            ],
        },
    ],
}


def main():
    checks = []

    # 1. Plain Text / WhatsApp Export
    txt_exp = export_itinerary_text(trip_data=mock_trip)
    checks.append(("text export returns text", "text" in txt_exp and len(txt_exp["text"]) > 100))
    checks.append(("text export has destination in title", "Udaipur" in txt_exp["text"]))
    checks.append(("text export has days breakdown", "Day 1" in txt_exp["text"] and "Day 2" in txt_exp["text"]))
    checks.append(("text export has places", "City Palace" in txt_exp["text"] and "Saheliyon Ki Bari" in txt_exp["text"]))
    checks.append(("text export has emergency note", "112" in txt_exp["text"]))

    # 2. iCalendar (.ics) Export
    ics_exp = export_itinerary_ics(trip_data=mock_trip)
    checks.append(("ics export returns ics_content", "ics_content" in ics_exp))
    checks.append(("ics has VCALENDAR header", "BEGIN:VCALENDAR" in ics_exp["ics_content"]))
    checks.append(("ics has VCALENDAR footer", "END:VCALENDAR" in ics_exp["ics_content"]))
    checks.append(("ics has all 4 event stops", ics_exp.get("event_count") == 4))
    checks.append(("ics has VEVENT blocks", "BEGIN:VEVENT" in ics_exp["ics_content"]))
    checks.append(("ics has Asia/Kolkata timezone or timestamps", "DTSTART:" in ics_exp["ics_content"]))

    # 3. PDF Export fallback
    pdf_exp = export_itinerary_pdf(trip_data=mock_trip)
    checks.append(("pdf export returns response without raising", "format" in pdf_exp and pdf_exp.get("format") == "pdf"))
    checks.append(("pdf export has fallback text", bool(pdf_exp.get("fallback_text"))))

    # 4. Unified export dispatcher
    disp_txt = export_itinerary(format_type="text", trip_data=mock_trip)
    checks.append(("dispatcher text works", "text" in disp_txt))

    disp_ics = export_itinerary(format_type="ics", trip_data=mock_trip)
    checks.append(("dispatcher ics works", "ics_content" in disp_ics))

    disp_pdf = export_itinerary(format_type="pdf", trip_data=mock_trip)
    checks.append(("dispatcher pdf works", "pdf_engine_available" in disp_pdf))

    # 5. Registry tool execution
    reg_exp = execute_tool("export_itinerary", {"format_type": "text", "trip_data": mock_trip})
    checks.append(("registry executes export_itinerary", "text" in reg_exp))

    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")

    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
