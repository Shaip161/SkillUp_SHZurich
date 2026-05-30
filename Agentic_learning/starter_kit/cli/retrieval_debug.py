"""Retrieval debugging renderers."""

from __future__ import annotations

from typing import Any

from .display import format_duration, format_section, indent_block, pretty_json


def render_retrieval_event(payload: dict[str, Any], *, max_chars: int = 1200) -> str:
    lines = [format_section("RETRIEVAL", str(
        payload.get("retriever", "retriever")).upper())]
    lines.append(format_section("QUERY", str(payload.get("query", ""))))
    lines.append(format_section(
        "STATUS", f"{payload.get('result_count', 0)} chunks"))
    lines.append(format_section(
        "TIME", format_duration(payload.get("duration_ms"))))
    lines.append(format_section("CHUNKS"))
    lines.append(indent_block(pretty_json(
        payload.get("results", []), max_chars=max_chars)))
    selected_context = payload.get("selected_context") or []
    if selected_context:
        lines.append(format_section("SELECTED_CONTEXT"))
        lines.append(indent_block(pretty_json(
            selected_context, max_chars=max_chars)))
    return "\n".join(lines)
