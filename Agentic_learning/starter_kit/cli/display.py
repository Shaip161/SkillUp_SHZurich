"""Shared text rendering helpers for CLI observability output."""

from __future__ import annotations

import json
from typing import Any


def truncate_text(text: str, max_chars: int) -> str:
    normalized = str(text)
    if max_chars <= 0 or len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3] + "..."


def estimate_tokens(text: str) -> int:
    normalized = str(text)
    if not normalized:
        return 0
    return max(1, round(len(normalized) / 4))


def pretty_json(value: Any, *, max_chars: int = 1200) -> str:
    rendered = json.dumps(value, indent=2, ensure_ascii=True, default=str)
    return truncate_text(rendered, max_chars)


def compact_json(value: Any, *, max_chars: int = 1200) -> str:
    rendered = json.dumps(value, ensure_ascii=True, default=str)
    return truncate_text(rendered, max_chars)


def format_section(title: str, body: str | None = None) -> str:
    if body is None or not str(body).strip():
        return f"[{title}]"
    return f"[{title}] {body}"


def indent_block(text: str, *, prefix: str = "  ") -> str:
    lines = str(text).splitlines() or [""]
    return "\n".join(f"{prefix}{line}" for line in lines)


def format_duration(duration_ms: float | int | None) -> str:
    if duration_ms is None:
        return "n/a"
    value = float(duration_ms)
    if value >= 1000:
        return f"{value / 1000:.2f}s"
    return f"{value:.1f}ms"


def clip_list(items: list[Any], *, max_items: int) -> list[Any]:
    if max_items <= 0:
        return []
    return list(items[:max_items])


def parse_prompt_sections(prompt_text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []
    for raw_line in str(prompt_text).splitlines():
        stripped = raw_line.strip()
        if stripped.endswith(":") and stripped[:-1] and stripped[:-1] == stripped[:-1].upper():
            if current_title is not None:
                sections.append(
                    (current_title, "\n".join(current_lines).strip()))
            current_title = stripped[:-1]
            current_lines = []
            continue
        current_lines.append(raw_line)

    if current_title is not None:
        sections.append((current_title, "\n".join(current_lines).strip()))
    if sections:
        return sections
    return [("PROMPT", str(prompt_text).strip())]
