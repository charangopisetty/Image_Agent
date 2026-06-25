import json

import crewai.llms.cache as _crewai_cache

_crewai_cache.mark_cache_breakpoint = lambda msg: msg

from image_agent.crew import ImageAgent
from image_agent.models import (
    FacebookPostContent,
    ImageAnalysis,
    InstagramPostContent,
    RedditPostContent,
    SocialPostResponse,
    TwitterPostContent,
)
from image_agent.parsing import extract_platform_json
from image_agent.schemas import SocialPostRequest
from image_agent.vision import analyze_image_url


def build_crew_inputs(payload: dict, analysis: ImageAnalysis) -> dict:
    brand = payload["brand_context"]
    opts = payload.get("options") or {}
    data = analysis.model_dump()
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
        "image_analysis_json": json.dumps(data, indent=2),
        "image_tags_list": ", ".join(data["image_tags"]),
        "scene_summary": data["scene_summary"],
        "mood": data["mood"],
        "food_items": ", ".join(data["food_items"]),
        "max_hashtags": opts.get("max_hashtags", 15),
        "locale": opts.get("locale", "en-US"),
        "cta_instruction": (
            "Include a short CTA suitable for link-in-bio."
            if opts.get("include_cta", True)
            else "Do not include a CTA."
        ),
    }


def _raw_by_task(result) -> dict[str, str]:
    """Map each task output to its task name, falling back to positional index."""
    mapping: dict[str, str] = {}
    for index, task_output in enumerate(result.tasks_output):
        name = (getattr(task_output, "name", None) or "").lower()
        mapping[name or f"index_{index}"] = task_output.raw or ""
        mapping[f"index_{index}"] = task_output.raw or ""
    return mapping


def generate_social_post(request: SocialPostRequest) -> SocialPostResponse:
    """Run vision, then the sequential per-platform crew, and assemble the response."""
    payload = request.model_dump(mode="json")
    analysis = analyze_image_url(payload["image_url"])
    inputs = build_crew_inputs(payload, analysis)

    result = ImageAgent().crew().kickoff(inputs=inputs)
    raw = _raw_by_task(result)

    def platform_raw(name: str, order_index: int) -> str:
        return raw.get(name) or raw.get(f"index_{order_index}", "{}")

    return SocialPostResponse(
        twitter=TwitterPostContent.model_validate(
            extract_platform_json(platform_raw("twitter", 1))
        ),
        reddit=RedditPostContent.model_validate(
            extract_platform_json(platform_raw("reddit", 2))
        ),
        instagram=InstagramPostContent.model_validate(
            extract_platform_json(platform_raw("instagram", 3))
        ),
        facebook=FacebookPostContent.model_validate(
            extract_platform_json(platform_raw("facebook", 4))
        ),
        image_tags=analysis.image_tags,
    )
