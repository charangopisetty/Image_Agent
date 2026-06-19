import json
import os
import re

from json_repair import repair_json
from litellm import completion

from image_agent.llm import resolve_llm
from image_agent.models import ImageAnalysis

_VISION_PROMPT = """Analyze this food or restaurant image.

Return ONLY a JSON object with these keys:
- image_tags: array of 3-8 concrete tag strings
- scene_summary: string, 1-2 sentences describing what is visible
- mood: string, e.g. cozy, celebratory, appetizing
- food_items: array of visible food/drink items

Rules:
- Describe only what you can see in the image
- Do not invent brand names or menu items not shown
- No markdown, no code fences, no extra keys"""


def _extract_json(raw: str) -> dict:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    return json.loads(repair_json(text))


def analyze_image_url(image_url: str) -> ImageAnalysis:
    """Call the vision LLM directly (avoids Groq + CrewAI tool conflicts)."""
    model = resolve_llm(os.getenv("VISION_MODEL"), vision=True)
    response = completion(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _VISION_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
    )
    raw = response.choices[0].message.content or ""
    return ImageAnalysis.model_validate(_extract_json(raw))
