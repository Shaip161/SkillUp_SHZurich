"""Minimal logging and debug hooks for local development and hackathons."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


LOG_LEVEL_RANKS = {
    "minimal": 0,
    "standard": 1,
    "verbose": 2,
    "debug": 3,
}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class DebugLogger:
    """Collect events in memory and optionally persist them to disk."""

    root_dir: str | Path | None = None
    echo: bool = False
    events: list[dict[str, Any]] = field(default_factory=list)
    observers: list[Any] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._root_path = Path(self.root_dir) if self.root_dir else None
        if self._root_path is not None:
            self._root_path.mkdir(parents=True, exist_ok=True)

    def attach(self, observer: Any) -> Any:
        self.observers.append(observer)
        return observer

    def record(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
        *,
        level: str = "standard",
    ) -> dict[str, Any]:
        event = {
            "event": str(event_type),
            "timestamp": _utc_now(),
            "level": str(level),
            "payload": dict(payload or {}),
        }
        self.events.append(event)
        if self._root_path is not None:
            with (self._root_path / "events.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=True) + "\n")
        if self.echo:
            print(f"[{event['level']}] [{event['event']}] {event['payload']}")
        for observer in list(self.observers):
            if hasattr(observer, "handle_event"):
                observer.handle_event(event)
            elif callable(observer):
                observer(event)
        return event

    def write_json(self, relative_path: str | Path, payload: Any) -> Path | None:
        if self._root_path is None:
            return None
        destination = self._root_path / Path(relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=True)
        return destination
