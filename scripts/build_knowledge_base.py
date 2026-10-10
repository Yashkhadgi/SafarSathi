import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "knowledge_base", "destinations.json")
EMBEDDINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "embeddings")


def build():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)

    client = chromadb.PersistentClient(path=EMBEDDINGS_PATH)
    collection = client.get_or_create_collection(name="tourist_kb")

    collection.upsert(
        ids=[r["id"] for r in records],
        documents=[r["text"] for r in records],
        metadatas=[{"place": r["place"], "category": r["category"]} for r in records],
    )
    print(f"Ingested {len(records)} documents into ChromaDB collection 'tourist_kb'.")


if __name__ == "__main__":
    build()
