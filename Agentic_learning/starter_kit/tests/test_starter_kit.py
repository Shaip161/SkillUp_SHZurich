from starter_kit.agent import AgentLoopConfig, run_agent_loop
from starter_kit.llm import CallableLlmClient, build_responses_create_kwargs
from starter_kit.logging import DebugLogger
from starter_kit.prompts import PromptBuilder, PromptCatalog, get_default_prompt_template
from starter_kit.retrieval import InMemoryRetriever
from starter_kit.state import WorkflowMessage, init_state
from starter_kit.tools import ToolDefinition, ToolRegistry
from starter_kit.validation import StrictLineActionParser
from starter_kit.workflow import NodeResult, WorkflowNode, WorkflowRunner, WorkflowServices


def test_agent_loop_runs_tool_then_finishes():
    responses = iter(
        [
            "THOUGHT: I need one lookup first.\n"
            "ACTION: fetch_note\n"
            'ACTION_INPUT: {"topic": "architecture"}',
            "THOUGHT: I can answer now.\n"
            "ACTION: finish\n"
            'ACTION_INPUT: {"answer": "Keep the loop explicit and the state shared."}',
        ]
    )

    llm = CallableLlmClient(lambda _prompt: next(responses))
    registry = ToolRegistry(
        [
            ToolDefinition(
                name="fetch_note",
                description="Fetch one note by topic.",
                required_keys=("topic",),
                handler=lambda action_input, _context: {
                    "note": f"lookup:{action_input['topic']}"},
            )
        ]
    )
    state = init_state("run-1", "Answer a small question.", max_steps=3)
    logger = DebugLogger()

    final_state = run_agent_loop(
        state=state,
        llm=llm,
        tool_registry=registry,
        parser=StrictLineActionParser(),
        logger=logger,
        config=AgentLoopConfig(final_actions=("finish",)),
    )

    assert final_state.status == "completed"
    assert final_state.outputs["final_response"]["answer"] == "Keep the loop explicit and the state shared."
    assert final_state.shared["last_tool_result"]["value"]["note"] == "lookup:architecture"
    assert len(final_state.history) == 2
    event_names = [event["event"] for event in logger.events]
    assert event_names == [
        "agent.start",
        "agent.step.start",
        "agent.prompt",
        "agent.response",
        "agent.parsed",
        "tool.start",
        "tool.finish",
        "agent.step.finish",
        "agent.step.start",
        "agent.prompt",
        "agent.response",
        "agent.parsed",
        "agent.step.finish",
        "agent.finish",
    ]
    assert logger.events[6]["payload"]["duration_ms"] >= 0.0


def test_tool_registry_validates_required_keys():
    registry = ToolRegistry(
        [
            ToolDefinition(
                name="search_docs",
                description="Search docs.",
                required_keys=("query",),
                handler=lambda action_input, _context: action_input,
            )
        ]
    )
    result = registry.run("search_docs", {}, context=type(
        "Context", (), {"logger": None})())

    assert result["ok"] is False
    assert result["error_code"] == "MISSING_REQUIRED_KEYS"


def test_workflow_runner_supports_sequential_nodes_and_messages():
    def plan_node(state, _services):
        return NodeResult(
            updates={"plan": "collect then summarize"},
            emitted_messages=[WorkflowMessage(
                sender="planner", recipient="worker", kind="task", payload={"id": 1})],
        )

    def worker_node(state, _services):
        assert state.shared["plan"] == "collect then summarize"
        assert state.messages[0].payload["id"] == 1
        return NodeResult(outputs={"result": "done"}, stop=True, status="completed")

    runner = WorkflowRunner(
        [
            WorkflowNode(name="plan", handler=plan_node, default_next="work"),
            WorkflowNode(name="work", handler=worker_node),
        ]
    )
    state = init_state("wf-1", "Run a two-node flow.")

    final_state = runner.run(state, start_at="plan",
                             services=WorkflowServices())

    assert final_state.status == "completed"
    assert final_state.outputs["result"] == "done"
    assert len(final_state.messages) == 1


def test_in_memory_retriever_ranks_by_token_overlap():
    logger = DebugLogger()
    retriever = InMemoryRetriever(
        [
            {"item_id": "a", "text": "agent loops with shared state"},
            {"item_id": "b", "text": "prompt templates and tool registry"},
        ],
        logger=logger,
    )

    results = retriever.search("shared state loop", limit=2)

    assert [item.item_id for item in results] == ["a"]
    assert results[0].score == 3.0
    assert logger.events[-1]["event"] == "retrieval.search"
    assert logger.events[-1]["payload"]["result_count"] == 1


def test_build_responses_create_kwargs_omits_temperature_for_gpt5_family():
    kwargs = build_responses_create_kwargs(
        model_name="gpt-5.5",
        prompt_text="hello",
        temperature=0.2,
    )

    assert kwargs == {"model": "gpt-5.5", "input": "hello"}


def test_workflow_runner_emits_state_diff_events():
    logger = DebugLogger()

    def plan_node(state, _services):
        return NodeResult(updates={"plan": "inspect"})

    def final_node(state, _services):
        return NodeResult(outputs={"result": state.shared["plan"]}, stop=True, status="completed")

    runner = WorkflowRunner(
        [
            WorkflowNode(name="plan", handler=plan_node, default_next="final"),
            WorkflowNode(name="final", handler=final_node),
        ],
        name="observable_workflow",
    )
    state = init_state("wf-observable", "Inspect workflow state.")

    final_state = runner.run(
        state,
        start_at="plan",
        services=WorkflowServices(logger=logger),
    )

    assert final_state.status == "completed"
    finish_events = [
        event for event in logger.events if event["event"] == "workflow.node.finish"]
    assert finish_events[0]["payload"]["state_diff"]["shared"]["added"] == {
        "plan": "inspect"}


def test_prompt_builder_loads_builtin_template_and_builds_prompt():
    template = get_default_prompt_template()
    state = init_state("prompt-run", "Summarize the current task.", max_steps=2)
    registry = ToolRegistry(
        [
            ToolDefinition(
                name="lookup",
                description="Look up one fact.",
                required_keys=("topic",),
                handler=lambda action_input, _context: action_input,
            )
        ]
    )
    builder = PromptBuilder(
        template=template,
        base_sections={"USER_CONTEXT": "This is a quick demo."},
    )

    prompt = builder.build(
        state,
        registry,
        extra_sections={"RETRIEVED_CONTEXT": ["chunk-a", "chunk-b"]},
    )

    assert "SYSTEM:" in prompt
    assert "OBJECTIVE:\nSummarize the current task." in prompt
    assert "AVAILABLE_TOOLS:\n- lookup: Look up one fact. (required: topic)" in prompt
    assert "RETRIEVED_CONTEXT:" in prompt


def test_prompt_catalog_loads_builtin_templates():
    catalog = PromptCatalog.load_builtin()

    assert "default_agent" in catalog.names()
    assert "hackathon_agent" in catalog.names()
