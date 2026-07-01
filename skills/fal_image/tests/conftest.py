"""pytest fixtures for fal_image tests (MOCK=1 / FAL_MOCK=1 friendly)."""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Make workspace importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

os.environ.setdefault("MOCK", "1")
os.environ.setdefault("FAL_MOCK", "1")

FAKE_RESULT = {
    "images": [
        {
            "url": "https://fal.media/mock-output.png",
            "width": 1024,
            "height": 576,
            "content_type": "image/png",
        }
    ]
}


@pytest.fixture(autouse=True)
def mock_fal_client():
    """Patch fal_client at the client module level for all tests."""
    with patch("skills.fal_image.client.fal_client") as m:
        m.subscribe.return_value = FAKE_RESULT
        m.upload_file.return_value = "https://fal.media/uploaded.png"
        yield m


@pytest.fixture
def registry_snapshot():
    from skills.fal_image.registry import MODEL_REGISTRY
    return dict(MODEL_REGISTRY)


@pytest.fixture
def fake_fal_result():
    return FAKE_RESULT.copy()
