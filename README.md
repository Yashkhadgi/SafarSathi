# SafarSathi

SafarSathi is a Gradio travel assistant focused on India. It combines a sourced destination knowledge base with session-based chat and voice, budget estimates, local transport guidance, scam alerts, language support, and offline emergency information. SOS numbers and emergency phrases remain available without an LLM or API key. Trusted-contact sharing creates prefilled WhatsApp/SMS links; the app does not send messages.

The current checkout does not include itinerary creation or editing. Live weather, maps, web search, translation, and LLM features depend on the corresponding provider keys.

## Features

- Per-user chat sessions, language preference, and voice interface.
- Retrieval from the local ChromaDB knowledge base with source information.
- Python-calculated budget estimates and tier comparisons for supported cities.
- How-to-reach and local transport guidance, with unavailable live details marked for verification.
- Sourced scam alerts for cities represented in the knowledge base.
- Static SOS numbers and emergency phrases; optional nearby emergency services lookup.
- Up to three consented trusted contacts, with user-approved prefilled share links.

## Requirements

- Python 3.11 for local installation.
- Docker Engine and Docker Compose v2 for container deployment.
- An Anthropic API key for assistant chat. Other integrations are optional.
- Internet access on first knowledge-base build so ChromaDB can download its default embedding model. Keep `data/embeddings/` between runs to avoid rebuilding it.

## Environment

Copy the template and set only the credentials for integrations you intend to use:

```sh
cp config/.env.example config/.env
```

| Key | Required | Purpose |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | For chat | Claude responses and language fallback. Without it, chat is unavailable; SOS remains usable. |
| `ORCHESTRATOR_MODEL` | Optional | Orchestrator model override. |
| `PLANNER_MODEL` | Optional | Planner model override. |
| `RAG_MODEL` | Optional | RAG model override. |
| `SAFETY_MODEL` | Optional | Safety model override. |
| `ETIQUETTE_MODEL` | Optional | Etiquette model override. |
| `GOOGLE_MAPS_API_KEY` | Optional | Maps, distance, places, and nearby emergency lookup. |
| `OPENWEATHER_API_KEY` | Optional | Weather lookup. |
| `EXCHANGE_RATE_API_KEY` | Optional | Currency conversion. |
| `BHASHINI_API_KEY` | Optional | Speech/language integration where configured. |
| `TAVILY_API_KEY` | Optional | Web search fallback. |
| `SARVAM_API_KEY` | Optional | Sarvam translation for supported Indian languages. |
| `USE_TOOL_AGENT` | Optional | Feature-flag setting reserved for tool-agent routing; defaults to `false`. |

Do not commit `config/.env`. The Docker build excludes local environment files; Compose passes `config/.env` to the running container.

## Local Setup

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp config/.env.example config/.env
```

Edit `config/.env`, then validate and build the local knowledge base:

```sh
python scripts/validate_kb.py
python scripts/build_knowledge_base.py
```

Start the app:

```sh
python ui/app.py
```

Open [http://localhost:7860](http://localhost:7860). Run the offline and integration smoke checks with:

```sh
python scripts/smoke_test.py
```

The optional tiny Anthropic request runs only when `ANTHROPIC_API_KEY` is set. The other smoke suites use local data or mocks.

## Docker

Create `config/.env` as above, then build and start:

```sh
docker compose up --build
```

On the first start, the entrypoint validates the JSON records and builds the ChromaDB collection before launching Gradio on port 7860. The `memory/` and `data/embeddings/` directories are mounted from the host for persistence. Open [http://localhost:7860](http://localhost:7860). Stop with `Ctrl+C`; remove the container with `docker compose down`.

To run the project smoke test inside the built image:

```sh
docker compose run --rm --entrypoint python safarsathi scripts/smoke_test.py
```

## Knowledge Base

Place schema-compliant JSON records in `data/knowledge_base/`. Validate and upsert all JSON files into the persistent `tourist_kb` collection:

```sh
python scripts/validate_kb.py
python scripts/build_knowledge_base.py
```

Upserts are idempotent by record ID. Review each record's source and verification date before presenting its facts as current.

## Troubleshooting

- **Chat says the assistant is unavailable:** set a valid `ANTHROPIC_API_KEY` in `config/.env` and restart the app/container. Static SOS content does not need the key.
- **Compose says the env file is missing:** create `config/.env` from `config/.env.example` before `docker compose up`.
- **Knowledge-base validation fails:** run `python scripts/validate_kb.py` and correct the reported record fields, URLs, dates, or duplicate IDs.
- **ChromaDB collection is empty:** run `python scripts/build_knowledge_base.py`; on first build, check internet access for the embedding model download.
- **Gradio/Pydantic import or launch error:** use Python 3.11 and install the pinned dependencies in a fresh virtual environment. Avoid upgrading Gradio or Pydantic independently of `requirements.txt`.
- **Docker port 7860 is occupied:** change the host side of the Compose mapping, for example `7861:7860`, then open `http://localhost:7861`.
- **Maps, web search, weather, or translation is unavailable:** check the corresponding optional key. Without live provider data the app may return a verification note or static fallback.
- **Persistent state looks stale:** the app uses the host `memory/` and `data/embeddings/` directories. Back them up before manually removing or replacing their contents.

## Scope Note

This repository is being built in planned batches. Use `plans/P0.md` for the P0 exit checklist; a passing packaging smoke test does not imply every planned P0 capability is implemented.
