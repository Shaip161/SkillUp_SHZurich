"""Modular integration layer connecting System A (matchmaking) and System B (learning).

The layer is intentionally thin and owns three responsibilities only:

* **Contracts** (:mod:`integration.contracts`) -- typed, validated schemas for
  System A's output and System B's input. The shared vocabulary.
* **Adapter** (:mod:`integration.adapter`) -- pure transformation from the
  System A contract to the System B contract.
* **Orchestrator** (:mod:`integration.orchestrator`) -- sequences the workflow,
  talking to both systems only through the :mod:`integration.ports` protocols.

Neither subsystem imports this package, and this package imports System B only
inside :class:`integration.providers.TransitionLearningEngine`. That one-way,
single-point coupling is what preserves separation of concerns.

Importing this top-level module pulls in only the pure-Python pieces (contracts,
adapter, orchestrator, logging); System B is *not* required until you actually
instantiate the learning-engine provider.
"""

from __future__ import annotations

from .adapter import (
    LearningObjective,
    build_learning_request,
    build_learning_request_from_gap,
)
from .contracts import (
    ContractError,
    GapResponse,
    LearningRequest,
    MatchmakingOutput,
    validate_gap_response,
    validate_learning_request,
    validate_matchmaking_output,
)
from .logging_utils import CapturingLogger
from .orchestrator import PipelineError, PipelineResult, run_end_to_end
from .ports import LearningEngine, MatchmakingProvider, StructuredLogger

__all__ = [
    "MatchmakingOutput",
    "GapResponse",
    "LearningRequest",
    "ContractError",
    "validate_matchmaking_output",
    "validate_gap_response",
    "validate_learning_request",
    "LearningObjective",
    "build_learning_request",
    "build_learning_request_from_gap",
    "CapturingLogger",
    "MatchmakingProvider",
    "LearningEngine",
    "StructuredLogger",
    "run_end_to_end",
    "PipelineResult",
    "PipelineError",
]
