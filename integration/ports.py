"""Ports (interfaces) that keep the integration layer decoupled from both systems.

The orchestrator depends only on these :class:`typing.Protocol` definitions,
never on concrete System A / System B classes. Any object that *structurally*
matches a protocol can be plugged in -- a real backend client, an in-process
call, or a test double -- which is what makes the integration "replaceable and
extensible" and avoids circular dependencies between the subsystems.

Concrete implementations live in :mod:`integration.providers`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

from .contracts import LearningRequest, MatchmakingOutput


@runtime_checkable
class StructuredLogger(Protocol):
    """Anything that can record a structured event.

    Deliberately matches System B's logger duck-type (``.record(event_type,
    payload, level=...)``) so the very same logger instance can be threaded
    into System B's ``WorkflowServices`` and capture both layers' events.
    """

    def record(
        self,
        event_type: str,
        payload: Mapping[str, Any],
        *,
        level: str = "standard",
    ) -> None: ...


@runtime_checkable
class MatchmakingProvider(Protocol):
    """Port abstracting System A (the Job Matchmaking Engine).

    Implementations take raw inputs (a CV and job listings) and return a payload
    that conforms to the :class:`MatchmakingOutput` contract -- either the model
    itself or a plain mapping the orchestrator will validate. The orchestrator
    never assumes *how* matching happens (HTTP call, in-process, canned mock).
    """

    def run(self, *, cv: Any, jobs: Any) -> Mapping[str, Any] | MatchmakingOutput: ...


@runtime_checkable
class LearningEngine(Protocol):
    """Port abstracting System B (the Learning Agent System).

    Implementations accept a validated :class:`LearningRequest` and return the
    learning output (e.g. a generated curriculum) as a mapping.
    """

    def generate(self, request: LearningRequest) -> Mapping[str, Any]: ...
