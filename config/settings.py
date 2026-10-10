import os
from dotenv import load_dotenv

# Load .env file from config folder
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Model assignments per agent
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL") or "claude-sonnet-5-5"
PLANNER_MODEL = os.getenv("PLANNER_MODEL") or "claude-sonnet-5-5"
RAG_MODEL = os.getenv("RAG_MODEL") or "claude-haiku-5-5"
SAFETY_MODEL = os.getenv("SAFETY_MODEL") or "claude-haiku-5-5"
ETIQUETTE_MODEL = os.getenv("ETIQUETTE_MODEL") or "claude-haiku-5-5"

# Other APIs (add as you get keys)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")
BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
USE_TOOL_AGENT = os.getenv("USE_TOOL_AGENT", "false").strip().lower() == "true"


def validate_config():
    missing = []
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    print("Config loaded successfully.")


if __name__ == "__main__":
    validate_config()
