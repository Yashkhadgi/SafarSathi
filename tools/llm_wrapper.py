import sys
import os

# Add project root to path so 'config' module is found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from config.settings import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def call_llm(model: str, system_prompt: str, user_message: str, max_tokens: int = 500):
    """
    Universal wrapper to call Claude models.
    Change 'model' param per agent (Sonnet for orchestrator/planner, Haiku for the rest).
    """
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"LLM call failed: {e}")
        return "Sorry, something went wrong while processing your request."


if __name__ == "__main__":
    from config.settings import ORCHESTRATOR_MODEL
    reply = call_llm(
        model=ORCHESTRATOR_MODEL,
        system_prompt="You are a helpful tourist assistant.",
        user_message="Hi, who are you?"
    )
    print(reply)
