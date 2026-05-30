"""Tool trace rendering helpers."""

from __future__ import annotations

from typing import Any

from .display import format_duration, format_section, indent_block, pretty_json


def render_tool_event(event_name: str, payload: dict[str, Any], *, max_chars: int = 1200) -> str:
    lines = [format_section("TOOL", str(
        payload.get("tool", "unknown")).upper())]
    if event_name == "tool.start":
        lines.append(format_section("ARGS"))
        lines.append(indent_block(pretty_json(
            payload.get("input", {}), max_chars=max_chars)))
        return "\n".join(lines)

    status = "SUCCESS" if payload.get("ok", False) else "FAILED"
    lines.append(format_section("STATUS", status))
    lines.append(format_section(
        "TIME", format_duration(payload.get("duration_ms"))))
    lines.append(format_section("ARGS"))
    lines.append(indent_block(pretty_json(
        payload.get("input", {}), max_chars=max_chars)))
    lines.append(format_section("RESULT"))
    lines.append(indent_block(pretty_json(
        payload.get("result", {}), max_chars=max_chars)))
    return "\n".join(lines)
