"""Opt-in Claude tool loop for the travel assistant."""

import json
import logging
import re
import time
from pathlib import Path

from config.settings import ORCHESTRATOR_MODEL
from memory.session_memory import get_history
from tools.llm_wrapper import call_llm_with_tools, stream_llm_with_tools
from tools.registry import TOOL_SCHEMAS, execute_tool
from memory.profiles import profile_summary


LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "tool_calls.log"
LOG_PATH.parent.mkdir(exist_ok=True)
_logger = logging.getLogger("safarsathi.tool_calls")
if not _logger.handlers:
    handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    _logger.addHandler(handler)
_logger.setLevel(logging.INFO)

_SAFETY = re.compile(
    r"\b(emergency|robbed|stolen|lost wallet|lost passport|hospital|police|unsafe|"
    r"injured|help me|madad|chori|lut|gum gaya|kho gaya|khoya|police|aspatal|"
    r"bachao|ambulance)\b|मदद|चोरी|लूट|खो गया|अस्पताल|पुलिस|बचाओ",
    re.I,
)

SYSTEM = (
    "You are SafarSathi, a concise and grounded India travel companion. "
    "Keep textual responses short, crisp, and direct (2-3 sentences max). "
    "Handle emergency or unsafe signals FIRST: advise immediate safety and SOS/112 or 108. "
    "Never provide booking or payment links. Use tools for factual lookups and numbers. "
    "When a tool returns structured data, DO NOT duplicate entire lists or tables in plain text because "
    "rich interactive UI cards are automatically rendered in the interface. "
    "Summarize key insights briefly, cite facts inline [1][2], and always end with a concise next-step "
    "follow-up question (e.g., 'Would you like to check nearby hotels or return transit options?')."
)


def safety_signal(message):
    return bool(_SAFETY.search(message or ""))


def _conversation(session_id, message):
    history = get_history(session_id, max_turns=8)
    messages = []
    for role, content in history:
        if role not in ("user", "assistant"):
            continue
        if messages and messages[-1]["role"] == role:
            messages[-1]["content"] += "\n" + content
        else:
            messages.append({"role": role, "content": content})
    if not messages or messages[-1] != {"role": "user", "content": message}:
        messages.append({"role": "user", "content": message})
    return messages


def run_core_agent(session_id, message, max_iters=2):
    """Return {answer, tools_used, tool_results}; never raise."""
    try:
        messages = _conversation(session_id, message)
        summary = profile_summary(session_id.split(":", 1)[0])
        preferences = (" Traveler preferences: " + summary + ". Honor diet, allergies and mobility. "
                       if summary else "")
        priority = " The current user message signals danger. Start with safety instructions. " if safety_signal(message) else ""
        used, results = [], []
        deadline = time.monotonic() + 90
        for _ in range(max(1, min(int(max_iters), 3))):
            if time.monotonic() >= deadline:
                return {"answer": "Live assistance timed out. Please retry. For immediate danger call 112.",
                        "tools_used": used, "tool_results": results}
            result = call_llm_with_tools(
                ORCHESTRATOR_MODEL, SYSTEM + priority + preferences, messages, TOOL_SCHEMAS,
                max_iters=max_iters,
            )
            if "error" in result:
                prefix = "For immediate danger call 112. " if priority else ""
                return {"answer": prefix + result["error"], "tools_used": used,
                        "tool_results": results}
            response = result["response"]
            blocks = response.content
            tool_uses = [block for block in blocks if block.type == "tool_use"]
            if not tool_uses:
                answer = "\n".join(block.text for block in blocks if block.type == "text").strip()
                if priority and "112" not in answer:
                    answer = "For immediate danger, call 112.\n\n" + answer
                return {"answer": answer or "No answer was returned.",
                        "tools_used": used, "tool_results": results}
            messages.append({"role": "assistant", "content": [block.model_dump(exclude_none=True) for block in blocks]})
            tool_answers = []
            for block in tool_uses:
                started = time.monotonic()
                arguments = dict(block.input or {})
                if block.name in ("build_itinerary", "edit_itinerary"):
                    arguments["session_id"] = session_id
                tool_result = execute_tool(block.name, arguments)
                elapsed_ms = round((time.monotonic() - started) * 1000)
                _logger.info("tool=%s elapsed_ms=%s error=%s", block.name,
                             elapsed_ms, "error" in tool_result)
                used.append(block.name)
                results.append(tool_result)
                tool_answers.append({
                    "type": "tool_result", "tool_use_id": block.id,
                    "content": json.dumps(tool_result, ensure_ascii=False, default=str),
                })
            messages.append({"role": "user", "content": tool_answers})
        return {"answer": "I reached the tool limit. Please narrow the request and retry.",
                "tools_used": used, "tool_results": results}
    except Exception as exc:
        return {"answer": f"Assistant unavailable: {exc}", "tools_used": [],
                "tool_results": [{"error": str(exc)}]}


def stream_core_agent(session_id, message, max_iters=2):
    """Yield status and partial answers while keeping tool use bounded."""
    try:
        messages = _conversation(session_id, message)
        summary = profile_summary(session_id.split(":", 1)[0])
        preferences = (" Traveler preferences: " + summary + ". Honor diet, allergies and mobility. "
                       if summary else "")
        priority = " The current user message signals danger. Start with safety instructions. " if safety_signal(message) else ""
        used, results = [], []
        deadline = time.monotonic() + 90
        for _ in range(max(1, min(int(max_iters), 6))):
            if time.monotonic() >= deadline:
                yield {"done": True, "answer": "Live assistance timed out. Call 112 for immediate danger.",
                       "tools_used": used, "tool_results": results}
                return
            text_so_far = ""
            response = None
            for event in stream_llm_with_tools(
                ORCHESTRATOR_MODEL, SYSTEM + priority + preferences, messages, TOOL_SCHEMAS
            ):
                if "error" in event:
                    yield {"done": True, "answer": event["error"],
                           "tools_used": used, "tool_results": results}
                    return
                if "text" in event:
                    text_so_far += event["text"]
                    yield {"partial": text_so_far, "tools_used": used}
                if "response" in event:
                    response = event["response"]
            if response is None:
                yield {"done": True, "answer": "No answer was returned.",
                       "tools_used": used, "tool_results": results}
                return
            blocks = response.content
            tool_uses = [block for block in blocks if block.type == "tool_use"]
            if not tool_uses:
                answer = "\n".join(block.text for block in blocks if block.type == "text").strip()
                if priority and "112" not in answer:
                    answer = "For immediate danger, call 112.\n\n" + answer
                yield {"done": True, "answer": answer or "No answer was returned.",
                       "tools_used": used, "tool_results": results}
                return
            messages.append({"role": "assistant", "content": [block.model_dump(exclude_none=True) for block in blocks]})
            tool_answers = []
            for block in tool_uses:
                yield {"status": f"Checking {block.name.replace('_', ' ')}...", "tools_used": used}
                started = time.monotonic()
                arguments = dict(block.input or {})
                if block.name in ("build_itinerary", "edit_itinerary"):
                    arguments["session_id"] = session_id
                tool_result = execute_tool(block.name, arguments)
                _logger.info("tool=%s elapsed_ms=%s error=%s", block.name,
                             round((time.monotonic() - started) * 1000), "error" in tool_result)
                used.append(block.name)
                results.append(tool_result)

                # Extract UI card payload if available
                ui_card = None
                if isinstance(tool_result, dict):
                    if "ui" in tool_result and isinstance(tool_result["ui"], dict):
                        ui_card = tool_result["ui"]
                    elif "days" in tool_result and "destination" in tool_result and not tool_result.get("error"):
                        ui_card = {"type": "itinerary", "version": "1.0", "data": tool_result}
                    elif ("estimates" in tool_result or ("categories" in tool_result and "total_inr" in tool_result)) and not tool_result.get("error"):
                        ui_card = {"type": "budget", "version": "1.0", "data": tool_result}
                    elif ("emergency_numbers" in tool_result or "safety_tips" in tool_result) and not tool_result.get("error"):
                        ui_card = {"type": "sos", "version": "1.0", "data": tool_result}

                if ui_card:
                    yield {"ui_card": ui_card, "tools_used": used}

                tool_answers.append({"type": "tool_result", "tool_use_id": block.id,
                                     "content": json.dumps(tool_result, ensure_ascii=False, default=str)})
            messages.append({"role": "user", "content": tool_answers})
        yield {"done": True, "answer": "I reached the tool limit. Please narrow the request.",
               "tools_used": used, "tool_results": results}
    except Exception as exc:
        yield {"done": True, "answer": f"Assistant unavailable: {exc}",
               "tools_used": [], "tool_results": [{"error": str(exc)}]}
