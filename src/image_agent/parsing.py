import json
import re

from json_repair import repair_json


def _strip_thinking(text: str) -> str:
    text = re.sub(
        r"<think>[\s\S]*?</think>",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text.strip()


def extract_platform_json(raw: str) -> dict:
    """Extract a single JSON object from a writer task's raw output.

    Handles Qwen-style <think> blocks, markdown fences, and surrounding prose.
    """
    text = _strip_thinking((raw or "").strip())
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        text = text[start : end + 1]
    return json.loads(repair_json(text))
