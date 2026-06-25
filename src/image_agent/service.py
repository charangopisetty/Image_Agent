import crewai.llms.cache as _crewai_cache

_crewai_cache.mark_cache_breakpoint = lambda msg: msg

from image_agent.crew import ImageAgent
from image_agent.models import SocialPostResponse
from image_agent.parsing import parse_social_post_response
from image_agent.schemas import SocialPostRequest


def build_crew_inputs(payload: dict) -> dict:
    brand = payload["brand_context"]
    opts = payload.get("options") or {}
    return {
        "image_url": str(payload["image_url"]),
        "asset_type": payload["asset_type"],
        "business_name": brand["business_name"],
        "website_url": brand.get("website_url", ""),
        "summary": brand["summary"],
        "tone": brand["tone"],
        "cuisine": brand.get("cuisine", ""),
        "location_hint": brand.get("location_hint", ""),
        "personality": ", ".join(brand.get("personality", [])),
        "colors": ", ".join(brand.get("colors", [])),
        "max_hashtags": opts.get("max_hashtags", 15),
        "locale": opts.get("locale", "en-US"),
        "cta_instruction": (
            "Include a short CTA suitable for link-in-bio."
            if opts.get("include_cta", True)
            else "Do not include a CTA."
        ),
    }


def generate_social_post(request: SocialPostRequest) -> SocialPostResponse:
    """Run the crew and return structured social post content."""
    inputs = build_crew_inputs(request.model_dump(mode="json"))
    result = ImageAgent().crew().kickoff(inputs=inputs)
    if result.pydantic:
        return result.pydantic  # type: ignore[return-value]
    return parse_social_post_response(result.raw)
