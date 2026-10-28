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

# Groq text model aliases → official Groq model id (without groq/ prefix)
# qwen3-32b is retired on this org; qwen3.8-27b is listed but org-blocked.
_GROQ_TEXT_ALIASES: dict[str, str] = {
    "qwen/qwen3.6-27b": "qwen/qwen3.6-27b",
    "qwen3.6-27b": "qwen/qwen3.6-27b",
    "qwen/qwen3.8-27b": "qwen/qwen3.6-27b",
    "qwen3.8-27b": "qwen/qwen3.6-27b",
    "qwen/qwen3-32b": "qwen/qwen3.6-27b",
    "qwen3-32b": "qwen/qwen3.6-27b",
    "llama-3.1-8b-instant": "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile": "llama-3.3-70b-versatile",
}

# Groq vision/multimodal models
_GROQ_VISION_ALIASES: dict[str, str] = {
    "qwen/qwen3.6-27b": "qwen/qwen3.6-27b",
    "qwen3.6-27b": "qwen/qwen3.6-27b",
    "qwen/qwen3.8-27b": "qwen/qwen3.6-27b",
    "qwen3.8-27b": "qwen/qwen3.6-27b",
    "qwen/qwen3-32b": "qwen/qwen3.6-27b",
    "qwen3-32b": "qwen/qwen3.6-27b",
    "meta-llama/llama-4-scout-17b-16e-instruct": "meta-llama/llama-4-scout-17b-16e-instruct",
}

# ChatGPT Luna is OpenAI model id gpt-6-luna (text + image input).
_OPENAI_ALIASES: dict[str, str] = {
    "gpt-6-luna": "gpt-6-luna",
    "chatgpt-luna": "gpt-6-luna",
    "chatgpt luna": "gpt-6-luna",
    "gpt-6 luna": "gpt-6-luna",
    "luna": "gpt-6-luna",
}

DEFAULT_TEXT_MODEL = "openai/gpt-6-luna"
DEFAULT_VISION_MODEL = "openai/gpt-6-luna"


def _openai_model_id(model: str) -> str:
    return _OPENAI_ALIASES.get(model.strip().lower(), model)


def resolve_llm(model: str | None, *, vision: bool = False) -> str:
    """Normalize MODEL env values to a LiteLLM-compatible provider/model string."""
    if not model:
        return DEFAULT_VISION_MODEL if vision else DEFAULT_TEXT_MODEL

    model = model.strip()
    if model.startswith("openai/"):
        openai_id = _openai_model_id(model.removeprefix("openai/"))
        return f"openai/{openai_id}"
    if model.startswith("groq/"):
        aliases = _GROQ_VISION_ALIASES if vision else _GROQ_TEXT_ALIASES
        groq_id = model.removeprefix("groq/")
        return f"groq/{aliases.get(groq_id, groq_id)}"
    if any(model.startswith(prefix) for prefix in _KNOWN_PREFIXES):
        return model

    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    if openai_key:
        return f"openai/{_openai_model_id(model)}"

    if groq_key:
        aliases = _GROQ_VISION_ALIASES if vision else _GROQ_TEXT_ALIASES
        groq_model = aliases.get(model, model)
        return f"groq/{groq_model}"

    raise ValueError(
        f"Model '{model}' has no provider prefix (e.g. openai/ or groq/). "
        "Set OPENAI_API_KEY in .env, or use a full model id like openai/gpt-6-luna."
    )
