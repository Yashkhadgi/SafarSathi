import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.llm_wrapper import call_llm
from config.settings import ORCHESTRATOR_MODEL

INTENT_CATEGORIES = ["planner", "info"]

def classify_intent(user_message: str) -> str:
    """
    Uses a cheap, fast LLM call to decide which specialist agent should handle the query.
    Returns one of: 'planner', 'info'
    """
    system_prompt = (
        "You are an intent classifier for a tourist assistant. "
        "Classify the user's message into exactly ONE of these categories:\n"
        "- 'planner' : if the user wants an itinerary, trip plan, schedule, or travel route\n"
        "- 'info' : if the user is asking about a place, monument, culture, food, or general tourist information\n\n"
        "Respond with ONLY the single word: planner OR info. No explanation, no punctuation."
    )

    result = call_llm(
        model=ORCHESTRATOR_MODEL,
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=10
    )

    result = result.strip().lower()

    if result not in INTENT_CATEGORIES:
        return "info"  # safe fallback

    return result


def route_query(user_message: str):
    """
    Orchestrator entry point: classifies intent, then calls the right agent.
    Returns (agent_name, response_text)
    """
    from agents.planner_agent import run_planner_agent
    from agents.rag_agent import run_rag_agent

    intent = classify_intent(user_message)

    if intent == "planner":
        response = run_planner_agent(user_message)
        return "Planner Agent", response
    else:
        response = run_rag_agent(user_message)
        return "Info/RAG Agent", response


if __name__ == "__main__":
    test_query = "Plan me a 3 day trip to Goa"
    agent, reply = route_query(test_query)
    print(f"Routed to: {agent}")
    print(f"Reply: {reply}")