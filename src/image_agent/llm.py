import os

# Known LiteLLM / CrewAI provider prefixes
_KNOWN_PREFIXES = (
    "groq/",
    "openai/",
    "anthropic/",
    "azure/",
    "gemini/",
    "google/",
    "ollama/",
    "bedrock/",
    "openrouter/",
)

# Groq model aliases → official Groq model id (without groq/ prefix)
_GROQ_ALIASES: dict[str, str] = {
    "qwen/qwen3.6-27b": "qwen/qwen3-32b",
    "qwen3.6-27b": "qwen/qwen3-32b",
    "qwen/qwen3-32b": "qwen/qwen3-32b",
    "llama-3.1-8b-instant": "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile": "llama-3.3-70b-versatile",
}

DEFAULT_TEXT_MODEL = "groq/qwen/qwen3-32b"
DEFAULT_VISION_MODEL = "groq/meta-llama/llama-4-scout-17b-16e-instruct"


def resolve_llm(model: str | None, *, vision: bool = False) -> str:
    """Normalize MODEL env values to a LiteLLM-compatible provider/model string."""
    if not model:
        return DEFAULT_VISION_MODEL if vision else DEFAULT_TEXT_MODEL

    model = model.strip()
    if any(model.startswith(prefix) for prefix in _KNOWN_PREFIXES):
        return model

    groq_key = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if groq_key:
        groq_model = _GROQ_ALIASES.get(model, model)
        return f"groq/{groq_model}"

    if openai_key:
        return f"openai/{model}"

    raise ValueError(
        f"Model '{model}' has no provider prefix (e.g. groq/ or openai/). "
        "Set GROQ_API_KEY or OPENAI_API_KEY in .env, or use a full model id like groq/qwen/qwen3-32b."
    )
