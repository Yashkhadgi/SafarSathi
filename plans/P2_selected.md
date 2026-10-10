# Phase 2 Selected Specs and Roadmap

## Section 1: Phase 2 Step Sequence

### Foundation Steps (F0 - F7)
- **F0: Architecture Plan & Decisions** — System architecture, schema design, API specs, component map, and 10 key decisions.
- **F1: Database + Chat History** — PostgreSQL via SQLAlchemy 2 + Alembic, repository layer, encryption for contacts, migration script from `sessions.db`.
- **F2: Auth, Login History, Account** — Argon2id password hashing, httpOnly SameSite secure cookie sessions with refresh rotation, CSRF protection, rate limiting, lockout, audit logs.
- **F3: API Layer** — FastAPI `/api/v1` with SSE `/chat` stream, conversations pagination, voice endpoints, static `/emergency`, rate limiting.
- **F4: Frontend Foundation** — Vite + React + TypeScript + Tailwind, self-hosted fonts, design tokens (6-8px radius, no purple gradients), public pages, `scripts/design_lint.sh`.
- **F5: Chat UI, History, SOS** — App shell with sidebar, SSE streaming viewer, source citations, tools status, persistent offline-capable SOS modal.
- **F6: Port P0/P1 Screens** — Itinerary viewer/editor, budget tier comparison, transport & stay, trusted contacts, settings. Gradio legacy transition.
- **F7: Google Maps in App** — Dual-key security (`GOOGLE_MAPS_BROWSER_KEY` vs backend key), `@googlemaps/js-api-loader` map component, itinerary route lines, near-me pins.

### Feature Steps (X1 - X8)
- **X1: Content Pack** — KB categories for saving tips, 20 transport hubs, shopping & nightlife, and 15 popular trekking routes.
- **X2: Events and Alerts** — Festival calendar 2026/2027, itinerary date overlap alerts, disaster/weather warnings.
- **X3: Trip Tools** — In-app expense tracker vs trip budget (pure math, note-keeping only), road trip planner with rest/fuel stops.
- **X4: Admin Panel and Analytics** — Role-based `/admin`, KB visual editor, feedback viewer, anonymized usage metrics, CSV export.
- **X5: PWA and Offline** — Service worker, app shell cache, offline SOS, phrasebook, and saved trips viewing.
- **X6: Check-in and Reminders** — APScheduler in Postgres, Web Push notifications, departure/checkout reminders, solo check-in timers.
- **X7: Voice-first and Camera OCR** — Push-to-talk voice interface, optional vision OCR for signboards/menus with zero photo storage.
- **X8: Accessibility Audit** — WCAG 2.2 AA compliance, keyboard navigation, ARIA live streaming, automated axe audit.

### Launch Preparation (L1)
- **L1: Launch Checklist** — Security hardening (CSP, HSTS, CORS), dependency audit, Privacy Policy & Terms verification, production deployment guide.

---

## Section 2: The 10 Core Architectural Decisions

1. **Production Hosting Target**: Render vs Railway vs Single Linux VPS with Docker Compose.
2. **Database Engine**: Managed PostgreSQL 16 vs Containerized PostgreSQL in Compose.
3. **Frontend Build Delivery**: FastAPI static mounting (`backend/static`) vs independent CDN/Vercel/Cloudflare Pages.
4. **Email Provider for Auth Verification**: Local console logging in dev + Resend API vs standard SMTP in production.
5. **Token Storage & Auth Flow**: Dual cookie (short-lived access cookie + rotating refresh cookie) with CSRF double-submit token vs pure Bearer headers in Authorization header.
6. **Voice Provider Strategy**: Sarvam AI API for Indic languages (STT/TTS) with Haiku/Bhashini fallback vs browser Web Speech API.
7. **Maps Dual-Key Configuration**: Restricted client-side Google Maps JavaScript API key (HTTP referrer domain locked) + server-side Places/Directions key.
8. **Real-time Streaming Protocol**: Server-Sent Events (`text/event-stream`) vs WebSockets.
9. **Scheduler Backend**: PostgreSQL-persisted APScheduler (single-instance backend) vs Celery + Redis.
10. **State Management & Data Fetching**: TanStack Query v5 + Zustand in React vs Redux Toolkit.
