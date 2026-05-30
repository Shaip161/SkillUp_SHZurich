"""Sequential and lightweight multi-agent workflow orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from traceback import format_exc
from typing import Any, Callable

from .state import (
    RunState,
    WorkflowMessage,
    _json_safe,
    append_error,
    build_state_summary,
    diff_state_snapshots,
    merge_shared,
    publish_message,
    set_output,
    snapshot_state,
)

NodeHandler = Callable[[RunState, "WorkflowServices"], "NodeResult"]


def _serialize_node_io(payload: dict[str, Any]) -> dict[str, Any]:
    return _json_safe(payload)


@dataclass
class WorkflowServices:
    llm: Any = None
    tools: Any = None
    retriever: Any = None
    api_client: Any = None
    logger: Any = None
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeResult:
    updates: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    next_node: str | None = None
    emitted_messages: list[WorkflowMessage] = field(default_factory=list)
    stop: bool = False
    status: str | None = None


@dataclass
class WorkflowNode:
    name: str
    handler: NodeHandler
    default_next: str | None = None
    description: str = ""


class WorkflowRunner:
    def __init__(
        self,
        nodes: list[WorkflowNode],
        *,
        max_transitions: int = 24,
        name: str = "workflow",
    ) -> None:
        self._nodes = {node.name: node for node in nodes}
        self.max_transitions = max_transitions
        self.name = name

    def describe_graph(self) -> dict[str, Any]:
        nodes = []
        edges = []
        for node_name, node in self._nodes.items():
            nodes.append(
                {
                    "name": node_name,
                    "description": node.description,
                    "default_next": node.default_next,
                }
            )
            if node.default_next:
                edges.append({"from": node_name, "to": node.default_next})
        return {
            "workflow": self.name,
            "nodes": nodes,
            "edges": edges,
        }

    def run(
        self,
        state: RunState,
        *,
        start_at: str,
        services: WorkflowServices | None = None,
    ) -> RunState:
        runtime = services or WorkflowServices()
        current_node_name = start_at
        transitions = 0
        workflow_started_at = perf_counter()

        if runtime.logger is not None:
            runtime.logger.record(
                "workflow.start",
                {
                    "workflow": self.name,
                    "start_at": start_at,
                    "state_summary": build_state_summary(state),
                },
                level="standard",
            )
            runtime.logger.record(
                "workflow.graph",
                {
                    "workflow": self.name,
                    "graph": self.describe_graph(),
                    "current_node": start_at,
                },
                level="verbose",
            )

        while current_node_name:
            if transitions >= self.max_transitions:
                append_error(
                    state,
                    {
                        "error_code": "MAX_TRANSITIONS_REACHED",
                        "error_message": "Workflow exceeded the configured transition limit.",
                    },
                )
                state.status = "failed"
                break

            node = self._nodes.get(current_node_name)
            if node is None:
                append_error(
                    state,
                    {
                        "error_code": "UNKNOWN_NODE",
                        "error_message": f"Workflow node '{current_node_name}' is not registered.",
                    },
                )
                state.status = "failed"
                break

            before_snapshot = snapshot_state(state)
            node_started_at = perf_counter()
            if runtime.logger is not None:
                runtime.logger.record(
                    "workflow.node.start",
                    {
                        "workflow": self.name,
                        "node": node.name,
                        "transition": transitions + 1,
                        "state_summary": before_snapshot["summary"],
                    },
                    level="standard",
                )
                runtime.logger.record(
                    "workflow.node.input",
                    {
                        "workflow": self.name,
                        "node": node.name,
                        "transition": transitions + 1,
                        "input": _serialize_node_io(
                            {
                                "objective": state.objective,
                                "shared": before_snapshot["shared"],
                                "outputs": before_snapshot["outputs"],
                                "metadata": dict(state.metadata),
                                "messages": [message.to_dict() for message in state.messages],
                            }
                        ),
                    },
                    level="debug",
                )

            try:
                result = node.handler(state, runtime)
            except Exception as exc:  # noqa: BLE001
                append_error(
                    state,
                    {
                        "error_code": "NODE_RUNTIME_ERROR",
                        "error_message": str(exc),
                        "node": node.name,
                        "stack_trace": format_exc(),
                    },
                )
                if runtime.logger is not None:
                    runtime.logger.record(
                        "workflow.node.error",
                        {
                            "workflow": self.name,
                            "node": node.name,
                            "error_message": str(exc),
                            "stack_trace": format_exc(),
                            "state_summary": before_snapshot["summary"],
                        },
                        level="minimal",
                    )
                state.status = "failed"
                break

            merge_shared(state, result.updates)
            for key, value in result.outputs.items():
                set_output(state, key, value)
            for message in result.emitted_messages:
                publish_message(state, message)

            if runtime.logger is not None:
                runtime.logger.record(
                    "workflow.node.output",
                    {
                        "workflow": self.name,
                        "node": node.name,
                        "transition": transitions + 1,
                        "output": _serialize_node_io(
                            {
                                "updates": result.updates,
                                "outputs": result.outputs,
                                "emitted_messages": [message.to_dict() for message in result.emitted_messages],
                                "next_node": result.next_node or node.default_next,
                                "stop": result.stop,
                                "status": result.status or ("completed" if result.stop else "success"),
                            }
                        ),
                    },
                    level="debug",
                )

            if runtime.logger is not None:
                after_snapshot = snapshot_state(state)
                runtime.logger.record(
                    "workflow.node.finish",
                    {
                        "workflow": self.name,
                        "node": node.name,
                        "next_node": result.next_node or node.default_next,
                        "stop": result.stop,
                        "status": result.status or ("completed" if result.stop else "success"),
                        "duration_ms": round((perf_counter() - node_started_at) * 1000, 3),
                        "state_summary": after_snapshot["summary"],
                        "state_diff": diff_state_snapshots(before_snapshot, after_snapshot),
                    },
                    level="standard",
                )

            transitions += 1
            if result.stop:
                state.status = result.status or "completed"
                break
            current_node_name = result.next_node if result.next_node is not None else node.default_next
        else:
            if state.status == "running":
                state.status = "completed"

        if not current_node_name and state.status == "running":
            state.status = "completed"
        if runtime.logger is not None:
            runtime.logger.record(
                "workflow.finish",
                {
                    "workflow": self.name,
                    "status": state.status,
                    "transitions": transitions,
                    "duration_ms": round((perf_counter() - workflow_started_at) * 1000, 3),
                    "state_summary": build_state_summary(state),
                },
                level="standard",
            )
        return state
