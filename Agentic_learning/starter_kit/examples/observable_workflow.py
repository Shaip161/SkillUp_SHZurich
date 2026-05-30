"""Observable starter-kit workflow demonstrating CLI-first debugging output."""

from __future__ import annotations

import os

from starter_kit import (
    AgentLoopConfig,
    CallableLlmClient,
    DebugLogger,
    InMemoryRetriever,
    NodeResult,
    ObservabilityConfig,
    PromptBuilder,
    StrictLineActionParser,
    ToolDefinition,
    ToolRegistry,
    WorkflowNode,
    WorkflowRunner,
    WorkflowServices,
    attach_cli_observer,
    init_state,
    load_prompt_template,
    run_agent_loop,
)


def _build_demo_llm() -> CallableLlmClient:
    responses = iter(
        [
            "THOUGHT: I should inspect the retrieved context before answering.\n"
            "ACTION: summarize_context\n"
            'ACTION_INPUT: {"focus": "observability"}',
            "THOUGHT: I have enough evidence to summarize the system behavior.\n"
            "ACTION: finish\n"
            'ACTION_INPUT: {"answer": "Use explicit workflow nodes, log every retrieval and tool call, and diff shared state after each step."}',
        ]
    )
    return CallableLlmClient(lambda _prompt: next(responses))


def _summarize_context(action_input, context):
    focus = action_input["focus"]
    retrieved_context = list(context.state.shared.get("retrieved_context", []))
    return {
        "focus": focus,
        "chunks_used": len(retrieved_context),
        "summary": " | ".join(retrieved_context),
    }


def _build_tool_registry() -> ToolRegistry:
    return ToolRegistry(
        [
            ToolDefinition(
                name="summarize_context",
                description="Summarize the retrieved context relevant to the current objective.",
                handler=_summarize_context,
                required_keys=("focus",),
            )
        ]
    )


def _retrieve_context(state, services):
    query = "transparent workflow observability for agent systems"
    results = services.retriever.search(query, limit=2)
    selected_context = [item.text for item in results]
    return NodeResult(
        updates={
            "retrieval_query": query,
            "retrieved_context": selected_context,
        },
        outputs={
            "retrieved_ids": [item.item_id for item in results],
        },
    )


def _run_agent(state, services):
    template = load_prompt_template(
        "starter_kit/prompt_templates/transparent_debug_agent.txt",
        name="observable_demo",
    )
    prompt_builder = PromptBuilder(
        template=template,
        base_sections={
            "USER_CONTEXT": "You are debugging an AI workflow during a hackathon.",
        },
    )
    final_state = run_agent_loop(
        state=state,
        llm=services.llm,
        tool_registry=services.tools,
        parser=StrictLineActionParser(),
        logger=services.logger,
        prompt_builder=lambda current_state, registry: prompt_builder.build(
            current_state,
            registry,
            extra_sections={
                "RETRIEVED_CONTEXT": current_state.shared.get("retrieved_context", []),
                "WORKFLOW_NAME": current_state.metadata.get("workflow_name", "workflow"),
            },
        ),
        config=AgentLoopConfig(final_actions=("finish",)),
    )
    return NodeResult(
        updates={"agent_status": final_state.status},
        outputs={"agent_result": final_state.outputs.get(
            "final_response", {})},
    )


def _finalize(state, _services):
    return NodeResult(
        outputs={"final_report": state.outputs.get("agent_result", {})},
        stop=True,
        status="completed",
    )


def main() -> None:
    logger = DebugLogger()
    attach_cli_observer(
        logger,
        ObservabilityConfig(
            mode=os.environ.get("STARTER_KIT_LOG_MODE", "standard"),
            max_chars=900,
            show_prompt_sections=True,
            show_state_diffs=True,
        ),
    )

    retriever = InMemoryRetriever(
        [
            {
                "item_id": "note-1",
                "text": "Log workflow transitions with node names, statuses, durations, and a compact state summary.",
                "metadata": {"source": "playbook", "topic": "workflow"},
            },
            {
                "item_id": "note-2",
                "text": "Trace retrieval inputs, selected chunks, similarity scores, and downstream prompt context.",
                "metadata": {"source": "playbook", "topic": "retrieval"},
            },
            {
                "item_id": "note-3",
                "text": "Keep tool traces explicit so failures show arguments, durations, and structured errors immediately.",
                "metadata": {"source": "playbook", "topic": "tools"},
            },
        ],
        logger=logger,
        name="demo_briefing",
    )

    state = init_state(
        run_id="starter-kit-demo",
        objective="Inspect the workflow, tool usage, retrieval context, and final answer in one transparent run.",
        max_steps=3,
        metadata={
            "workflow_name": "transparent_debug_workflow",
            "agent_name": "briefing_agent",
        },
    )
    registry = _build_tool_registry()
    runner = WorkflowRunner(
        [
            WorkflowNode(name="retrieve_context",
                         handler=_retrieve_context, default_next="run_agent"),
            WorkflowNode(name="run_agent", handler=_run_agent,
                         default_next="finalize"),
            WorkflowNode(name="finalize", handler=_finalize),
        ],
        name="transparent_debug_workflow",
    )
    services = WorkflowServices(
        llm=_build_demo_llm(),
        tools=registry,
        retriever=retriever,
        logger=logger,
    )
    runner.run(state, start_at="retrieve_context", services=services)


if __name__ == "__main__":
    main()
