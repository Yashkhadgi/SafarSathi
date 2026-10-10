# Phase 2 Architecture & Technical Blueprint

This document defines the production architecture for SafarSathi Phase 2, transitioning from the Gradio/SQLite prototype to a production-grade **FastAPI + PostgreSQL + React (Vite + TypeScript + Tailwind)** application.

---

## 1. Folder & System Structure

```text
SafarSathi_V.1.1/
├── backend/                        # FastAPI Backend Application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application factory & static mount
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic v2 settings (env parsing, secrets)
│   │   │   ├── security.py         # Argon2id hashing, Fernet encryption, JWT tokens
│   │   │   └── logging.py          # Structured JSON logging & request ID middleware
│   │   ├── db/
│   │   │   ├── session.py          # SQLAlchemy 2 async/sync engine & session factory
│   │   │   ├── base.py             # Declarative base model & metadata
│   │   │   └── models/             # SQLAlchemy ORM models
│   │   │       ├── user.py
│   │   │       ├── auth_session.py
│   │   │       ├── conversation.py
│   │   │       ├── trip.py
│   │   │       ├── profile.py
│   │   │       ├── contact.py
│   │   │       └── feedback.py
│   │   ├── repositories/           # Isolated data access layer (no SQL in routes)
│   │   │   ├── user_repo.py
│   │   │   ├── chat_repo.py
│   │   │   ├── trip_repo.py
│   │   │   └── profile_repo.py
│   │   ├── api/
│   │   │   ├── deps.py             # Auth dependencies & ownership verifiers
│   │   │   └── v1/
│   │   │       ├── router.py       # Main v1 API router aggregator
│   │   │       ├── auth.py         # Authentication & account management
│   │   │       ├── chat.py         # SSE streaming & conversation management
│   │   │       ├── trips.py        # Itineraries, versions, and exports
│   │   │       ├── profile.py      # Traveler preferences & privacy
│   │   │       ├── voice.py        # Sarvam STT/TTS proxy
│   │   │       ├── emergency.py    # Public static emergency data
│   │   │       ├── maps.py         # Server-side proxy for Google Maps with caching
│   │   │       └── admin.py        # Admin panel & analytics
│   │   └── services/               # Core business logic & agent adapters
│   │       ├── agent_adapter.py    # Bridge to agents/core_agent.py
│   │       ├── mailer.py           # Email service (SMTP / Resend / Console log)
│   │       └── scheduler.py        # APScheduler for reminders & check-ins
│   ├── alembic/                    # Database migration environment
│   │   ├── env.py
│   │   └── versions/
│   └── tests/                      # pytest backend test suite
│       ├── test_auth.py
│       ├── test_chat_ownership.py
│       ├── test_encryption.py
│       └── test_trips.py
│
├── frontend/                       # React Single Page Application (SPA)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── tokens/                 # Design tokens (colors, radii 6-8px, typography)
│       │   └── designTokens.ts
│       ├── fonts/                  # Self-hosted web fonts (Inter, Noto Sans Devanagari)
│       ├── api/                    # TanStack Query hooks & fetch clients
│       │   ├── client.ts           # Axios/fetch with CSRF & credential handling
│       │   ├── auth.ts
│       │   ├── chat.ts
│       │   └── trips.ts
│       ├── components/             # Reusable UI components (Lucide icons only)
│       │   ├── ui/                 # Buttons (6-8px radius), inputs, modals, cards
│       │   ├── layout/             # Topbar, sidebar, page wrappers
│       │   ├── chat/               # Chat stream, sources list, tool pill, voice button
│       │   ├── map/                # Google Maps JS API loader component
│       │   └── sos/                # Instant persistent SOS modal
│       ├── pages/                  # Route views
│       │   ├── LandingPage.tsx
│       │   ├── LoginPage.tsx
│       │   ├── SignupPage.tsx
│       │   ├── VerifyEmailPage.tsx
│       │   ├── ResetPasswordPage.tsx
│       │   ├── ChatPage.tsx
│       │   ├── ItineraryPage.tsx
│       │   ├── BudgetPage.tsx
│       │   ├── ProfilePage.tsx
│       │   ├── AccountPage.tsx
│       │   ├── AdminPage.tsx
│       │   ├── PrivacyPolicyPage.tsx
│       │   ├── TermsPage.tsx
│       │   └── NotFoundPage.tsx
│       └── store/                  # Lightweight client state (Zustand)
│           ├── authStore.ts
│           └── uiStore.ts
│
├── agents/                         # Core multi-agent logic (preserved from P0/P1)
├── tools/                          # Safe travel tools & registry (preserved from P0/P1)
├── data/                           # Knowledge base JSONs & budget benchmarks
├── docs/                           # Documentation & design standards
│   └── DESIGN_RULES.md
├── scripts/                        # Management & verification scripts
│   ├── design_lint.sh              # Design rule compliance checker
│   ├── migrate_sqlite_to_postgres.py # Data migration script
│   └── smoke_test.py               # Regression check
└── docker-compose.yml              # Local Postgres + Backend + Frontend development

```

### Production Frontend Serving
In production, the React frontend is built via `npm run build` into `frontend/dist/`. FastAPI serves these static assets:
- `/api/v1/*` routes handled by FastAPI routers.
- Static assets (`/assets/*`, favicon, manifest) served directly via `StaticFiles`.
- All non-API routes return `frontend/dist/index.html` (SPA HTML5 client-side routing).

---

## 2. PostgreSQL Database Schema (Step F1)

All tables use UUID v4 primary keys and enforce strict referential integrity with `ON DELETE CASCADE` from the `users` table.

```sql
-- 1. Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- Argon2id
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users(email);

-- 2. Auth Sessions & Refresh Tokens (Rotating, hashed storage)
CREATE TABLE auth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(64) NOT NULL, -- SHA-256 hash of refresh secret
    user_agent VARCHAR(512),
    ip_address VARCHAR(45),
    device_label VARCHAR(100),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_auth_sessions_user ON auth_sessions(user_id, created_at DESC);
CREATE INDEX idx_auth_sessions_hash ON auth_sessions(refresh_token_hash);

-- 3. Login Audit Events (90-day retention)
CREATE TABLE login_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    email_attempted VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_agent VARCHAR(512),
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_login_events_user ON login_events(user_id, created_at DESC);
CREATE INDEX idx_login_events_created ON login_events(created_at);

-- 4. Email Tokens (Verification & Password Reset)
CREATE TABLE email_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL,
    token_type VARCHAR(20) NOT NULL, -- 'verify_email', 'reset_password'
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_email_tokens_lookup ON email_tokens(token_hash, token_type);

-- 5. OAuth Accounts (Google Sign-In)
CREATE TABLE oauth_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL, -- 'google'
    provider_user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(provider, provider_user_id)
);

-- 6. Conversations (Chat Sessions)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL DEFAULT 'New chat',
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_conversations_user ON conversations(user_id, updated_at DESC);

-- 7. Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    tools_used JSONB DEFAULT '[]'::jsonb,
    sources JSONB DEFAULT '[]'::jsonb,
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_messages_convo ON messages(conversation_id, created_at ASC);
CREATE INDEX idx_messages_user ON messages(user_id, created_at DESC);
-- Full text search index on message content
CREATE INDEX idx_messages_fts ON messages USING gin(to_tsvector('english', content));

-- 8. Trips
CREATE TABLE trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    title VARCHAR(150) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    start_date DATE,
    duration_days INT NOT NULL,
    data_json JSONB NOT NULL,
    current_version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_trips_user ON trips(user_id, updated_at DESC);

-- 9. Trip Versions (Immutable version history)
CREATE TABLE trip_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    version INT NOT NULL,
    change_summary VARCHAR(255) NOT NULL,
    data_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(trip_id, version)
);

-- 10. Traveler Profiles
CREATE TABLE profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    home_city VARCHAR(100),
    diet_preference VARCHAR(50) DEFAULT 'all', -- 'veg', 'vegan', 'jain', 'halal', 'all'
    allergies JSONB DEFAULT '[]'::jsonb,
    travel_style VARCHAR(50) DEFAULT 'normal', -- 'relaxed', 'normal', 'packed'
    budget_range VARCHAR(50) DEFAULT 'mid',    -- 'backpacker', 'mid', 'luxury'
    mobility_notes TEXT,
    interests JSONB DEFAULT '[]'::jsonb,
    consent_location BOOLEAN NOT NULL DEFAULT FALSE,
    consent_contacts BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 11. Trusted Contacts (Phone numbers encrypted at rest with Fernet)
CREATE TABLE trusted_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    phone_encrypted TEXT NOT NULL, -- AES-128-CBC / Fernet authenticated ciphertext
    relationship VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_trusted_contacts_user ON trusted_contacts(user_id);

-- 12. Feedback
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    rating INT NOT NULL, -- +1 (thumbs up), -1 (thumbs down)
    reason VARCHAR(100), -- 'wrong_info', 'too_long', 'language_error', 'other'
    comment TEXT,
    tools_used JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_feedback_user ON feedback(user_id, created_at DESC);
```

---

## 3. API Endpoint Specification (`/api/v1`)

| Method | Endpoint | Auth Req? | Purpose / Functionality |
|---|---|---|---|
| **GET** | `/api/v1/health` | No | System health check (PostgreSQL connectivity, version). |
| **GET** | `/api/v1/emergency` | No | Public emergency numbers, static phrases, and nearby hospital logic (cached, no LLM). |
| **POST** | `/api/v1/auth/signup` | No | Register new email + password with Argon2id; emits verification token. |
| **POST** | `/api/v1/auth/verify-email` | No | Confirm email address token. |
| **POST** | `/api/v1/auth/login` | No | Authenticate credentials; sets `httpOnly` secure access & rotating refresh cookies; records login event. |
| **POST** | `/api/v1/auth/refresh` | No (Cookie) | Rotates refresh token and issues new access token. |
| **POST** | `/api/v1/auth/logout` | Yes | Revokes current session and clears auth cookies. |
| **POST** | `/api/v1/auth/logout-all` | Yes | Revokes all active sessions for current user. |
| **POST** | `/api/v1/auth/forgot-password` | No | Initiates password reset flow with rate limiting. |
| **POST** | `/api/v1/auth/reset-password` | No | Sets new password with verified token. |
| **GET** | `/api/v1/auth/me` | Yes | Get current user details, verification status, and profile summary. |
| **GET** | `/api/v1/auth/sessions` | Yes | List all active devices and login history (IP, user agent, last seen). |
| **DELETE** | `/api/v1/auth/sessions/{id}` | Yes | Revoke specific session (ownership checked). |
| **GET** | `/api/v1/auth/export-data` | Yes | Download complete user data package (JSON format). |
| **DELETE** | `/api/v1/auth/account` | Yes | Hard delete account and all cascade data (requires password confirmation). |
| **POST** | `/api/v1/chat` | Yes | **Server-Sent Events (SSE)** endpoint. Streams response tokens, tool status events, source citations, and message IDs. |
| **GET** | `/api/v1/conversations` | Yes | List paginated conversations for current user with search. |
| **POST** | `/api/v1/conversations` | Yes | Create new conversation. |
| **GET** | `/api/v1/conversations/{id}` | Yes | Get message history for conversation (paginated). |
| **PATCH** | `/api/v1/conversations/{id}` | Yes | Rename conversation. |
| **DELETE** | `/api/v1/conversations/{id}` | Yes | Delete conversation and dependent messages. |
| **GET** | `/api/v1/trips` | Yes | List saved trips for current user. |
| **POST** | `/api/v1/trips` | Yes | Save new itinerary. |
| **GET** | `/api/v1/trips/{id}` | Yes | Get specific trip with all version histories. |
| **PATCH** | `/api/v1/trips/{id}` | Yes | Apply patch edit / undo operation to trip. |
| **DELETE** | `/api/v1/trips/{id}` | Yes | Delete trip. |
| **POST** | `/api/v1/trips/{id}/export` | Yes | Export trip as WhatsApp Text, `.ics` iCalendar, or PDF. |
| **GET** | `/api/v1/profile` | Yes | Get user profile preferences & privacy consents. |
| **PUT** | `/api/v1/profile` | Yes | Update profile, diet, mobility, and consent toggles. |
| **GET** | `/api/v1/trusted-contacts` | Yes | List trusted contacts (decrypted). |
| **POST** | `/api/v1/trusted-contacts` | Yes | Add trusted contact (encrypted at rest). |
| **DELETE** | `/api/v1/trusted-contacts/{id}` | Yes | Remove trusted contact. |
| **POST** | `/api/v1/feedback` | Yes | Submit 👍/👎 feedback with reason code for a message turn. |
| **POST** | `/api/v1/voice/transcribe` | Yes | Speech-to-text proxy (Sarvam AI / fallback). |
| **POST** | `/api/v1/voice/speak` | Yes | Text-to-speech proxy (Sarvam AI / fallback). |
| **GET** | `/api/v1/maps/places` | Yes | Server-side cached Google Places proxy. |
| **GET** | `/api/v1/admin/analytics` | Yes (Admin) | Anonymized tool usage, latency, error rate, content gap queries. |
| **GET** | `/api/v1/admin/kb` | Yes (Admin) | List and filter knowledge base records. |
| **POST** | `/api/v1/admin/kb` | Yes (Admin) | Create/update KB record with automated validation. |

---

## 4. Frontend Structure & Routing

### Design Rules Adherence
- **Colors**: Solid neutrals (Zinc/Slate: `#09090b`, `#18181b`, `#27272a`, `#f4f4f5`, `#ffffff`), single high-contrast accent (`#0284c7` Deep Sky / `#0369a1`), zero purple gradients.
- **Typography**: Self-hosted `Inter` for UI body, `Noto Sans Devanagari` for Indic scripts.
- **Components**: 6px to 8px border radii (`rounded-md` / `rounded-lg`). Lucide-react SVG icons only. No emojis as icons.
- **Copy & Imagery**: Clear, factual headlines. Honest empty states. Zero fake customer reviews or artificial metrics.

### Routes Table

| Route Path | View Component | Access | Layout |
|---|---|---|---|
| `/` | `LandingPage` | Public | Public header + footer, features, zero hype copy |
| `/login` | `LoginPage` | Public (guest) | Centered card, rate-limited form |
| `/signup` | `SignupPage` | Public (guest) | Centered card with password requirements |
| `/verify-email` | `VerifyEmailPage` | Public | Token validation status card |
| `/forgot-password` | `ForgotPasswordPage` | Public | Generic response to prevent user enumeration |
| `/reset-password` | `ResetPasswordPage` | Public | New password form |
| `/privacy` | `PrivacyPolicyPage` | Public | Transparent data flows, retention & rights |
| `/terms` | `TermsPage` | Public | Terms of service and disclaimers |
| `/app` | `ChatPage` | Authenticated | Main Shell: Collapsible sidebar + Chat stream + SOS button |
| `/app/c/:conversationId` | `ChatPage` | Authenticated | Specific conversation thread |
| `/app/trips` | `TripsPage` | Authenticated | List of saved itineraries with version history |
| `/app/trips/:tripId` | `TripDetailPage` | Authenticated | Day-by-day planner, map pins, budget view, export |
| `/app/profile` | `ProfilePage` | Authenticated | Diet, mobility, home city, language preferences |
| `/app/account` | `AccountPage` | Authenticated | Security, active sessions, login history, data export, delete |
| `/app/admin` | `AdminPage` | Admin only | KB editor, feedback inspector, real metrics dashboard |
| `*` | `NotFoundPage` | Public | High-contrast 404 with back-to-home link |

---

## 5. Agent Integration & P0 Compatibility

The backend uses a clean adapter layer ([`backend/app/services/agent_adapter.py`](file:///Users/yashkhadgi/Downloads/SafarSathi_V.1.1/backend/app/services/agent_adapter.py)) that wraps the existing [`agents/core_agent.py`](file:///Users/yashkhadgi/Downloads/SafarSathi_V.1.1/agents/core_agent.py) and [`tools/registry.py`](file:///Users/yashkhadgi/Downloads/SafarSathi_V.1.1/tools/registry.py):

1. **Dual Run Modes**:
   - `stream_core_agent(session_id, message)` yields incremental events (`status`, `partial`, `done`, `tools_used`, `tool_results`).
   - The SSE endpoint consumes these generator events and converts them directly into formatted Server-Sent Events for the React UI.
2. **Context Injection**:
   - The adapter loads the user's profile preferences from PostgreSQL (`diet_preference`, `allergies`, `mobility_notes`) and provides them to the agent.
   - Message history is fetched from the PostgreSQL `messages` table for the active `conversation_id`.
3. **P0 Legacy Compatibility**:
   - The legacy `orchestrator_graph` and feature flag `USE_TOOL_AGENT` remain fully intact.
   - All 24 offline smoke test suites continue running directly against the agent and tool modules.

---

## 6. Migration Strategy

- **Database Migration (`sessions.db` -> PostgreSQL)**:
  - An idempotent migration script [`scripts/migrate_sqlite_to_postgres.py`](file:///Users/yashkhadgi/Downloads/SafarSathi_V.1.1/scripts/migrate_sqlite_to_postgres.py) reads SQLite tables (`users`, `sessions`, `turns`, `trips`, `trip_versions`, `profiles`, `trusted_contacts`, `feedback`) and maps them into PostgreSQL with UUID primary keys and preserved timestamps.
  - A compatibility shim in `memory/session_memory.py` directs read/write operations to the repository layer when `DATABASE_URL` is set, falling back to SQLite if unset.
- **Gradio Transition (F1 to F6)**:
  - `ui/app.py` (Gradio) remains in the repository and continues functioning throughout F1–F5.
  - In step **F6**, once all P0/P1 views are operational in React and pass the manual demo script, the default entry point switches to the FastAPI + React app, and Gradio is tagged as `gradio-legacy`.

---

## 7. Risks, Prerequisites & Requirements from User

| Item | Requirement / Risk | Required From User |
|---|---|---|
| **PostgreSQL Database** | PostgreSQL 15+ instance for local dev and production. | Local Docker Compose provided; production connection string (`DATABASE_URL`) needed at launch. |
| **Contact Encryption Key** | 32-byte Fernet base64 key for encrypting trusted contact phone numbers at rest. | Generated automatically in development; user configures `CONTACTS_ENCRYPTION_KEY` in production. |
| **Google Maps Browser Key** | Separate client-side Maps JavaScript key with HTTP-referrer domain restrictions (never using the backend key in browser). | Setup in Google Cloud Console with domain restriction for production. |
| **Email Delivery (Auth)** | Email verification and password resets require an SMTP server or Resend API key in production. | In local development, links are logged to the console; production requires Resend or SMTP credentials. |
| **Custom Domain & HTTPS** | Production launch requires HTTPS with SSL certificates. | Domain ownership and DNS configuration needed at step L1. |

---

## 8. The 10 Architectural Decisions & Recommendations

Please review the 10 decisions below and confirm your approval:

1. **Production Hosting Target**:
   - *Recommendation*: **Render or Single Linux VPS with Docker Compose** (Standardized container running FastAPI + static frontend build + managed Postgres).
2. **Database Engine**:
   - *Recommendation*: **PostgreSQL 16 via SQLAlchemy 2 + Alembic** (Async engine with connection pooling).
3. **Frontend Build Delivery**:
   - *Recommendation*: **FastAPI mounts `frontend/dist` as static assets** (Single-service simplicity, zero CORS friction in production, unified Docker container).
4. **Email Provider Strategy**:
   - *Recommendation*: **Console logging in development; Resend API or SMTP interface in production** configured via `MAIL_PROVIDER` environment variable.
5. **Auth Session Management**:
   - *Recommendation*: **Dual Cookie Strategy**: 15-minute `httpOnly` `SameSite=Lax` JWT access cookie + 30-day rotating refresh token cookie stored as SHA-256 hash in `auth_sessions`, plus double-submit CSRF token header for state-modifying requests.
6. **Voice Provider Strategy**:
   - *Recommendation*: **Sarvam AI API (STT/TTS) backend proxy** with fallback for Indic languages, keeping API keys securely on the server.
7. **Google Maps Key Isolation**:
   - *Recommendation*: **Dual-Key Policy**: `GOOGLE_MAPS_BROWSER_KEY` (restricted to web domain referrer for `@googlemaps/js-api-loader`) + server-side key for Places/Directions API.
8. **Chat Streaming Protocol**:
   - *Recommendation*: **Server-Sent Events (`text/event-stream`)** over HTTP/2 (Simpler than WebSockets, natively reconnecting, standard for LLM token streaming).
9. **Scheduler Architecture**:
   - *Recommendation*: **PostgreSQL-backed APScheduler** running in the FastAPI backend worker process (no Redis/Celery dependency required).
10. **Frontend State Management**:
    - *Recommendation*: **TanStack Query v5 (server cache & SSE invalidation) + Zustand (client UI state & auth tokens)**.

---

*Phase 2 Architecture Plan complete. Awaiting user approval to proceed to Step F1.*
