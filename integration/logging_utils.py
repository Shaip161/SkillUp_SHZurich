"""Structured logging for the integration boundary.

Provides a single :class:`CapturingLogger` that satisfies the
:class:`integration.ports.StructuredLogger` protocol (and therefore also
System B's logger duck-type). It records every event in memory so tests can
assert on payloads, optionally echoes a compact line to stdout for live
debugging, and offers helpers to retrieve the three payloads we most want
visibility into:

* the raw matchmaking output (System A),
* the transformed payload (the adapter's :class:`LearningRequest`),
* the final agent input handed to System B.

Event levels mirror System B's convention ("minimal" .. "verbose"); the logger
keeps everything regardless of level so nothing is lost during debugging.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

# Canonical event types emitted by the orchestrator. Centralised so producers
# and consumers (tests, dashboards) share one vocabulary.
EVENT_MATCHMAKING_RAW = "integration.matchmaking.raw_output"
EVENT_MATCHMAKING_VALIDATED = "integration.matchmaking.validated"
EVENT_TRANSFORMED_PAYLOAD = "integration.adapter.transformed_payload"
EVENT_AGENT_INPUT = "integration.learning.agent_input"
EVENT_AGENT_OUTPUT = "integration.learning.agent_output"
EVENT_SCHEMA_MISMATCH = "integration.error.schema_mismatch"
EVENT_PIPELINE_WARNING = "integration.pipeline.warning"


def _json_safe(value: Any) -> Any:
    """Best-effort conversion of arbitrary values to JSON-serialisable form."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "model_dump"):  # pydantic model
        return _json_safe(value.model_dump())
    if hasattr(value, "to_dict"):  # System B dataclasses
        return _json_safe(value.to_dict())
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return str(value)


@dataclass
class LogEvent:
    """One recorded structured event."""

    event_type: str
    payload: dict[str, Any]
    level: str = "standard"

    def to_dict(self) -> dict[str, Any]:
        return {"event_type": self.event_type, "level": self.level, "payload": self.payload}


@dataclass
class CapturingLogger:
    """In-memory structured logger usable by both the orchestrator and System B.

    Set ``echo=True`` to also print a one-line summary of each event to stdout.
    """

    echo: bool = False
    events: list[LogEvent] = field(default_factory=list)

    # -- StructuredLogger protocol -----------------------------------------
    def record(
        self,
        event_type: str,
        payload: Mapping[str, Any],
        *,
        level: str = "standard",
    ) -> None:
        event = LogEvent(event_type=event_type, payload=_json_safe(dict(payload)), level=level)
        self.events.append(event)
        if self.echo:
            preview = json.dumps(event.payload, ensure_ascii=True)
            if len(preview) > 200:
                preview = preview[:197] + "..."
            print(f"[{level:>8}] {event_type}: {preview}")

    # -- Inspection helpers ------------------------------------------------
    def events_of_type(self, event_type: str) -> list[LogEvent]:
        return [event for event in self.events if event.event_type == event_type]

    def last_payload(self, event_type: str) -> dict[str, Any] | None:
        matches = self.events_of_type(event_type)
        return matches[-1].payload if matches else None

    @property
    def raw_matchmaking_payload(self) -> dict[str, Any] | None:
        return self.last_payload(EVENT_MATCHMAKING_RAW)

    @property
    def transformed_payload(self) -> dict[str, Any] | None:
        return self.last_payload(EVENT_TRANSFORMED_PAYLOAD)

    @property
    def agent_input_payload(self) -> dict[str, Any] | None:
        return self.last_payload(EVENT_AGENT_INPUT)

    def dump(self) -> list[dict[str, Any]]:
        """Return every event as a list of plain dicts (for files/assertions)."""
        return [event.to_dict() for event in self.events]
