import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.llm_wrapper import call_llm
from config.settings import ETIQUETTE_MODEL


def run_etiquette_agent(user_message: str, history: str = "") -> str:
    system_prompt = (
        "You are the Cultural Etiquette Agent of a multilingual tourist assistant. "
        "You provide clear, practical cultural guidance for tourists visiting India. "
        "Cover: dress code, temple/religious etiquette (footwear, head covering, photography rules), "
        "greetings (namaste, when to bow, handshakes), tipping norms, do's and don'ts, "
        "what behaviours are considered rude or respectful in the local context. "
        "If a specific place or religious site is mentioned, tailor your guidance accordingly. "
        "Keep responses concise, structured, and non-judgmental. "
        "Respond in the same language/style the user used.\n\n"
        + (f"Recent conversation:\n{history}\n\n" if history else "")
    )
    return call_llm(
        model=ETIQUETTE_MODEL,
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=600,
    )


if __name__ == "__main__":
    print(run_etiquette_agent(
        "what should I wear visiting a temple in Varanasi, is it rude to point my feet at someone"
    ))
