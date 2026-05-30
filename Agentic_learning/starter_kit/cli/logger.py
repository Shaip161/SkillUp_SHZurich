"""CLI event observer that renders structured runtime events to a text stream."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, TextIO

from ..logging import LOG_LEVEL_RANKS
from .display import (
    estimate_tokens,
    format_section,
    indent_block,
    parse_prompt_sections,
    pretty_json,
    truncate_text,
)
from .retrieval_debug import render_retrieval_event
from .state_view import render_state_diff, render_state_summary
from .tool_trace import render_tool_event
from .workflow_view import render_workflow_event


@dataclass
class ObservabilityConfig:
    mode: str = "standard"
    max_chars: int = 1200
    show_json: bool = False
    show_token_counts: bool = False
    show_state_diffs: bool = True
    show_prompt_sections: bool = True
    graph_format: str = "ascii"


class CliObserver:
    def __init__(
        self,
        config: ObservabilityConfig | None = None,
        *,
        stream: TextIO | None = None,
    ) -> None:
        self.config = config or ObservabilityConfig()
        self.stream = stream or sys.stdout

    def handle_event(self, event: dict[str, Any]) -> None:
        if not self._should_render(str(event.get("level", "standard"))):
            return
        rendered = self.render_event(event)
        if not rendered:
            return
        self.stream.write(rendered + "\n")
        self.stream.flush()

    def _should_render(self, event_level: str) -> bool:
        configured_rank = LOG_LEVEL_RANKS.get(
            self.config.mode, LOG_LEVEL_RANKS["standard"])
        event_rank = LOG_LEVEL_RANKS.get(
            event_level, LOG_LEVEL_RANKS["standard"])
        return configured_rank >= event_rank

    def render_event(self, event: dict[str, Any]) -> str | None:
        event_name = str(event.get("event", ""))
        payload = dict(event.get("payload", {}) or {})
        if event_name.startswith("workflow."):
            return render_workflow_event(
                event_name,
                payload,
                max_chars=self.config.max_chars,
                show_json=self.config.show_json,
                output_format=self.config.graph_format,
            )
        if event_name.startswith("tool."):
            return render_tool_event(event_name, payload, max_chars=self.config.max_chars)
        if event_name == "retrieval.search":
            return render_retrieval_event(payload, max_chars=self.config.max_chars)
        if event_name.startswith("agent."):
            return self._render_agent_event(event_name, payload)
        return None

    def _render_agent_event(self, event_name: str, payload: dict[str, Any]) -> str | None:
        agent_name = str(payload.get("agent", "agent")).upper()
        lines = [format_section("AGENT", agent_name)]

        if event_name == "agent.start":
            lines.append(format_section("STATUS", "STARTED"))
            state_summary = payload.get("state_summary")
            if isinstance(state_summary, dict):
                lines.append(format_section("STATE", render_state_summary(
                    state_summary, max_chars=self.config.max_chars)))
            return "\n".join(lines)

        if event_name == "agent.prompt":
            lines.append(format_section(
                "STEP", str(payload.get("step_id", "?"))))
            prompt_text = str(payload.get("prompt", ""))
            if self.config.show_token_counts:
                lines.append(format_section(
                    "TOKENS_EST", str(estimate_tokens(prompt_text))))
            if self.config.show_prompt_sections:
                for title, content in parse_prompt_sections(prompt_text):
                    lines.append(format_section(title))
                    lines.append(indent_block(truncate_text(
                        content, self.config.max_chars)))
            else:
                lines.append(format_section("PROMPT"))
                lines.append(indent_block(truncate_text(
                    prompt_text, self.config.max_chars)))
            return "\n".join(lines)

        if event_name == "agent.response":
            lines.append(format_section(
                "STEP", str(payload.get("step_id", "?"))))
            lines.append(format_section("RESPONSE"))
            response_text = str(payload.get("response", ""))
            lines.append(indent_block(truncate_text(
                response_text, self.config.max_chars)))
            return "\n".join(lines)

        if event_name == "agent.parsed":
            lines.append(format_section(
                "STEP", str(payload.get("step_id", "?"))))
            lines.append(format_section("PARSED"))
            lines.append(indent_block(pretty_json(
                payload, max_chars=self.config.max_chars)))
            return "\n".join(lines)

        if event_name == "agent.step.start":
            lines.append(format_section(
                "STEP", str(payload.get("step_id", "?"))))
            lines.append(format_section("STATUS", "RUNNING"))
            state_summary = payload.get("state_summary")
            if isinstance(state_summary, dict):
                lines.append(format_section("STATE", render_state_summary(
                    state_summary, max_chars=self.config.max_chars)))
            return "\n".join(lines)

        if event_name == "agent.step.finish":
            lines.append(format_section(
                "STEP", str(payload.get("step_id", "?"))))
            lines.append(format_section("STATUS", str(
                payload.get("status", "completed")).upper()))
            lines.append(format_section("TIME", str(payload.get("duration_ms", "n/a")) +
                         "ms" if isinstance(payload.get("duration_ms"), (int, float)) else "n/a"))
            state_summary = payload.get("state_summary")
            if isinstance(state_summary, dict):
                lines.append(format_section("STATE", render_state_summary(
                    state_summary, max_chars=self.config.max_chars)))
            if self.config.show_state_diffs and isinstance(payload.get("state_diff"), dict):
                lines.append(render_state_diff(
                    payload["state_diff"], max_chars=self.config.max_chars, show_json=self.config.show_json))
            return "\n".join(lines)

        if event_name == "agent.error":
            lines.append(format_section("STATUS", "FAILED"))
            lines.append(format_section("ERROR"))
            lines.append(indent_block(pretty_json(
                payload, max_chars=self.config.max_chars)))
            return "\n".join(lines)

        if event_name == "agent.finish":
            lines.append(format_section("STATUS", str(
                payload.get("status", "completed")).upper()))
            state_summary = payload.get("state_summary")
            if isinstance(state_summary, dict):
                lines.append(format_section("STATE", render_state_summary(
                    state_summary, max_chars=self.config.max_chars)))
            outputs = payload.get("outputs")
            if outputs:
                lines.append(format_section("OUTPUTS"))
                lines.append(indent_block(pretty_json(
                    outputs, max_chars=self.config.max_chars)))
            return "\n".join(lines)

        return None


def attach_cli_observer(
    logger: Any,
    config: ObservabilityConfig | None = None,
    *,
    stream: TextIO | None = None,
) -> CliObserver:
    observer = CliObserver(config, stream=stream)
    logger.attach(observer)
    return observer
