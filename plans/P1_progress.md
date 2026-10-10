# P1 Progress

Current branch: `p1/full-build`. The P0 completion tag is still absent; all 34 P1 features across batches B1 to B16 are implemented and pass all 24 offline smoke test suites. Manual checkpoints are awaiting human verification.

| Batch | Status | Notes |
| --- | --- | --- |
| B1 Auth/privacy, cache/rate limit | awaiting-my-check | PBKDF2 auth, privacy consent/delete, TTL cache, rate limiter implemented. All 15 offline checks pass. Manual checkpoint pending. |
| B2 Profiles, saved trips | awaiting-my-check | Profiles, saved trips, and favorites isolated per-user. All 8 offline checks pass. Manual checkpoint pending. |
| B3 Streaming, feedback | awaiting-my-check | Token streaming generator and feedback DB/reports pass offline. Manual checkpoint pending. |
| B4 Weather/AQI, hours, near me | awaiting-my-check | Live weather/AQI, opening hours conflicts, and Near Me tool with consent pass offline. Live provider check pending. |
| B5 Map | awaiting-my-check | OSM Leaflet map with day filtering and 25-pin payload reduction pass offline. Live geocoding/browser check pending. |
| B6 Language, phrasebook, emergency audio | awaiting-my-check | Auto language detection, 8-situation phrasebook, and SOS phrases pass offline; Marathi/Gujarati offline audio pending native recording. |
| B7 Two-way translation | awaiting-my-check | Two-column UI and mocked translation pipeline pass offline; live microphone/latency check pending. |
| B8 Safety/medical/lost documents | awaiting-my-check | Area safety, medical help (no dosages, disclaimers, 108/112), and lost document workflows pass offline. Manual checkpoint pending. |
| B9 Entry fees/fair price/currency | awaiting-my-check | ASI monument entry fees, fair-price guidance, and ATM advice pass offline. Manual checkpoint pending. |
| B10 Train/bus, stay areas | awaiting-my-check | Train/bus route info (with IRCTC note, no booking links) and stay area recommendations pass offline. Manual checkpoint pending. |
| B11 Food, temple, etiquette | awaiting-my-check | Dietary food filter (veg/vegan/Jain/halal), temple guidelines, and regional etiquette pass offline. Manual checkpoint pending. |
| B12 Theme/traveler plans, Plan B | awaiting-my-check | 9 travel themes, 5 traveler types (kids, senior, accessibility), and weather-triggered Plan B pass offline. Manual checkpoint pending. |
| B13 Recommender, best time | awaiting-my-check | Python-scored destination recommender (budget, season, tags, distance) and best-time lookups pass offline. Manual checkpoint pending. |
| B14 Multi-city optimizer | awaiting-my-check | Nearest-neighbour TSP heuristic and proportional day allocation with haversine distance pass offline. Manual checkpoint pending. |
| B15 Packing/pre-trip checklist | awaiting-my-check | Smart packing list (differentiated for Goa/Ladakh/monsoon) and T-30/T-7/T-1 timeline checklists pass offline. Manual checkpoint pending. |
| B16 Export | awaiting-my-check | WhatsApp text, RFC 5545 iCalendar (.ics), and PDF renderer fallback pass offline. Manual checkpoint pending. |

