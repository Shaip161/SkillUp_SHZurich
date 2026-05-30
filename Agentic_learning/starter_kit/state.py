"""Shared state primitives for agent loops and lightweight workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


@dataclass
class StepRecord:
    """One traceable unit of agent execution."""

    step_id: int
    prompt: str = ""
    response: str = ""
    thought: str = ""
    action: str = ""
    action_input: dict[str, Any] = field(default_factory=dict)
    observation: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass
class WorkflowMessage:
    """Simple message envelope for passing signals between nodes or agents."""

    sender: str
    recipient: str = "broadcast"
    kind: str = "note"
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass
class RunState:
    """Compact shared state designed for hackathon iteration speed."""

    run_id: str
    objective: str
    max_steps: int = 8
    current_step: int = 0
    status: str = "running"
    shared: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    history: list[StepRecord] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    messages: list[WorkflowMessage] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


def build_state_summary(state: RunState) -> dict[str, Any]:
    return {
        "run_id": state.run_id,
        "status": state.status,
        "current_step": state.current_step,
        "max_steps": state.max_steps,
        "shared_keys": sorted(state.shared.keys()),
        "output_keys": sorted(state.outputs.keys()),
        "history_count": len(state.history),
        "error_count": len(state.errors),
        "message_count": len(state.messages),
    }


def snapshot_state(state: RunState) -> dict[str, Any]:
    return {
        "summary": build_state_summary(state),
        "shared": _json_safe(dict(state.shared)),
        "outputs": _json_safe(dict(state.outputs)),
    }


def _diff_mapping(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    added = {key: after[key] for key in after.keys() - before.keys()}
    removed = sorted(before.keys() - after.keys())
    changed = {
        key: {"before": before[key], "after": after[key]}
        for key in before.keys() & after.keys()
        if before[key] != after[key]
    }
    return {
        "added": _json_safe(added),
        "removed": removed,
        "changed": _json_safe(changed),
    }


def diff_state_snapshots(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_summary = dict(before.get("summary", {}) or {})
    after_summary = dict(after.get("summary", {}) or {})
    return {
        "status_changed": before_summary.get("status") != after_summary.get("status"),
        "step_changed": before_summary.get("current_step") != after_summary.get("current_step"),
        "error_count_delta": int(after_summary.get("error_count", 0)) - int(before_summary.get("error_count", 0)),
        "history_count_delta": int(after_summary.get("history_count", 0)) - int(before_summary.get("history_count", 0)),
        "message_count_delta": int(after_summary.get("message_count", 0)) - int(before_summary.get("message_count", 0)),
        "shared": _diff_mapping(
            dict(before.get("shared", {}) or {}),
            dict(after.get("shared", {}) or {}),
        ),
        "outputs": _diff_mapping(
            dict(before.get("outputs", {}) or {}),
            dict(after.get("outputs", {}) or {}),
        ),
    }


def init_state(
    run_id: str,
    objective: str,
    *,
    max_steps: int = 8,
    shared: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> RunState:
    return RunState(
        run_id=run_id,
        objective=objective,
        max_steps=max_steps,
        shared=dict(shared or {}),
        metadata=dict(metadata or {}),
    )


def append_step_record(state: RunState, step_record: StepRecord | dict[str, Any]) -> None:
    if isinstance(step_record, StepRecord):
        state.history.append(step_record)
        return
    state.history.append(StepRecord(**dict(step_record)))


def append_error(state: RunState, error_record: dict[str, Any]) -> None:
    record = dict(error_record)
    record.setdefault("timestamp", utc_now())
    state.errors.append(record)


def merge_shared(state: RunState, updates: dict[str, Any]) -> None:
    state.shared.update(dict(updates))


def set_output(state: RunState, key: str, value: Any) -> None:
    state.outputs[str(key)] = value


def publish_message(state: RunState, message: WorkflowMessage | dict[str, Any]) -> None:
    if isinstance(message, WorkflowMessage):
        state.messages.append(message)
        return
    state.messages.append(WorkflowMessage(**dict(message)))


def advance_step(state: RunState, increment: int = 1) -> None:
    if increment < 0:
        raise ValueError("increment must be non-negative")
    state.current_step += increment
