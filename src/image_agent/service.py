import json
import logging
import random
import string
from concurrent.futures import ThreadPoolExecutor
from functools import cache
from pathlib import Path

import yaml
import crewai.llms.cache as _crewai_cache

_crewai_cache.mark_cache_breakpoint = lambda msg: msg

from image_agent.cliches import BANNED_PHRASES
from image_agent.crew import ImageAgent
from image_agent.models import (
    FacebookPostContent,
    ImageAnalysis,
    InstagramPostContent,
    SocialPostResponse,
)
from image_agent.parsing import extract_platform_json
from image_agent.schemas import SocialPostRequest
from image_agent.vision import analyze_image_url

logger = logging.getLogger(__name__)

ANGLES_PATH = Path(__file__).parent / "config" / "angles.yaml"


@cache
def load_angles() -> dict[str, dict[str, str]]:
    """Creative angles for the air-gapped drafters, keyed by angle id."""
    with open(ANGLES_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


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
        "standout_details": "; ".join(data["standout_details"]) or "none noted",
        "banned_phrases": ", ".join(f'"{phrase}"' for phrase in BANNED_PHRASES),
        "max_hashtags": opts.get("max_hashtags", 15),
        "locale": opts.get("locale", "en-US"),
        "cta_instruction": (
            "Include a short CTA suitable for link-in-bio."
            if opts.get("include_cta", True)
            else "Do not include a CTA."
        ),
    }


def _run_drafter(
    inputs: dict, angle_id: str, angle: dict[str, str], lead_hook: int
) -> dict[str, str] | None:
    """Run one drafter in its own crew. It sees the brief, never other drafts.

    Each drafter opens on a different numbered hook so isolated drafters don't
    all converge on the photo's most obvious detail.
    """
    angle_inputs = {
        **inputs,
        "angle_name": angle["name"],
        "angle_direction": angle["direction"],
        "lead_hook": lead_hook,
    }
    try:
        result = ImageAgent().draft_crew().kickoff(inputs=angle_inputs)
        draft = extract_platform_json(result.raw)
        return {
            "angle": angle_id,
            "instagram": str(draft["instagram"]).strip(),
            "facebook": str(draft["facebook"]).strip(),
        }
    except Exception:
        logger.exception("Drafter %s failed; continuing with the other drafts", angle_id)
        return None


def run_air_gapped_drafters(inputs: dict) -> list[dict[str, str]]:
    """Run every angle's drafter in parallel, each isolated from the others."""
    angles = load_angles()
    with ThreadPoolExecutor(max_workers=len(angles)) as pool:
        futures = [
            pool.submit(_run_drafter, inputs, angle_id, angle, lead_hook)
            for lead_hook, (angle_id, angle) in enumerate(angles.items(), start=1)
        ]
        drafts = [draft for future in futures if (draft := future.result())]
    if not drafts:
        raise RuntimeError("All caption drafters failed.")
    return drafts


def format_blind_drafts(drafts: list[dict[str, str]], platform: str) -> str:
    """Shuffle drafts and label them A, B, C... so editors judge the writing, not the angle."""
    shuffled = random.sample(drafts, k=len(drafts))
    return "\n\n".join(
        f"Draft {label}:\n{draft[platform]}"
        for label, draft in zip(string.ascii_uppercase, shuffled)
    )


def generate_social_post(request: SocialPostRequest) -> SocialPostResponse:
    """Vision -> brief -> air-gapped drafters -> blind per-platform editors."""
    payload = request.model_dump(mode="json")
    analysis = analyze_image_url(payload["image_url"])
    inputs = build_crew_inputs(payload, analysis)

    brief = ImageAgent().brief_crew().kickoff(inputs=inputs)
    inputs["creative_brief"] = brief.raw

    drafts = run_air_gapped_drafters(inputs)
    inputs["instagram_drafts"] = format_blind_drafts(drafts, "instagram")
    inputs["facebook_drafts"] = format_blind_drafts(drafts, "facebook")

    with ThreadPoolExecutor(max_workers=2) as pool:
        instagram = pool.submit(ImageAgent().instagram_crew().kickoff, inputs=inputs)
        facebook = pool.submit(ImageAgent().facebook_crew().kickoff, inputs=inputs)
        instagram_raw = instagram.result().raw
        facebook_raw = facebook.result().raw

    return SocialPostResponse(
        instagram=InstagramPostContent.model_validate(extract_platform_json(instagram_raw)),
        facebook=FacebookPostContent.model_validate(extract_platform_json(facebook_raw)),
        image_tags=analysis.image_tags,
    )
