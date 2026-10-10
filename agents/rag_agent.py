import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from tools.llm_wrapper import call_llm
from config.settings import RAG_MODEL

EMBEDDINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "embeddings")

_client = chromadb.PersistentClient(path=EMBEDDINGS_PATH)
_collection = _client.get_or_create_collection(name="tourist_kb")


def retrieve_context(query: str, n_results: int = 3) -> str:
    results = _collection.query(query_texts=[query], n_results=n_results)
    docs = results.get("documents", [[]])[0]
    if not docs:
        return ""
    return "\n\n".join(f"- {d}" for d in docs)


def run_rag_agent(user_message: str, history: str = "") -> str:
    context = retrieve_context(user_message)

    if context:
        system_prompt = (
            "You are the Local Info Agent of a multilingual tourist assistant. "
            "Answer the user's question using ONLY the context below when it's relevant. "
            "If the context doesn't cover the question, answer from general knowledge but say so briefly. "
            "Respond in the same language/style the user used. Keep answers concise and factual.\n\n"
            f"CONTEXT:\n{context}"
            + (f"\n\nRecent conversation:\n{history}" if history else "")
        )
    else:
        system_prompt = (
            "You are the Local Info Agent of a multilingual tourist assistant. "
            "No local knowledge base match was found for this query — answer from general knowledge, "
            "and mention that this is general knowledge, not verified local data. "
            "Respond in the same language/style the user used. Keep answers concise."
            + (f"\n\nRecent conversation:\n{history}" if history else "")
        )

    return call_llm(model=RAG_MODEL, system_prompt=system_prompt, user_message=user_message, max_tokens=800)


if __name__ == "__main__":
    print(run_rag_agent("Tell me about Hawa Mahal"))
