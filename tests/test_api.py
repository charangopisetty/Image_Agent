"""API tests — crew is mocked; no live Groq calls."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from litellm.exceptions import RateLimitError

from image_agent.api import app
from image_agent.errors import ErrorCode, classify_exception
from image_agent.models import SocialPostResponse

client = TestClient(app)

VALID_REQUEST = {
    "image_url": "https://example.com/food.jpg",
    "platform": "instagram",
    "asset_type": "post",
    "brand_context": {
        "business_name": "Joe's Pizza",
        "website_url": "https://joespizza.com",
        "summary": "Family-owned Neapolitan pizzeria.",
        "tone": "warm, casual, local",
        "cuisine": "Italian",
        "location_hint": "Brooklyn, NY",
        "personality": ["friendly", "authentic"],
        "colors": ["#C0392B", "#F5E6CA"],
    },
    "options": {
        "max_hashtags": 15,
        "include_cta": True,
        "locale": "en-US",
    },
}

MOCK_RESPONSE = SocialPostResponse(
    caption="Fresh pizza night.",
    caption_variants=["Alt 1", "Alt 2"],
    hashtags=["#pizza", "#brooklyn"],
    image_tags=["pizza", "margherita"],
    cta="Order now — link in bio",
    platform_notes="Keep under 2200 chars for Instagram.",
)


@pytest.fixture
def mock_generate():
    with patch("image_agent.api.generate_social_post") as mocked:
        mocked.return_value = MOCK_RESPONSE
        yield mocked


class TestHealth:
    def test_health_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSocialPostValidation:
    def test_missing_image_url_returns_422(self):
        payload = {**VALID_REQUEST}
        del payload["image_url"]
        response = client.post("/social-post", json=payload)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == ErrorCode.VALIDATION_ERROR

    def test_invalid_image_url_returns_422(self):
        payload = {**VALID_REQUEST, "image_url": "not-a-url"}
        response = client.post("/social-post", json=payload)
        assert response.status_code == 422


class TestSocialPostSuccess:
    def test_create_social_post(self, mock_generate):
        response = client.post("/social-post", json=VALID_REQUEST)
        assert response.status_code == 200
        body = response.json()
        assert body["caption"] == MOCK_RESPONSE.caption
        assert body["hashtags"] == MOCK_RESPONSE.hashtags
        mock_generate.assert_called_once()


class TestErrorMapping:
    def test_rate_limit_maps_to_429(self):
        status, code, _ = classify_exception(RateLimitError("rate limited", "groq", "groq/qwen"))
        assert status == 429
        assert code == ErrorCode.RATE_LIMIT_EXCEEDED
