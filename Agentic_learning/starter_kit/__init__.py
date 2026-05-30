"""Minimal starter-kit primitives required by the backend learning core."""

from .prompts import PromptTemplate
from .state import (
    RunState,
    StepRecord,
    WorkflowMessage,
    advance_step,
    append_error,
    append_step_record,
    build_state_summary,
    diff_state_snapshots,
    init_state,
    merge_shared,
    publish_message,
    set_output,
    snapshot_state,
)
from .workflow import NodeResult, WorkflowNode, WorkflowRunner, WorkflowServices

__all__ = [
    "NodeResult",
    "PromptTemplate",
    "RunState",
    "StepRecord",
    "WorkflowMessage",
    "WorkflowNode",
    "WorkflowRunner",
    "WorkflowServices",
    "advance_step",
    "append_error",
    "append_step_record",
    "build_state_summary",
    "diff_state_snapshots",
    "init_state",
    "merge_shared",
    "publish_message",
    "set_output",
    "snapshot_state",
]
