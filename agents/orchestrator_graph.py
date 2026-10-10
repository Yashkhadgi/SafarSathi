import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

from tools.llm_wrapper import call_llm
from config.settings import ORCHESTRATOR_MODEL, USE_TOOL_AGENT
from agents.planner_agent import run_planner_agent
from agents.rag_agent import run_rag_agent
from agents.safety_agent import run_safety_agent
from agents.etiquette_agent import run_etiquette_agent
from memory.session_memory import save_turn, format_history
from agents.guardrails import post_process_answer
from agents.rag_agent import retrieve
from agents.scam_alerts import auto_attach_scam_alerts
from agents.language_agent import run_language_pipeline
from memory.language_preferences import get_session_preferences, save_session_preferences
from memory.profiles import profile_summary, save_from_chat


def _history_with_profile(session_id):
    user_id = session_id.split(":", 1)[0]
    summary = profile_summary(user_id)
    history = format_history(session_id)
    return (f"Traveler preferences: {summary}. Honor diet, allergies and mobility.\n" if summary else "") + history


# Define the shared state that flows through the graph
class AgentState(TypedDict):
    session_id: str
    user_message: str
    intent: str
    agent_used: str
    response: str


# Node 1: Classify intent
def classify_node(state: AgentState) -> AgentState:
    system_prompt = (
        "You are an intent classifier for a tourist assistant. "
        "Classify the user's message into exactly ONE of these categories:\n"
        "- 'planner' : if the user wants an itinerary, trip plan, schedule, day-wise plan, travel route, "
        "or mentions accommodation/budget/food/travel FOR a trip. "
        "This includes requests like 'plan a trip', 'X days in Y', 'help me visit places'.\n"
        "- 'info' : ONLY if the user is asking a standalone factual question about a place, monument, culture, "
        "or food, with NO request to plan/organize a trip.\n"
        "- 'safety' : if the user describes an emergency, feels unsafe, is lost, injured, robbed, "
        "needs a hospital/police, or asks for emergency help.\n"
        "- 'etiquette' : if the user asks about local customs, dress code, manners, what's respectful "
        "or disrespectful, tipping norms, greetings, temple/religious etiquette.\n\n"
        "If the message describes real distress or an emergency, classify as 'safety' regardless of any other "
        "planning/info content in the same message — safety always takes top priority.\n\n"
        "Real user queries often contain typos and run-on phrasing (e.g. 'acomodation', 'planing', 'everythng') — "
        "do not be thrown off by that. "
        "If a message asks for BOTH info about a place AND a plan/itinerary/budget/route, classify as 'planner' (planning intent wins). "
        "When genuinely ambiguous, default to 'planner'.\n\n"
        "Respond with ONLY one word: planner OR info OR safety OR etiquette. No explanation, no punctuation."
    )
    result = call_llm(
        model=ORCHESTRATOR_MODEL,
        system_prompt=system_prompt,
        user_message=state["user_message"],
        max_tokens=10
    )
    intent = result.strip().lower()
    if intent not in ["planner", "info", "safety", "etiquette"]:
        intent = "planner"

    state["intent"] = intent
    return state


# Node 2: Planner agent
def planner_node(state: AgentState) -> AgentState:
    history = _history_with_profile(state["session_id"])
    state["response"] = run_planner_agent(state["user_message"], history=history)
    state["agent_used"] = "Planner Agent"
    return state


# Node 3: RAG/Info agent
def rag_node(state: AgentState) -> AgentState:
    history = _history_with_profile(state["session_id"])
    state["response"] = run_rag_agent(state["user_message"], history=history)
    state["agent_used"] = "Info/RAG Agent"
    return state


# Node 4: Safety/Emergency agent
def safety_node(state: AgentState) -> AgentState:
    history = _history_with_profile(state["session_id"])
    state["response"] = run_safety_agent(state["user_message"], history=history)
    state["agent_used"] = "Safety Agent"
    return state


# Node 5: Cultural Etiquette agent
def etiquette_node(state: AgentState) -> AgentState:
    history = _history_with_profile(state["session_id"])
    state["response"] = run_etiquette_agent(state["user_message"], history=history)
    state["agent_used"] = "Etiquette Agent"
    return state


# Conditional routing function — decides which node runs next
def route_decision(state: AgentState) -> Literal["planner", "info", "safety", "etiquette"]:
    return state["intent"]


# Build the graph
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("classify", classify_node)
    graph.add_node("planner", planner_node)
    graph.add_node("info", rag_node)
    graph.add_node("safety", safety_node)
    graph.add_node("etiquette", etiquette_node)

    graph.set_entry_point("classify")

    graph.add_conditional_edges(
        "classify",
        route_decision,
        {
            "planner": "planner",
            "info": "info",
            "safety": "safety",
            "etiquette": "etiquette",
        }
    )

    graph.add_edge("planner", END)
    graph.add_edge("info", END)
    graph.add_edge("safety", END)
    graph.add_edge("etiquette", END)

    return graph.compile()


# Compiled app — import this in ui/app.py
tourist_agent_graph = build_graph()


def _run_core_agent(session_id: str, user_message: str):
    initial_state = {
        "session_id": session_id,
        "user_message": user_message,
        "intent": "",
        "agent_used": "",
        "response": ""
    }
    final_state = tourist_agent_graph.invoke(initial_state)

    context = ""
    if final_state.get("intent") == "info":
        try:
            context = "\n\n".join(
                record["text"]
                for record in retrieve(user_message).get("records", [])
                if record.get("text")
            )
        except Exception:
            context = ""

    final_state["response"] = post_process_answer(
        final_state["response"], user_message=user_message, context=context
    )
    final_state["response"] = auto_attach_scam_alerts(
        final_state["response"], user_message=user_message
    )
    return final_state["agent_used"], final_state["response"]


def run_agent(session_id: str, user_message: str, language_override=None, show_english=None):
    preferences = get_session_preferences(session_id)
    language_override = language_override or preferences["language_code"]
    show_english = preferences["show_english"] if show_english is None else bool(show_english)
    save_turn(session_id, "user", user_message)
    save_from_chat(session_id.split(":", 1)[0], user_message)

    agent_used = "Tourist Assistant"
    def core_agent(normalized_message):
        nonlocal agent_used
        if USE_TOOL_AGENT:
            from agents.core_agent import run_core_agent

            result = run_core_agent(session_id, normalized_message)
            agent_used = "Tool Agent"
            response = post_process_answer(
                result["answer"], user_message=normalized_message,
                tool_results=result["tool_results"],
            )
            response = auto_attach_scam_alerts(response, user_message=normalized_message)
            tools_used = list(dict.fromkeys(result["tools_used"]))
            return response + ("\n\nUsed: " + ", ".join(tools_used) if tools_used else "")
        agent_used, response = _run_core_agent(session_id, normalized_message)
        return response

    response, language = run_language_pipeline(
        user_message,
        core_agent,
        preference=language_override,
        show_english=show_english,
        previous_language=preferences["detected_language"],
    )
    save_session_preferences(
        session_id,
        language_code=preferences["language_code"] if language_override is None else language_override,
        detected_language=language,
        show_english=show_english,
    )
    save_turn(session_id, "assistant", response)
    return agent_used, response


if __name__ == "__main__":
    agent, reply = run_agent("test-session", "Plan a 3 day trip to Udaipur")
    print(f"Agent used: {agent}")
    print(f"Reply: {reply}")
