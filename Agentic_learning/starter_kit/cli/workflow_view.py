"""Workflow execution and graph renderers."""

from __future__ import annotations

import json
from typing import Any

from .display import format_duration, format_section, indent_block, pretty_json
from .state_view import render_state_diff, render_state_summary


def workflow_graph_to_mermaid(graph: dict[str, Any]) -> str:
    lines = ["graph TD"]
    for edge in list(graph.get("edges", []) or []):
        lines.append(f"  {edge['from']} --> {edge['to']}")
    if len(lines) == 1:
        for node in list(graph.get("nodes", []) or []):
            lines.append(f"  {node['name']}")
    return "\n".join(lines)


def render_workflow_graph(
    graph: dict[str, Any],
    *,
    current_node: str | None = None,
    output_format: str = "ascii",
) -> str:
    normalized_format = output_format.strip().lower()
    if normalized_format == "json":
        return json.dumps(graph, indent=2, ensure_ascii=True)
    if normalized_format == "mermaid":
        return workflow_graph_to_mermaid(graph)

    lines = [format_section("WORKFLOW_GRAPH", str(
        graph.get("workflow", "workflow")).upper())]
    for node in list(graph.get("nodes", []) or []):
        marker = "*" if node.get("name") == current_node else "-"
        next_node = node.get("default_next") or "END"
        lines.append(f"{marker} {node['name']} -> {next_node}")
    return "\n".join(lines)


def render_workflow_event(
    event_name: str,
    payload: dict[str, Any],
    *,
    max_chars: int = 1200,
    show_json: bool = False,
    output_format: str = "ascii",
) -> str:
    if event_name == "workflow.graph":
        return render_workflow_graph(
            dict(payload.get("graph", {}) or {}),
            current_node=str(payload.get("current_node") or "") or None,
            output_format=output_format,
        )

    workflow_name = str(payload.get("workflow", "workflow")).upper()
    lines = [format_section("WORKFLOW", workflow_name)]
    if event_name == "workflow.start":
        lines.append(format_section("STATUS", "STARTED"))
        lines.append(format_section("STEP", str(
            payload.get("start_at", "")).upper()))
    elif event_name == "workflow.finish":
        lines.append(format_section("STATUS", str(
            payload.get("status", "completed")).upper()))
        lines.append(format_section(
            "TIME", format_duration(payload.get("duration_ms"))))
    elif event_name == "workflow.node.start":
        lines.append(format_section(
            "STEP", str(payload.get("node", "")).upper()))
        lines.append(format_section("STATUS", "RUNNING"))
    elif event_name == "workflow.node.finish":
        status_value = str(payload.get("status", "success")).upper()
        if status_value == "SUCCESS":
            status_value = "SUCCESS"
        lines.append(format_section(
            "STEP", str(payload.get("node", "")).upper()))
        lines.append(format_section("STATUS", status_value))
        lines.append(format_section(
            "TIME", format_duration(payload.get("duration_ms"))))
    elif event_name == "workflow.node.error":
        lines.append(format_section(
            "STEP", str(payload.get("node", "")).upper()))
        lines.append(format_section("STATUS", "FAILED"))
        lines.append(format_section("ERROR"))
        lines.append(indent_block(pretty_json(payload, max_chars=max_chars)))
        return "\n".join(lines)

    state_summary = payload.get("state_summary")
    if isinstance(state_summary, dict):
        lines.append(format_section("STATE", render_state_summary(
            state_summary, max_chars=max_chars)))
    state_diff = payload.get("state_diff")
    if isinstance(state_diff, dict):
        lines.append(render_state_diff(
            state_diff, max_chars=max_chars, show_json=show_json))
    return "\n".join(lines)
