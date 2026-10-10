# Batch B0 Tracker

Done:
- Read `plans/P0.md` sections `0. Kaam karne ka tareeka` and `B0 (prep): Baseline`.
- Created `AGENTS.md` at the repo root from the plan snippet.
- Updated `config/.env.example` with every key used in `config/settings.py`, empty values, and `USE_TOOL_AGENT=false`.
- Updated default model names in `config/settings.py` while keeping non-empty environment variable overrides.
- Created `scripts/smoke_test.py` with checks for config loading, SQLite, ChromaDB, Gradio import, and optional Anthropic LLM call.

Verification:
- Done: ran `python3 scripts/smoke_test.py`; non-LLM checks passed, optional LLM check failed with a connection error because `ANTHROPIC_API_KEY` is set locally and network/API access was unavailable for that check.
- Done: ran `ANTHROPIC_API_KEY= python3 scripts/smoke_test.py`; all checks passed with the optional LLM call skipped.
- Done: verified `pip install -r requirements.txt` in a fresh virtual environment at `/private/tmp/safarsathi-b0-venv`; install succeeded after network access was allowed.
