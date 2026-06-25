#!/usr/bin/env python
import json
import sys
import warnings

import crewai.llms.cache as _crewai_cache

_crewai_cache.mark_cache_breakpoint = lambda msg: msg

from image_agent.service import build_crew_inputs, generate_social_post
from image_agent.schemas import SocialPostRequest

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

EXAMPLE_PAYLOAD = {
    "image_url": "https://ik.imagekit.io/fooai/socials/example/uploaded_at_example.jpeg",
    "asset_type": "post",
    "brand_context": {
        "business_name": "Joe's Pizza",
        "website_url": "https://joespizza.com",
        "summary": "Family-owned Neapolitan pizzeria in Brooklyn.",
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


def run(payload: dict | None = None) -> None:
    """Run the crew with an example or custom request payload."""
    payload = payload or EXAMPLE_PAYLOAD
    request = SocialPostRequest.model_validate(payload)
    output = generate_social_post(request)

    print("\n\n=== SOCIAL POST OUTPUT ===\n\n")
    print(json.dumps(output.model_dump(), indent=2))


def run_with_trigger() -> None:
    """Run from JSON passed as first CLI argument."""
    if len(sys.argv) < 2:
        raise SystemExit(
            "Usage: run_with_trigger '<json payload>'\n"
            "Or: uv run run_with_trigger examples/request.json"
        )

    arg = sys.argv[1]
    if arg.endswith(".json"):
        with open(arg, encoding="utf-8") as f:
            payload = json.load(f)
    else:
        payload = json.loads(arg)

    run(payload)


if __name__ == "__main__":
    run()
