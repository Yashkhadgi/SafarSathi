import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chromadb

from scripts.validate_kb import load_records, validate_records


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "knowledge_base"
EMBEDDINGS_PATH = PROJECT_ROOT / "data" / "embeddings"


def build():
    records, load_errors = load_records(DATA_PATH)
    errors = load_errors + validate_records(records)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return False
    if not records:
        print(f"ERROR: no KB records found in {DATA_PATH}")
        return False

    client = chromadb.PersistentClient(path=str(EMBEDDINGS_PATH))
    collection = client.get_or_create_collection(name="tourist_kb")
    collection.upsert(
        ids=[record["id"] for record in records],
        documents=[record["text"] for record in records],
        metadatas=[
            {
                "place": record["place"],
                "state": record["state"],
                "category": record["category"],
                "source_name": record["source_name"],
                "source_url": record["source_url"],
                "last_verified": record["last_verified"],
                "language": record["language"],
                "tags": ",".join(record["tags"]),
            }
            for record in records
        ],
    )
    print(f"Upserted {len(records)} documents into ChromaDB collection 'tourist_kb'.")
    return True


if __name__ == "__main__":
    try:
        raise SystemExit(0 if build() else 1)
    except Exception as exc:
        print(f"ERROR: knowledge base build failed: {exc}")
        raise SystemExit(1)
