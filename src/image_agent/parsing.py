import json
import re

from json_repair import repair_json
from pydantic import BaseModel

from image_agent.models import SocialPostResponse


def _extract_json(raw: str) -> dict:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    return json.loads(repair_json(text))


def parse_social_post_response(raw: str) -> SocialPostResponse:
    """Parse crew output into the API response schema."""
    return SocialPostResponse.model_validate(_extract_json(raw))


def pydantic_to_dict(model: BaseModel | None) -> dict | None:
    if model is None:
        return None
    return model.model_dump()
