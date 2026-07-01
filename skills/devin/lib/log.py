"""Simple mode-aware logger for devin skill.

Writes to stderr + appends to memory/devin/devin.log (ISO timestamps).
Never logs raw API keys (callers must mask).
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path


LOG_DIR = Path.home() / ".openclaw" / "workspace" / "memory" / "devin"
LOG_FILE = LOG_DIR / "devin.log"


def _ensure_log_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _mask_if_key(text: str) -> str:
    # Best-effort: if looks like cog_ key, mask middle
    import re
    def repl(m):
        k = m.group(0)
        if len(k) > 8:
            return k[:4] + "****" + k[-4:]
        return k[:2] + "****"
    return re.sub(r'cog_[A-Za-z0-9_-]{6,}', repl, text)


def log(msg: str, level: str = "INFO", session_id: str | None = None) -> None:
    """Log with [ISO] [LEVEL] prefix. Respects MOCK prefix. Always masks keys."""
    _ensure_log_dir()
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    prefix = "[MOCK] " if os.getenv("MOCK") else ""
    sid_part = f" [{session_id}]" if session_id else ""
    line = f"{prefix}[{ts}] [{level}]{sid_part} {msg}"
    safe_line = _mask_if_key(line)

    # stderr always
    print(safe_line, file=sys.stderr)

    # append to log (ignore errors)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(safe_line + "\n")
    except Exception:
        pass