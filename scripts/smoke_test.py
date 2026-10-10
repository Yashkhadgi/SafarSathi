import os
import subprocess
import sqlite3
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _print_result(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"{status}: {name}{suffix}")


def check_config_load():
    from config import settings

    required_attrs = [
        "ANTHROPIC_API_KEY",
        "ORCHESTRATOR_MODEL",
        "PLANNER_MODEL",
        "RAG_MODEL",
        "SAFETY_MODEL",
        "ETIQUETTE_MODEL",
        "GOOGLE_MAPS_API_KEY",
        "OPENWEATHER_API_KEY",
        "EXCHANGE_RATE_API_KEY",
        "BHASHINI_API_KEY",
        "TAVILY_API_KEY",
        "SARVAM_API_KEY",
    ]
    missing = [name for name in required_attrs if not hasattr(settings, name)]
    if missing:
        return False, f"missing settings: {', '.join(missing)}"
    return True, "settings imported"


def check_kb_validation():
    from scripts.validate_kb import load_records, validate_records

    records, load_errors = load_records(PROJECT_ROOT / "data" / "knowledge_base")
    errors = load_errors + validate_records(records)
    if errors:
        return False, "; ".join(errors[:3])
    return True, f"{len(records)} records valid"


def check_offline_p0_features():
    scripts = [
        "smoke_budget.py",
        "smoke_transport.py",
        "smoke_sos.py",
        "smoke_trusted_contacts.py",
        "smoke_scam_alerts.py",
        "smoke_language_agent.py",
        "smoke_guardrails.py",
        "smoke_itinerary.py",
        "smoke_p1_b1.py",
        "smoke_p1_b2.py",
        "smoke_p1_b3.py",
        "smoke_p1_b4.py",
        "smoke_p1_b5.py",
        "smoke_p1_b6.py",
        "smoke_p1_b7.py",
        "smoke_p1_b8.py",
        "smoke_p1_b9.py",
        "smoke_p1_b10.py",
        "smoke_p1_b11.py",
        "smoke_p1_b12.py",
        "smoke_p1_b13.py",
        "smoke_p1_b14.py",
        "smoke_p1_b15.py",
        "smoke_p1_b16.py",
    ]
    failures = []
    for script in scripts:
        path = PROJECT_ROOT / "scripts" / script
        result = subprocess.run(
            [sys.executable, str(path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        if result.returncode:
            details = (result.stdout + "\n" + result.stderr).strip().splitlines()
            failures.append(f"{script}: {' | '.join(details[-4:])}")
    if failures:
        return False, "; ".join(failures)
    return True, f"{len(scripts)} offline feature suites passed"


def check_sqlite_open():
    db_path = PROJECT_ROOT / "memory" / "sessions.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("SELECT 1").fetchone()
    finally:
        conn.close()
    return True, str(db_path)


def check_chromadb_query():
    import chromadb

    embeddings_path = PROJECT_ROOT / "data" / "embeddings"
    client = chromadb.PersistentClient(path=str(embeddings_path))
    collection = client.get_or_create_collection(name="tourist_kb")
    count = collection.count()
    if count == 0:
        return False, "tourist_kb collection is empty; run scripts/build_knowledge_base.py"
    results = collection.query(query_texts=["Hawa Mahal"], n_results=1)
    docs = results.get("documents", [[]])[0]
    if not docs:
        return False, "query returned no documents"
    return True, f"queried {count} documents"


def check_gradio_import():
    import gradio

    return True, f"gradio {gradio.__version__}"


def check_optional_llm_call():
    from config.settings import ANTHROPIC_API_KEY, RAG_MODEL

    if not ANTHROPIC_API_KEY:
        return True, "skipped; ANTHROPIC_API_KEY not set"

    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=RAG_MODEL,
        max_tokens=8,
        system="Reply with one short word.",
        messages=[{"role": "user", "content": "Say ok"}],
    )
    text = response.content[0].text.strip() if response.content else ""
    if not text:
        return False, "empty LLM response"
    return True, "LLM responded"


def run_check(name, func):
    try:
        ok, detail = func()
    except Exception as exc:
        ok, detail = False, str(exc)
    _print_result(name, ok, detail)
    return ok


def main():
    checks = [
        ("config loads", check_config_load),
        ("SQLite DB opens", check_sqlite_open),
        ("ChromaDB query works", check_chromadb_query),
        ("Gradio imports", check_gradio_import),
        ("knowledge base validates", check_kb_validation),
        ("offline P0 feature checks", check_offline_p0_features),
        ("optional Anthropic LLM call", check_optional_llm_call),
    ]
    failed = [name for name, func in checks if not run_check(name, func)]
    if failed:
        print(f"\nSmoke test failed: {', '.join(failed)}")
        return 1
    print("\nSmoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
