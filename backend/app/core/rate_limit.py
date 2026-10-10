"""In-memory rate limiter and lockout tracking for auth endpoints."""

import time
from typing import Dict, Tuple

# Key -> [(timestamp)]
_REQUEST_HISTORY: Dict[str, list] = {}
# IP/Email -> lockout_until_timestamp
_LOCKOUTS: Dict[str, float] = {}


def check_rate_limit(key: str, max_requests: int = 10, window_seconds: int = 60) -> Tuple[bool, int]:
    """Check if a request under `key` exceeds max_requests within window_seconds.

    Returns (is_allowed, retry_after_seconds).
    """
    now = time.time()
    
    # Check lockout
    if key in _LOCKOUTS:
        if now < _LOCKOUTS[key]:
            return False, int(_LOCKOUTS[key] - now)
        else:
            del _LOCKOUTS[key]

    history = _REQUEST_HISTORY.get(key, [])
    # Filter out requests older than window
    valid_history = [t for t in history if now - t < window_seconds]
    
    if len(valid_history) >= max_requests:
        retry_after = int(window_seconds - (now - valid_history[0]))
        return False, max(1, retry_after)

    valid_history.append(now)
    _REQUEST_HISTORY[key] = valid_history
    return True, 0


def record_failed_attempt(key: str, max_failures: int = 5, lockout_seconds: int = 300) -> bool:
    """Record a failed auth attempt. If max_failures reached, trigger a temporary lockout."""
    now = time.time()
    history = _REQUEST_HISTORY.get(f"fail_{key}", [])
    valid_history = [t for t in history if now - t < lockout_seconds]
    valid_history.append(now)
    _REQUEST_HISTORY[f"fail_{key}"] = valid_history

    if len(valid_history) >= max_failures:
        _LOCKOUTS[key] = now + lockout_seconds
        return True  # Is locked out
    return False


def clear_failed_attempts(key: str):
    """Clear failed attempt history on successful login."""
    _REQUEST_HISTORY.pop(f"fail_{key}", None)
    _LOCKOUTS.pop(key, None)


def reset_rate_limits():
    """Reset all rate limit and lockout state (used in test suites)."""
    _REQUEST_HISTORY.clear()
    _LOCKOUTS.clear()
