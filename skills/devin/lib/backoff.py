"""Exponential backoff and transient error classification for DevinClient.

Inspired by skills/deep-research/lib/retry.sh patterns.
"""

import time
import random
from typing import Callable, Any


def is_transient_error(status_code: int | None = None, text: str = "", exception: Exception | None = None) -> bool:
    """Return True for errors we should retry (429, 5xx, network/timeout).

    Never retry 4xx auth/bad-request (401,403,400,404 etc).
    """
    if status_code is not None:
        if status_code == 429:
            return True
        if 500 <= status_code < 600:
            return True
        if status_code < 500 and status_code != 429:
            return False

    text_lower = (text or "").lower()
    transient_patterns = (
        "timeout", "timed out", "rate limit", "too many requests",
        "429", "503", "502", "504", "service unavailable",
        "connection reset", "connection refused", "network", "temporary"
    )
    if any(p in text_lower for p in transient_patterns):
        return True

    if exception is not None:
        exc_str = str(exception).lower()
        if any(p in exc_str for p in ("timeout", "connection", "network")):
            return True

    return False


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    func: Callable[..., Any] | None = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Call func with retries on transient errors. Returns func result.

    If called as decorator style without func, use as wrapper.
    """
    if func is None:
        # allow @retry style or direct pass later; simple direct call usage in client
        def decorator(f):
            def wrapper(*a, **k):
                return retry_with_backoff(max_attempts, base_delay, max_delay, f, *a, **k)
            return wrapper
        return decorator

    attempt = 0
    last_exc = None
    delay = base_delay

    while attempt < max_attempts:
        attempt += 1
        try:
            return func(*args, **kwargs)
        except Exception as exc:  # requests exceptions + HTTPError etc
            last_exc = exc
            status = getattr(exc, 'response', None)
            status_code = status.status_code if status is not None else None
            text = ""
            if status is not None:
                try:
                    text = status.text
                except Exception:
                    text = str(exc)

            if not is_transient_error(status_code, text, exc):
                raise

            if attempt >= max_attempts:
                raise

            jitter = random.uniform(0, 0.3) * delay
            sleep_for = min(delay + jitter, max_delay)
            time.sleep(sleep_for)
            delay = min(delay * 1.5, max_delay)

    if last_exc:
        raise last_exc
    raise RuntimeError("retry_with_backoff exhausted without result")