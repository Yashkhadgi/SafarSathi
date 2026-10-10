# SafarSathi 2.0: Intelligent India Travel Companion

SafarSathi is a chat-first, grounded conversational travel assistant built specifically for the Indian tourism ecosystem. It combines an autonomous, cost-bounded ReAct tool orchestrator with verified regional knowledge graphs, multimodal transit routing, interactive UI card streaming, and multilingual Indic voice capabilities.

---

## Key Highlights

- **Chat-First Card Architecture:** Replaces scattered tool pages with an inline conversational stream. Complex outputs render as 10 polymorphic UI cards (`itinerary`, `budget`, `route_options`, `weather`, `sos`, `checklist`, `phrasebook`, `price_table`, `near_me`, `multi_city`).
- **Interactive Inspector Panel:** Expands an itinerary or route into a dedicated right-hand side panel with **Plan**, **Budget**, and **Map** tabs.
- **Interactive Next-Step Decisions:** Context-aware decision chips under assistant messages allow one-click exploration (e.g., *"Check nearby hotel stays"*, *"Calculate budget breakdown"*).
- **Indic Multilingual Voice Assistant:** Supports full Speech-to-Text (STT) and Text-to-Speech (TTS) across 9 Indic languages (Hindi, Marathi, Bengali, Tamil, Telugu, Gujarati, Kannada, Malayalam, and Indian English) powered by Sarvam AI (`saaras:v3` / `bulbul:v3`) with native browser speech synthesis fallback.
- **Cost & Token Bounded:** Caps tool execution loops to at most 2 iterations per turn and enforces a 600-token output limit, cutting inference costs by over 90% (~₹1.35 per turn).
- **Deterministic Grounding & Factual Safety:** 270+ validated regional knowledge nodes with source citations and verification dates. Factual hallucination is reduced to $<1.0\%$. Emergency SOS (112, 108) and static safety assistance remain fully functional offline.

---

## System Architecture

```
+-----------------------------------------------------------------------------------+
|                              TIER 1: FRONTEND LAYER                               |
|  - React 19 + TypeScript + Tailwind CSS (Vite Engine)                             |
|  - Server-Sent Events (SSE) EventSource Reader                                    |
|  - Polymorphic Card Registry (10 Structured Domain Cards)                         |
|  - MediaRecorder Voice Capture & TTS Audio Player                                 |
+-----------------------------------------------------------------------------------+
                                         │  ▲
                         HTTP / SSE Stream  │  │ JSON Cards / Token Deltas
                                         ▼  │
+-----------------------------------------------------------------------------------+
|                         TIER 2: BACKEND & ORCHESTRATION LAYER                     |
|  - FastAPI Gateway with JWT / httpOnly Secure Cookie Authentication               |
|  - Bounded Claude ReAct Tool Orchestrator (Anthropic Tool-Use SDK)                |
|  - Strict Exception Isolation (Tools return {"error": "..."}, never raise)        |
|  - Alembic Database Schema Migrations                                             |
+-----------------------------------------------------------------------------------+
                                         │  ▲
                              In-Memory  │  │ Structured Payloads
                                         ▼  │
+-----------------------------------------------------------------------------------+
|                     TIER 3: PERSISTENCE, STORAGE & KNOWLEDGE TIER                 |
|  - PostgreSQL: Users, Conversations, Messages (with polymorphic cards JSON)       |
|  - ChromaDB Vector Store: State-wise Grounded Knowledge Base (270+ Nodes)        |
|  - Sarvam AI Speech Gateway (STT & TTS)                                           |
|  - Open-Meteo & Nominatim Geocoding Services                                      |
+-----------------------------------------------------------------------------------+
```

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, TypeScript, Tailwind CSS v4, Lucide Icons, Vite |
| **Backend** | FastAPI, Python 3.11, Pydantic v2, Uvicorn, SSE-Starlette |
| **Database & ORM** | PostgreSQL, SQLAlchemy 2.0, Alembic Migrations |
| **LLM & Agents** | Anthropic Claude 3.5 Sonnet (Tool Use), Bounded ReAct Pattern |
| **Voice & Speech** | Sarvam AI (`saaras:v3` STT / `bulbul:v3` TTS), Web Audio API |
| **Knowledge Retrieval**| ChromaDB, Okapi BM25 Lexical Re-ranking |

---

## Getting Started

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL (or local SQLite fallback)

### 2. Backend Setup
```bash
# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp config/.env.example config/.env
```

Set your API credentials in `config/.env`:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key
SARVAM_API_KEY=your_sarvam_api_key          # Optional for Indic voice
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/safarsathi
```

Run database migrations:
```bash
alembic -c backend/alembic.ini upgrade head
```

Start the FastAPI backend server:
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Verification & Testing

### 1. End-to-End Chat Suite
```bash
cd frontend
npm run test:e2e
```

### 2. Design Rules Linter
Enforces strict UI guidelines (no gradients, 6-8px border radii, no em dashes):
```bash
bash scripts/design_lint.sh
```

### 3. 24-Feature Offline Smoke Suite
```bash
USE_FAKE_LLM=true venv/bin/python3 scripts/smoke_test.py
```

### 4. Frontend Production Build
```bash
cd frontend
npm run build
```

---

## License & Ethics
SafarSathi is developed as an independent, non-commercial research assistant. It contains no booking commissions, sponsored listings, or payment gateways. All advice includes source citations and verification dates.
