"""State summaries and diff rendering for CLI output."""

from __future__ import annotations

from typing import Any

from .display import compact_json, format_section, indent_block, pretty_json, truncate_text


def render_state_summary(summary: dict[str, Any], *, max_chars: int = 1200) -> str:
    parts = [
        f"status={summary.get('status', 'unknown')}",
        f"step={summary.get('current_step', 0)}/{summary.get('max_steps', '?')}",
        f"shared={len(summary.get('shared_keys', []))}",
        f"outputs={len(summary.get('output_keys', []))}",
        f"errors={summary.get('error_count', 0)}",
        f"messages={summary.get('message_count', 0)}",
    ]
    return truncate_text(" | ".join(parts), max_chars)


def _has_mapping_changes(diff_block: dict[str, Any]) -> bool:
    return bool(diff_block.get("added") or diff_block.get("removed") or diff_block.get("changed"))


def render_state_diff(diff: dict[str, Any], *, max_chars: int = 1200, show_json: bool = False) -> str:
    if not diff:
        return format_section("STATE_DIFF", "none")

    lines: list[str] = []
    if diff.get("step_changed"):
        lines.append("step advanced")
    if diff.get("status_changed"):
        lines.append("status changed")
    if diff.get("error_count_delta"):
        lines.append(f"errors +{diff['error_count_delta']}")
    if diff.get("history_count_delta"):
        lines.append(f"history +{diff['history_count_delta']}")
    if diff.get("message_count_delta"):
        lines.append(f"messages +{diff['message_count_delta']}")

    for field_name in ("shared", "outputs"):
        block = dict(diff.get(field_name, {}) or {})
        if not _has_mapping_changes(block):
            continue
        rendered = pretty_json(block, max_chars=max_chars) if show_json else compact_json(
            block, max_chars=max_chars)
        lines.append(f"{field_name}: {rendered}")

    if not lines:
        lines.append("no visible state changes")
    return "\n".join(
        [
            format_section("STATE_DIFF"),
            indent_block("\n".join(lines)),
        ]
    )
