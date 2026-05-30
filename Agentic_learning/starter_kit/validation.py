"""Structured output parsing and small validation helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable


def validate_required_keys(payload: dict[str, Any], required_keys: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for key in required_keys:
        if key not in payload:
            missing.append(str(key))
    return missing


@dataclass
class ParsedAction:
    ok: bool
    thought: str | None = None
    action: str | None = None
    action_input: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None
    raw_output: str = ""


class StrictLineActionParser:
    """Configurable strict parser for simple line-based agent protocols."""

    def __init__(
        self,
        *,
        thought_field: str = "THOUGHT",
        action_field: str = "ACTION",
        action_input_field: str = "ACTION_INPUT",
        required_action_input_keys: tuple[str, ...] = (),
    ) -> None:
        self.thought_field = thought_field
        self.action_field = action_field
        self.action_input_field = action_input_field
        self.required_action_input_keys = required_action_input_keys

    def _error(self, code: str, message: str, raw_output: str) -> ParsedAction:
        return ParsedAction(
            ok=False,
            error_code=code,
            error_message=message,
            raw_output=raw_output,
        )

    def parse(self, text: str) -> ParsedAction:
        lines = [line.rstrip()
                 for line in str(text).strip().splitlines() if line.strip()]
        if len(lines) != 3:
            return self._error(
                "PARSE_ERROR",
                "Model output must contain exactly 3 non-empty lines.",
                text,
            )

        expected_prefixes = [
            f"{self.thought_field}:",
            f"{self.action_field}:",
            f"{self.action_input_field}:",
        ]
        for line, prefix in zip(lines, expected_prefixes, strict=True):
            if not line.startswith(prefix):
                return self._error(
                    "PARSE_ERROR",
                    f"Expected line prefix '{prefix}'.",
                    text,
                )

        thought = lines[0][len(expected_prefixes[0]):].strip()
        action = lines[1][len(expected_prefixes[1]):].strip()
        action_input_text = lines[2][len(expected_prefixes[2]):].strip()
        if not thought:
            return self._error("PARSE_ERROR", f"{self.thought_field} cannot be empty.", text)
        if not action:
            return self._error("PARSE_ERROR", f"{self.action_field} cannot be empty.", text)

        try:
            action_input = json.loads(action_input_text)
        except json.JSONDecodeError as exc:
            return self._error(
                "INVALID_JSON",
                f"{self.action_input_field} is not valid JSON: {exc.msg}",
                text,
            )

        if not isinstance(action_input, dict):
            return self._error(
                "PARSE_ERROR",
                f"{self.action_input_field} must decode to a JSON object.",
                text,
            )

        missing = validate_required_keys(
            action_input, self.required_action_input_keys)
        if missing:
            return self._error(
                "PARSE_ERROR",
                f"{self.action_input_field} is missing required keys: {', '.join(missing)}",
                text,
            )

        return ParsedAction(
            ok=True,
            thought=thought,
            action=action,
            action_input=action_input,
            raw_output=text,
        )
