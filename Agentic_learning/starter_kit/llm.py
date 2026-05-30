"""LLM client adapters with a small callable-based default and OpenAI support."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Protocol


class LlmClient(Protocol):
    def generate(self, prompt_text: str, *, metadata: dict[str, Any] | None = None) -> str:
        ...


def load_local_dotenv(start_path: str | Path | None = None) -> Path | None:
    """Load the nearest local .env file without overriding existing env vars."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return None

    anchor = Path(start_path or __file__).resolve()
    search_root = anchor if anchor.is_dir() else anchor.parent
    for candidate_dir in (search_root, *search_root.parents):
        candidate = candidate_dir / ".env"
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            return candidate
    return None


_LOADED_DOTENV_PATH = load_local_dotenv()
_RESPONSES_MODELS_WITHOUT_TEMPERATURE_PREFIXES = ("gpt-5",)


def build_responses_create_kwargs(
    *,
    model_name: str,
    prompt_text: str,
    temperature: float | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": model_name,
        "input": prompt_text,
    }
    if temperature is None:
        return kwargs
    if model_name.strip().lower().startswith(_RESPONSES_MODELS_WITHOUT_TEMPERATURE_PREFIXES):
        return kwargs
    kwargs["temperature"] = temperature
    return kwargs


def _iter_output_text_blocks(response: Any) -> list[str]:
    blocks: list[str] = []
    for output in list(getattr(response, "output", []) or []):
        if getattr(output, "type", None) != "message":
            continue
        for content in list(getattr(output, "content", []) or []):
            if getattr(content, "type", None) != "output_text":
                continue
            text = getattr(content, "text", None)
            if isinstance(text, str) and text.strip():
                blocks.append(text)
    return blocks


def extract_response_text(response: Any) -> str:
    text_blocks = _iter_output_text_blocks(response)
    if not text_blocks:
        fallback = getattr(response, "output_text", "")
        return fallback if isinstance(fallback, str) else ""
    normalized_blocks = [block.strip() for block in text_blocks]
    if len(normalized_blocks) > 1 and len(set(normalized_blocks)) == 1:
        return text_blocks[0]
    return "".join(text_blocks)


class CallableLlmClient:
    def __init__(self, generate_fn: Callable[[str], str]) -> None:
        self._generate_fn = generate_fn

    def generate(self, prompt_text: str, *, metadata: dict[str, Any] | None = None) -> str:
        _ = metadata
        return self._generate_fn(prompt_text)


class OpenAIResponsesClient:
    """Small OpenAI Responses API adapter suitable for quick experiments."""

    def __init__(self, model_name: str, *, temperature: float | None = 0.0) -> None:
        self.model_name = model_name
        self.temperature = temperature

    def generate(self, prompt_text: str, *, metadata: dict[str, Any] | None = None) -> str:
        _ = metadata
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "OpenAI package is not installed. Install 'openai' to use OpenAIResponsesClient."
            ) from exc

        client = OpenAI()
        response = client.responses.create(
            **build_responses_create_kwargs(
                model_name=self.model_name,
                prompt_text=prompt_text,
                temperature=self.temperature,
            )
        )
        return extract_response_text(response)
