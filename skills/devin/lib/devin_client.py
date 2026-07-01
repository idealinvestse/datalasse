"""DevinClient for Cognition Devin.ai v3 API.

Production-ready: retries, cost safety defaults, MOCK=1, key masking,
type hints, logging (truncated prompts only).
"""

import os
import time
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Iterator, Callable, List

import requests

from .backoff import retry_with_backoff, is_transient_error
from .log import log


class DevinClient:
    """Python client for Devin API v3 (org-scoped REST).

    Credentials resolution order (per instance):
      1. explicit args
      2. env vars (DEVIN_*)
      3. ~/.config/devin/devin.env (KEY=val or export KEY=val)
    """

    DEFAULT_BASE = "https://api.devin.ai/v3"
    DEFAULT_MAX_ACU = 10
    HARD_MAX_ACU = 500

    def __init__(
        self,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        dry_run: bool = False,
    ) -> None:
        self.api_key = api_key or os.getenv("DEVIN_API_KEY") or self._load_from_config_file("DEVIN_API_KEY")
        self.org_id = org_id or os.getenv("DEVIN_ORG_ID") or self._load_from_config_file("DEVIN_ORG_ID")
        raw_base = base_url or os.getenv("DEVIN_BASE_URL") or self.DEFAULT_BASE
        self.base_url = raw_base.rstrip("/")
        self.timeout = int(os.getenv("DEVIN_TIMEOUT", timeout))
        self.dry_run = bool(dry_run or os.getenv("MOCK") or os.getenv("DEVIN_DRY_RUN"))

        self._session = requests.Session()
        if self.api_key:
            self._session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    # --- credential helpers ---

    def _load_from_config_file(self, key: str) -> Optional[str]:
        p = Path.home() / ".config" / "devin" / "devin.env"
        if not p.exists():
            return None
        try:
            for raw in p.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[len("export "):].strip()
                if "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k == key:
                    return v
        except Exception:
            pass
        return None

    def _mask(self, key: Optional[str]) -> str:
        if not key:
            return ""
        if len(key) <= 8:
            return key[:2] + "****"
        return key[:4] + "****" + key[-4:]

    # --- internal request with retry + mock ---

    def _mock_response(self, method: str, path: str, kw: Dict[str, Any]) -> Any:
        """Return a fake requests.Response-like for dry_run/MOCK."""
        class _MockResp:
            def __init__(self, data: Dict[str, Any], status: int = 200):
                self._data = data
                self.status_code = status
                self.text = json.dumps(data)
            def json(self) -> Dict[str, Any]:
                return self._data
            def raise_for_status(self) -> None:
                if self.status_code >= 400:
                    raise requests.HTTPError(f"Mock HTTP {self.status_code}")

        if method == "POST" and path == "/sessions":
            sid = f"devin-mock-{int(time.time()*1000) % 1000000}"
            payload = kw.get("json", {})
            return _MockResp({
                "session_id": sid,
                "status": "new",
                "url": f"https://app.devin.ai/sessions/{sid}",
                "max_acu_limit": payload.get("max_acu_limit", self.DEFAULT_MAX_ACU),
                "acus_consumed": 0,
                "tags": payload.get("tags", []),
            })
        if method == "GET" and path.startswith("/sessions/") and path != "/sessions":
            sid = path.split("/")[-1]
            return _MockResp({
                "session_id": sid,
                "status": "exit",
                "acus_consumed": 7,
                "structured_output": {"result": "Mock task complete"},
                "urls": {"web": f"https://app.devin.ai/sessions/{sid}"},
                "pull_requests": [],
                "messages": [{"role": "assistant", "content": "Done."}],
            })
        if method == "GET" and path == "/sessions":
            return _MockResp({"sessions": [{"session_id": "devin-mock-list1", "status": "exit"}]})
        if method == "POST" and "/messages" in path:
            return _MockResp({})
        if method == "DELETE" and "/sessions/" in path:
            return _MockResp({}, status=204)
        if method == "POST" and path == "/attachments":
            return _MockResp({"url": "https://attachments.devin.ai/mock/123/f.txt", "filename": "mock"})
        # default success
        return _MockResp({"ok": True, "mock": True})

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        if self.dry_run:
            log(f"[MOCK] {method} {path}", "INFO")
            return self._mock_response(method, path, kwargs)  # type: ignore

        url = f"{self.base_url}/organizations/{self.org_id}{path}"

        def _do() -> requests.Response:
            if "files" in kwargs:
                # multipart: requests will set proper content-type boundary
                headers = {"Authorization": f"Bearer {self.api_key}"}
                r = self._session.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
            else:
                hdrs = kwargs.setdefault("headers", {})
                if "json" in kwargs and "Content-Type" not in hdrs:
                    hdrs["Content-Type"] = "application/json"
                r = self._session.request(method, url, timeout=self.timeout, **kwargs)

            if r.status_code == 429:
                ra = r.headers.get("Retry-After")
                if ra:
                    try:
                        time.sleep(min(int(ra), 30))
                    except Exception:
                        time.sleep(5)
            r.raise_for_status()
            return r

        # wrap with retry logic (3 attempts)
        return retry_with_backoff(3, 1.0, 30.0, _do)

    # --- public API ---

    def create_session(
        self,
        prompt: str,
        max_acu_limit: int = DEFAULT_MAX_ACU,
        *,
        tags: Optional[List[str]] = None,
        repos: Optional[List[str]] = None,
        secrets: Optional[List[Dict[str, Any]]] = None,
        structured_output_schema: Optional[Dict[str, Any]] = None,
        devin_mode: str = "normal",
        playbook_id: Optional[str] = None,
        yes: bool = False,
        **extra: Any,
    ) -> Dict[str, Any]:
        if max_acu_limit > 50 and not yes:
            raise ValueError(
                f"max_acu_limit={max_acu_limit} > 50 requires --yes (cost safety). "
                f"Estimated cost: {self.estimate_cost(max_acu_limit)}"
            )
        if max_acu_limit > self.HARD_MAX_ACU:
            raise ValueError(f"Hard safety limit exceeded: max_acu_limit > {self.HARD_MAX_ACU}")

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "max_acu_limit": max_acu_limit,
            "devin_mode": devin_mode,
        }
        if tags:
            payload["tags"] = tags
        if repos:
            payload["repos"] = repos
        if secrets:
            payload["session_secrets"] = secrets
        if structured_output_schema:
            payload["structured_output_schema"] = structured_output_schema
        if playbook_id:
            payload["playbook_id"] = playbook_id
        payload.update(extra)

        log(f"create prompt={prompt[:80]!r}... max_acu={max_acu_limit} mode={devin_mode}", "INFO")

        resp = self._request("POST", "/sessions", json=payload)
        data = resp.json()
        sid = data.get("session_id")
        log(f"created session_id={sid}", "INFO")
        return data

    def get_session(self, session_id: str) -> Dict[str, Any]:
        resp = self._request("GET", f"/sessions/{session_id}")
        return resp.json()

    def send_message(self, session_id: str, message: str) -> None:
        self._request("POST", f"/sessions/{session_id}/messages", json={"message": message})

    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        resp = self._request("GET", "/sessions", params={"limit": min(limit, 100)})
        data = resp.json()
        sessions = data if isinstance(data, list) else data.get("sessions", data) or []
        return list(sessions)[:limit]

    def kill_session(self, session_id: str) -> bool:
        try:
            r = self._request("DELETE", f"/sessions/{session_id}")
            return r.status_code < 300
        except requests.HTTPError as e:
            if getattr(e, "response", None) and e.response.status_code == 404:
                return True
            raise

    def upload_attachment(self, session_id: Optional[str], file_path: str) -> Dict[str, Any]:
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(file_path)
        with p.open("rb") as fh:
            files = {"file": (p.name, fh)}
            resp = self._request("POST", "/attachments", files=files)
        return resp.json()

    def wait_for_completion(
        self,
        session_id: str,
        poll_interval: int = 10,
        max_wait: int = 3600,
        on_status: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        start = time.time()
        backoff = float(poll_interval)
        while time.time() - start < max_wait:
            s = self.get_session(session_id)
            st = s.get("status", "")
            if on_status:
                try:
                    on_status(st, s)
                except Exception:
                    pass
            if st in ("exit", "error", "suspended"):
                log(f"session {session_id} terminal status={st} acu={s.get('acus_consumed')}", "INFO")
                return s
            time.sleep(min(backoff, 30.0))
            backoff = min(backoff * 1.5, 30.0)
        raise TimeoutError(f"Session {session_id} did not complete within {max_wait}s")

    def get_message_stream(self, session_id: str) -> Iterator[Dict[str, Any]]:
        seen = 0
        while True:
            s = self.get_session(session_id)
            msgs: List[Dict[str, Any]] = s.get("messages", []) or []
            for m in msgs[seen:]:
                yield m
            seen = len(msgs)
            if s.get("status") in ("exit", "error", "suspended"):
                break
            time.sleep(5)

    def estimate_cost(self, max_acu: int) -> str:
        usd = max_acu * 2.25
        return f"~${usd:.2f} ({max_acu} ACUs @ $2.25)"

    def health_check(self) -> bool:
        """Lightweight check used by doctor (list or profile)."""
        try:
            _ = self.list_sessions(limit=1)
            return True
        except Exception:
            return False