import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chromadb

from config.settings import ANTHROPIC_API_KEY, RAG_MODEL


EMBEDDINGS_PATH = str(Path(__file__).resolve().parents[1] / "data" / "embeddings")
MAX_DISTANCE = 1.5
TOP_K = 5

_client = chromadb.PersistentClient(path=EMBEDDINGS_PATH)
_collection = _client.get_or_create_collection(name="tourist_kb")


def _normalize_query(query):
    """Translate the query to English for embedding search, preserving names."""
    if not query or not ANTHROPIC_API_KEY:
        return query
    try:
        from tools.llm_wrapper import call_llm

        normalized = call_llm(
            model=RAG_MODEL,
            system_prompt=(
                "Convert the user's travel question to concise English for search. "
                "Preserve proper names and place names. If it is already English, "
                "return it unchanged. Return only the normalized query."
            ),
            user_message=query,
            max_tokens=80,
        )
        normalized = normalized.strip()
        if normalized and not normalized.lower().startswith("sorry,"):
            return normalized
    except Exception:
        pass
    return query


def _retrieve_uncached(query, n_results=TOP_K, place=None, category=None):
    """Return matching records with source metadata and a normalized relevance score."""
    if not isinstance(query, str) or not query.strip():
        return {"records": [], "grounded": False}
    try:
        count = _collection.count()
        if not count:
            return {"records": [], "grounded": False}
        filters = []
        if place:
            filters.append({"place": {"$eq": place}})
        if category:
            filters.append({"category": {"$eq": category}})
        where = None
        if len(filters) == 1:
            where = filters[0]
        elif filters:
            where = {"$and": filters}
        results = _collection.query(
            query_texts=[_normalize_query(query)],
            n_results=max(1, min(int(n_results), TOP_K)),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        return {"records": [], "grounded": False}

    documents = results.get("documents", [[]])[0] or []
    metadatas = results.get("metadatas", [[]])[0] or []
    distances = results.get("distances", [[]])[0] or []
    records = []
    for text, metadata, distance in zip(documents, metadatas, distances):
        if distance is None or float(distance) > MAX_DISTANCE:
            continue
        metadata = metadata or {}
        distance = float(distance)
        records.append(
            {
                "text": text,
                "source_name": metadata.get("source_name", ""),
                "source_url": metadata.get("source_url", ""),
                "last_verified": metadata.get("last_verified", ""),
                "score": round(1.0 / (1.0 + max(0.0, distance)), 4),
                "place": metadata.get("place", ""),
                "category": metadata.get("category", ""),
            }
        )
    grounded = any(
        record["source_name"] and record["source_url"] and record["last_verified"]
        for record in records
    )
    return {"records": records, "grounded": grounded}


def retrieve(query, n_results=TOP_K, place=None, category=None):
    from memory.cache import cached_call

    return cached_call(
        "knowledge_base", [query, n_results, place, category], 6 * 3600,
        lambda: _retrieve_uncached(query, n_results, place, category),
    )


def retrieve_context(query, n_results=TOP_K, place=None, category=None):
    """Compatibility helper that returns only the retrieved record list."""
    return retrieve(query, n_results=n_results, place=place, category=category)["records"]


def _generate_answer(user_message, context, history):
    sources = [
        record for record in context
        if record["source_name"] and record["source_url"] and record["last_verified"]
    ]
    grounded = bool(sources)
    if grounded:
        numbered = "\n\n".join(
            f"[{index}] {record['text']}\n"
            f"Source: {record['source_name']} ({record['source_url']}); "
            f"last verified {record['last_verified']}"
            for index, record in enumerate(sources, start=1)
        )
        system_prompt = (
            "You are a multilingual local information assistant. Answer only with facts supported "
            "by the numbered evidence. Add inline citations like [1] immediately after each "
            "supported factual claim. Do not use uncited facts. Answer in the user's language. "
            "If the evidence does not answer the question, say so briefly.\n\n"
            f"EVIDENCE:\n{numbered}"
        )
        fallback = f"{sources[0]['text']} [1]"
    else:
        system_prompt = (
            "You are a multilingual travel assistant. No source-verified knowledge-base evidence "
            "passed the relevance threshold. Answer as general knowledge, clearly label it as "
            "general knowledge, do not invent sources, and answer in the user's language."
        )
        fallback = "I couldn't find a verified answer in the local knowledge base. This is general knowledge."

    if history:
        system_prompt += f"\n\nRecent conversation:\n{history}"
    try:
        from tools.llm_wrapper import call_llm

        answer = call_llm(
            model=RAG_MODEL,
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=800,
        )
    except Exception:
        answer = fallback
    if not isinstance(answer, str) or not answer.strip() or answer.startswith("Sorry, something went wrong"):
        answer = fallback

    if grounded:
        if not re.search(r"\[\d+\]", answer):
            answer = f"{answer.rstrip()} [1]"
        answer = re.sub(
            r"\[(\d+)\]",
            lambda match: match.group(0)
            if 1 <= int(match.group(1)) <= len(sources)
            else "[1]",
            answer,
        )
        source_list = "\n".join(
            f"[{index}] {record['source_name']} - {record['source_url']} "
            f"(last verified: {record['last_verified']})"
            for index, record in enumerate(sources, start=1)
        )
        answer = f"{answer.strip()}\n\nSources:\n{source_list}"
    else:
        answer = f"{answer.strip()}\n\nSources: None (general knowledge; no verified KB source matched.)"
    return answer


def run_rag_agent(user_message, history="", place=None, category=None):
    try:
        result = retrieve(user_message, place=place, category=category)
        return _generate_answer(user_message, result["records"], history)
    except Exception:
        return "I couldn't retrieve verified local information. This is general knowledge.\n\nSources: None."


if __name__ == "__main__":
    print(run_rag_agent("Tell me about Hawa Mahal"))
