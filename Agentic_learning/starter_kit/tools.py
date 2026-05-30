"""Pluggable tool registry with explicit validation and uniform results."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from traceback import format_exc
from typing import Any, Callable

from .validation import validate_required_keys

ToolHandler = Callable[[dict[str, Any], "ToolContext"], Any]


@dataclass
class ToolContext:
    state: Any
    logger: Any = None
    services: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDefinition:
    name: str
    description: str
    handler: ToolHandler
    required_keys: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "required_keys": list(self.required_keys),
            "metadata": dict(self.metadata),
        }


class ToolRegistry:
    def __init__(self, tools: list[ToolDefinition] | None = None) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: ToolDefinition) -> None:
        normalized_name = str(tool.name).strip()
        if not normalized_name:
            raise ValueError("tool.name must be a non-empty string")
        self._tools[normalized_name] = tool

    def get(self, tool_name: str) -> ToolDefinition | None:
        return self._tools.get(str(tool_name).strip())

    def names(self) -> list[str]:
        return sorted(self._tools.keys())

    def describe(self) -> list[dict[str, Any]]:
        return [self._tools[name].describe() for name in self.names()]

    def render_for_prompt(self) -> str:
        if not self._tools:
            return "NONE"
        lines = []
        for tool_name in self.names():
            definition = self._tools[tool_name]
            required = ", ".join(definition.required_keys) or "none"
            lines.append(
                f"- {tool_name}: {definition.description} (required: {required})")
        return "\n".join(lines)

    def run(
        self,
        tool_name: str,
        action_input: dict[str, Any],
        context: ToolContext,
    ) -> dict[str, Any]:
        started_at = perf_counter()
        definition = self.get(tool_name)
        if definition is None:
            result = {
                "ok": False,
                "tool": tool_name,
                "input": dict(action_input or {}),
                "value": None,
                "error_code": "UNKNOWN_TOOL",
                "error_message": f"Unknown tool '{tool_name}'.",
            }
            if context.logger is not None:
                context.logger.record(
                    "tool.finish",
                    {
                        "tool": tool_name,
                        "input": dict(action_input or {}),
                        "ok": False,
                        "duration_ms": round((perf_counter() - started_at) * 1000, 3),
                        "result": dict(result),
                    },
                    level="standard",
                )
            return result

        if not isinstance(action_input, dict):
            result = {
                "ok": False,
                "tool": definition.name,
                "input": {},
                "value": None,
                "error_code": "INVALID_ACTION_INPUT",
                "error_message": "Tool input must be a JSON object.",
            }
            if context.logger is not None:
                context.logger.record(
                    "tool.finish",
                    {
                        "tool": definition.name,
                        "input": {},
                        "ok": False,
                        "duration_ms": round((perf_counter() - started_at) * 1000, 3),
                        "result": dict(result),
                    },
                    level="standard",
                )
            return result

        missing = validate_required_keys(
            action_input, definition.required_keys)
        if missing:
            result = {
                "ok": False,
                "tool": definition.name,
                "input": dict(action_input),
                "value": None,
                "error_code": "MISSING_REQUIRED_KEYS",
                "error_message": f"Missing required keys: {', '.join(missing)}",
            }
            if context.logger is not None:
                context.logger.record(
                    "tool.finish",
                    {
                        "tool": definition.name,
                        "input": dict(action_input),
                        "ok": False,
                        "duration_ms": round((perf_counter() - started_at) * 1000, 3),
                        "result": dict(result),
                    },
                    level="standard",
                )
            return result

        if context.logger is not None:
            context.logger.record(
                "tool.start",
                {
                    "tool": definition.name,
                    "description": definition.description,
                    "input": dict(action_input),
                    "metadata": dict(definition.metadata),
                },
                level="verbose",
            )

        try:
            raw_result = definition.handler(dict(action_input), context)
        except Exception as exc:  # noqa: BLE001
            result = {
                "ok": False,
                "tool": definition.name,
                "input": dict(action_input),
                "value": None,
                "error_code": "TOOL_RUNTIME_ERROR",
                "error_message": str(exc),
                "stack_trace": format_exc(),
            }
            if context.logger is not None:
                context.logger.record(
                    "tool.finish",
                    {
                        "tool": definition.name,
                        "input": dict(action_input),
                        "ok": False,
                        "duration_ms": round((perf_counter() - started_at) * 1000, 3),
                        "result": dict(result),
                    },
                    level="standard",
                )
            return result

        if isinstance(raw_result, dict) and "ok" in raw_result:
            result = {
                "tool": definition.name,
                "input": dict(action_input),
                **raw_result,
            }
        else:
            result = {
                "ok": True,
                "tool": definition.name,
                "input": dict(action_input),
                "value": raw_result,
            }

        if context.logger is not None:
            context.logger.record(
                "tool.finish",
                {
                    "tool": definition.name,
                    "input": dict(action_input),
                    "ok": bool(result.get("ok", False)),
                    "duration_ms": round((perf_counter() - started_at) * 1000, 3),
                    "result": dict(result),
                },
                level="standard",
            )
        return result
