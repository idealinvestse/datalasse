"""pytest unit tests for DevinClient (MOCK primary, no real net)."""

import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # workspace root
sys.path.insert(0, str(Path(__file__).parent.parent))  # devin/

import pytest

os.environ.setdefault("MOCK", "1")

from lib.devin_client import DevinClient


def test_init_env_and_mock(monkeypatch, tmp_path):
    monkeypatch.setenv("DEVIN_API_KEY", "cog_testkey123456")
    monkeypatch.setenv("DEVIN_ORG_ID", "org-test123")
    monkeypatch.setenv("MOCK", "1")
    c = DevinClient()
    assert c.dry_run is True
    assert "cog_test" in c.api_key
    assert c.org_id == "org-test123"


def test_create_session_payload_and_mock():
    c = DevinClient(dry_run=True)
    data = c.create_session("fix auth", max_acu_limit=5, tags=["bug"])
    assert data["session_id"].startswith("devin-mock-")
    assert data["max_acu_limit"] == 5
    assert data["status"] == "new"


def test_get_session_mock():
    c = DevinClient(dry_run=True)
    s = c.get_session("devin-xyz")
    assert s["session_id"] == "devin-xyz"
    assert s["status"] == "exit"


def test_create_cost_safety_raises():
    c = DevinClient(dry_run=True)
    with pytest.raises(ValueError) as exc:
        c.create_session("big task", max_acu_limit=60)
    assert "50" in str(exc.value) or "requires --yes" in str(exc.value)


def test_send_message_mock():
    c = DevinClient(dry_run=True)
    # should not raise
    c.send_message("sid", "update?")


def test_list_and_kill_mock():
    c = DevinClient(dry_run=True)
    lst = c.list_sessions(5)
    assert isinstance(lst, list)
    assert c.kill_session("any") is True


def test_wait_for_completion_stops_on_terminal():
    c = DevinClient(dry_run=True)
    final = c.wait_for_completion("sid", poll_interval=1, max_wait=5)
    assert final["status"] in ("exit", "error", "suspended")


def test_estimate_cost():
    c = DevinClient(dry_run=True)
    assert "22.50" in c.estimate_cost(10)
    assert "ACUs" in c.estimate_cost(10)


@patch("skills.devin.lib.devin_client.requests.Session")
def test_upload_multipart_format(mock_session_cls, tmp_path):
    # ensure no real net even if mock off
    f = tmp_path / "t.txt"
    f.write_text("hello")
    c = DevinClient(dry_run=True, api_key="cog_xxx")
    res = c.upload_attachment(None, str(f))
    assert "url" in res or res.get("mock") is True


def test_health_check_mock():
    c = DevinClient(dry_run=True)
    assert c.health_check() is True