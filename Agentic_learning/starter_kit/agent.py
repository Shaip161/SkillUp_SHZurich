"""Generic bounded agent loop with explicit seams for prompts, tools, and hooks."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from traceback import format_exc
from typing import Any, Callable

from .logging import DebugLogger
from .prompts import build_agent_prompt
from .state import (
    RunState,
    StepRecord,
    advance_step,
    append_error,
    append_step_record,
    build_state_summary,
    diff_state_snapshots,
    merge_shared,
    set_output,
    snapshot_state,
)
from .tools import ToolContext, ToolRegistry
from .validation import ParsedAction, StrictLineActionParser

PromptBuilder = Callable[[RunState, ToolRegistry], str]


@dataclass
class AgentLoopConfig:
    max_parse_errors: int = 2
    final_actions: tuple[str, ...] = ("finish", "respond")
    final_output_key: str = "final_response"


@dataclass
class AgentHooks:
    before_step: Callable[[RunState, int], None] | None = None
    after_parse: Callable[[RunState, ParsedAction], None] | None = None
    after_tool: Callable[[RunState, ParsedAction,
                          dict[str, Any]], dict[str, Any] | None] | None = None


def _default_prompt_builder(state: RunState, tool_registry: ToolRegistry) -> str:
    return build_agent_prompt(state, tool_registry)


def _agent_name(state: RunState) -> str:
    return str(state.metadata.get("agent_name") or state.run_id)


def _record_step(
    state: RunState,
    *,
    step_id: int,
    prompt_text: str,
    raw_output: str,
    parsed: ParsedAction,
    observation: dict[str, Any],
    status: str,
) -> None:
    append_step_record(
        state,
        StepRecord(
            step_id=step_id,
            prompt=prompt_text,
            response=raw_output,
            thought=parsed.thought or "",
            action=parsed.action or "",
            action_input=dict(parsed.action_input or {}),
            observation=dict(observation),
            status=status,
        ),
    )


def run_agent_loop(
    *,
    state: RunState,
    llm: Any,
    tool_registry: ToolRegistry,
    parser: StrictLineActionParser | None = None,
    prompt_builder: PromptBuilder | None = None,
    logger: DebugLogger | None = None,
    hooks: AgentHooks | None = None,
    config: AgentLoopConfig | None = None,
    services: dict[str, Any] | None = None,
) -> RunState:
    """Run a bounded explicit loop that is easy to debug and replace in parts."""

    parser = parser or StrictLineActionParser()
    prompt_builder = prompt_builder or _default_prompt_builder
    hooks = hooks or AgentHooks()
    config = config or AgentLoopConfig()
    parse_failures = 0
    runtime_services = dict(services or {})
    agent_name = _agent_name(state)

    if logger is not None:
        logger.record(
            "agent.start",
            {
                "agent": agent_name,
                "state_summary": build_state_summary(state),
                "tools": tool_registry.describe(),
            },
            level="standard",
        )

    while state.current_step < state.max_steps and state.status == "running":
        step_id = state.current_step + 1
        step_started_at = perf_counter()
        before_snapshot = snapshot_state(state)
        if hooks.before_step is not None:
            hooks.before_step(state, step_id)

        if logger is not None:
            logger.record(
                "agent.step.start",
                {
                    "agent": agent_name,
                    "step_id": step_id,
                    "state_summary": before_snapshot["summary"],
                    "tool_names": tool_registry.names(),
                },
                level="standard",
            )

        prompt_text = prompt_builder(state, tool_registry)
        if logger is not None:
            logger.record(
                "agent.prompt",
                {
                    "agent": agent_name,
                    "step_id": step_id,
                    "prompt": prompt_text,
                    "tool_descriptions": tool_registry.describe(),
                    "state_summary": before_snapshot["summary"],
                },
                level="verbose",
            )

        try:
            raw_output = llm.generate(prompt_text, metadata={
                                      "step_id": step_id, "run_id": state.run_id})
        except Exception as exc:  # noqa: BLE001
            append_error(
                state,
                {
                    "error_code": "LLM_ERROR",
                    "error_message": str(exc),
                    "step_id": step_id,
                    "stack_trace": format_exc(),
                },
            )
            if logger is not None:
                logger.record(
                    "agent.error",
                    {
                        "agent": agent_name,
                        "step_id": step_id,
                        "error_code": "LLM_ERROR",
                        "error_message": str(exc),
                        "stack_trace": format_exc(),
                        "prompt": prompt_text,
                    },
                    level="minimal",
                )
            state.status = "failed"
            break

        if logger is not None:
            logger.record(
                "agent.response",
                {
                    "agent": agent_name,
                    "step_id": step_id,
                    "response": raw_output,
                },
                level="verbose",
            )

        parsed = parser.parse(raw_output)
        if hooks.after_parse is not None:
            hooks.after_parse(state, parsed)

        if logger is not None:
            logger.record(
                "agent.parsed",
                {
                    "agent": agent_name,
                    "step_id": step_id,
                    "ok": parsed.ok,
                    "thought": parsed.thought,
                    "action": parsed.action,
                    "action_input": dict(parsed.action_input or {}),
                    "error_code": parsed.error_code,
                    "error_message": parsed.error_message,
                },
                level="debug",
            )

        if not parsed.ok:
            parse_failures += 1
            observation = {
                "ok": False,
                "error_code": parsed.error_code,
                "error_message": parsed.error_message,
            }
            append_error(
                state,
                {
                    "error_code": parsed.error_code,
                    "error_message": parsed.error_message,
                    "step_id": step_id,
                },
            )
            _record_step(
                state,
                step_id=step_id,
                prompt_text=prompt_text,
                raw_output=raw_output,
                parsed=parsed,
                observation=observation,
                status=parsed.error_code or "PARSE_ERROR",
            )
            advance_step(state)
            after_snapshot = snapshot_state(state)
            if logger is not None:
                logger.record(
                    "agent.step.finish",
                    {
                        "agent": agent_name,
                        "step_id": step_id,
                        "status": parsed.error_code or "PARSE_ERROR",
                        "duration_ms": round((perf_counter() - step_started_at) * 1000, 3),
                        "state_summary": after_snapshot["summary"],
                        "state_diff": diff_state_snapshots(before_snapshot, after_snapshot),
                        "observation": observation,
                    },
                    level="standard",
                )
            if parse_failures >= config.max_parse_errors:
                state.status = "failed"
                break
            continue

        parse_failures = 0
        action_name = str(parsed.action or "").strip()
        action_input = dict(parsed.action_input or {})

        if action_name in config.final_actions:
            observation = {"ok": True, "final": True, "value": action_input}
            set_output(state, config.final_output_key, action_input)
            _record_step(
                state,
                step_id=step_id,
                prompt_text=prompt_text,
                raw_output=raw_output,
                parsed=parsed,
                observation=observation,
                status="completed",
            )
            advance_step(state)
            state.status = "completed"
            after_snapshot = snapshot_state(state)
            if logger is not None:
                logger.record(
                    "agent.step.finish",
                    {
                        "agent": agent_name,
                        "step_id": step_id,
                        "status": "completed",
                        "duration_ms": round((perf_counter() - step_started_at) * 1000, 3),
                        "state_summary": after_snapshot["summary"],
                        "state_diff": diff_state_snapshots(before_snapshot, after_snapshot),
                        "observation": observation,
                    },
                    level="standard",
                )
            break

        tool_result = tool_registry.run(
            action_name,
            action_input,
            ToolContext(state=state, logger=logger, services=runtime_services),
        )
        updates: dict[str, Any] = {
            "last_action": {"name": action_name, "input": action_input},
            "last_tool_result": dict(tool_result),
        }
        if hooks.after_tool is not None:
            custom_updates = hooks.after_tool(state, parsed, tool_result)
            if custom_updates:
                updates.update(custom_updates)
        merge_shared(state, updates)

        if not tool_result.get("ok", False):
            append_error(
                state,
                {
                    "error_code": str(tool_result.get("error_code") or "TOOL_ERROR"),
                    "error_message": str(tool_result.get("error_message") or "Tool execution failed."),
                    "step_id": step_id,
                    "tool": action_name,
                },
            )

        _record_step(
            state,
            step_id=step_id,
            prompt_text=prompt_text,
            raw_output=raw_output,
            parsed=parsed,
            observation=tool_result,
            status="tool_ok" if tool_result.get("ok", False) else "tool_error",
        )
        advance_step(state)
        after_snapshot = snapshot_state(state)
        if logger is not None:
            logger.record(
                "agent.step.finish",
                {
                    "agent": agent_name,
                    "step_id": step_id,
                    "status": "tool_ok" if tool_result.get("ok", False) else "tool_error",
                    "duration_ms": round((perf_counter() - step_started_at) * 1000, 3),
                    "state_summary": after_snapshot["summary"],
                    "state_diff": diff_state_snapshots(before_snapshot, after_snapshot),
                    "observation": tool_result,
                },
                level="standard",
            )

    if state.current_step >= state.max_steps and state.status == "running":
        state.status = "max_steps_reached"
    if logger is not None:
        logger.record(
            "agent.finish",
            {
                "agent": agent_name,
                "status": state.status,
                "state_summary": build_state_summary(state),
                "outputs": dict(state.outputs),
                "errors": list(state.errors),
            },
            level="standard",
        )
    return state
