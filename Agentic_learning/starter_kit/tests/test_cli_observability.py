from io import StringIO

from starter_kit.agent import AgentLoopConfig, run_agent_loop
from starter_kit.cli import ObservabilityConfig, attach_cli_observer, render_workflow_graph, workflow_graph_to_mermaid
from starter_kit.llm import CallableLlmClient
from starter_kit.logging import DebugLogger
from starter_kit.prompts import PromptTemplate, build_agent_prompt
from starter_kit.retrieval import InMemoryRetriever
from starter_kit.state import init_state
from starter_kit.tools import ToolDefinition, ToolRegistry
from starter_kit.validation import StrictLineActionParser
from starter_kit.workflow import NodeResult, WorkflowNode, WorkflowRunner, WorkflowServices


def test_cli_observer_renders_workflow_agent_tool_and_retrieval_output():
    stream = StringIO()
    logger = DebugLogger()
    attach_cli_observer(
        logger,
        ObservabilityConfig(mode="debug", max_chars=400,
                            show_prompt_sections=True),
        stream=stream,
    )
    retriever = InMemoryRetriever(
        [
            {"item_id": "chunk-1", "text": "workflow debugging with state diffs",
                "metadata": {"source": "notes"}},
            {"item_id": "chunk-2", "text": "tool trace visibility and retrieval context",
                "metadata": {"source": "notes"}},
        ],
        logger=logger,
        name="demo_retriever",
    )
    responses = iter(
        [
            "THOUGHT: I should inspect context first.\n"
            "ACTION: inspect_context\n"
            'ACTION_INPUT: {"focus": "debug"}',
            "THOUGHT: I can summarize now.\n"
            "ACTION: finish\n"
            'ACTION_INPUT: {"answer": "transparent run"}',
        ]
    )
    llm = CallableLlmClient(lambda _prompt: next(responses))
    registry = ToolRegistry(
        [
            ToolDefinition(
                name="inspect_context",
                description="Inspect retrieved context.",
                required_keys=("focus",),
                handler=lambda _action_input, context: {"chunks": len(
                    context.state.shared.get("retrieved_context", []))},
            )
        ]
    )

    def retrieve_node(state, services):
        results = services.retriever.search("workflow debug context", limit=2)
        return NodeResult(updates={"retrieved_context": [item.text for item in results]})

    def agent_node(state, services):
        template = PromptTemplate(name="demo", sections={
                                  "SYSTEM": "Work clearly.", "USER_CONTEXT": "Debug the workflow."})
        run_agent_loop(
            state=state,
            llm=services.llm,
            tool_registry=services.tools,
            parser=StrictLineActionParser(),
            logger=services.logger,
            prompt_builder=lambda current_state, tools: build_agent_prompt(
                current_state,
                tools,
                template=template,
                extra_sections={"RETRIEVED_CONTEXT": current_state.shared.get(
                    "retrieved_context", [])},
            ),
            config=AgentLoopConfig(final_actions=("finish",)),
        )
        return NodeResult(stop=True, status="completed")

    runner = WorkflowRunner(
        [
            WorkflowNode(name="retrieve_context",
                         handler=retrieve_node, default_next="run_agent"),
            WorkflowNode(name="run_agent", handler=agent_node),
        ],
        name="demo_workflow",
    )
    state = init_state(
        "cli-demo",
        "Observe the run.",
        metadata={"agent_name": "debug_agent",
                  "workflow_name": "demo_workflow"},
    )

    runner.run(
        state,
        start_at="retrieve_context",
        services=WorkflowServices(
            llm=llm, tools=registry, retriever=retriever, logger=logger),
    )

    output = stream.getvalue()
    assert "[WORKFLOW] DEMO_WORKFLOW" in output
    assert "[STEP] RETRIEVE_CONTEXT" in output
    assert "[RETRIEVAL] DEMO_RETRIEVER" in output
    assert "[AGENT] DEBUG_AGENT" in output
    assert "[TOOL] INSPECT_CONTEXT" in output
    assert "[STATE_DIFF]" in output


def test_workflow_graph_renderers_support_ascii_and_mermaid():
    runner = WorkflowRunner(
        [
            WorkflowNode(name="a", handler=lambda _state,
                         _services: NodeResult(), default_next="b"),
            WorkflowNode(name="b", handler=lambda _state,
                         _services: NodeResult(stop=True, status="completed")),
        ],
        name="graph_demo",
    )

    graph = runner.describe_graph()
    ascii_graph = render_workflow_graph(
        graph, current_node="a", output_format="ascii")
    mermaid_graph = workflow_graph_to_mermaid(graph)

    assert "[WORKFLOW_GRAPH] GRAPH_DEMO" in ascii_graph
    assert "* a -> b" in ascii_graph
    assert "graph TD" in mermaid_graph
    assert "a --> b" in mermaid_graph
