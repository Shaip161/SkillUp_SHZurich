"""Minimal example showing how to wire the starter kit for a new project."""

from __future__ import annotations

from starter_kit import (
    AgentLoopConfig,
    CallableLlmClient,
    PromptBuilder,
    StrictLineActionParser,
    ToolDefinition,
    ToolRegistry,
    load_prompt_template,
    init_state,
    run_agent_loop,
)


def _build_demo_llm() -> CallableLlmClient:
    responses = iter(
        [
            "THOUGHT: I should gather one reusable fact first.\n"
            "ACTION: read_brief\n"
            'ACTION_INPUT: {"topic": "demo"}',
            "THOUGHT: I have enough context to answer.\n"
            "ACTION: finish\n"
            'ACTION_INPUT: {"answer": "The starter kit keeps loops, tools, and workflows explicit."}',
        ]
    )
    return CallableLlmClient(lambda _prompt: next(responses))


def _read_brief(action_input, _context):
    topic = action_input["topic"]
    return {"summary": f"Brief for {topic}: keep orchestration explicit and easy to swap."}


def main() -> None:
    state = init_state(
        run_id="demo-run",
        objective="Collect one fact, then return a concise answer.",
        max_steps=3,
    )
    registry = ToolRegistry(
        [
            ToolDefinition(
                name="read_brief",
                description="Load one short project fact.",
                handler=_read_brief,
                required_keys=("topic",),
            )
        ]
    )
    parser = StrictLineActionParser()
    template = load_prompt_template(
        "starter_kit/prompt_templates/hackathon_agent.txt",
        name="demo",
    )
    prompt_builder = PromptBuilder(
        template=template,
        base_sections={
            "USER_CONTEXT": "This is a demo hackathon workflow.",
            "TEAM_STYLE": "Keep answers brief and explicit.",
        },
    )

    final_state = run_agent_loop(
        state=state,
        llm=_build_demo_llm(),
        tool_registry=registry,
        parser=parser,
        prompt_builder=lambda current_state, tools: prompt_builder.build(
            current_state,
            tools,
            extra_sections={"PROJECT_CONTEXT": "Demo reusable starter-kit run."},
        ),
        config=AgentLoopConfig(final_actions=("finish",)),
    )
    print(final_state.to_dict())


if __name__ == "__main__":
    main()
