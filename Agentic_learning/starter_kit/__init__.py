"""Lightweight AI systems starter kit extracted from the existing project patterns."""

from .agent import AgentHooks, AgentLoopConfig, run_agent_loop
from .api import JsonApiClient, JsonApiRequest, JsonApiResponse
from .cli import CliObserver, ObservabilityConfig, attach_cli_observer
from .llm import CallableLlmClient, OpenAIResponsesClient
from .logging import DebugLogger
from .prompts import (
    DEFAULT_PROMPT_TEMPLATE_DIR,
    PromptBuilder,
    PromptCatalog,
    PromptTemplate,
    build_agent_prompt,
    get_default_prompt_template,
    load_prompt_template,
)
from .retrieval import InMemoryRetriever, RetrievalItem
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
from .tools import ToolContext, ToolDefinition, ToolRegistry
from .validation import ParsedAction, StrictLineActionParser
from .workflow import NodeResult, WorkflowNode, WorkflowRunner, WorkflowServices

__all__ = [
    "AgentHooks",
    "AgentLoopConfig",
    "CliObserver",
    "CallableLlmClient",
    "DEFAULT_PROMPT_TEMPLATE_DIR",
    "DebugLogger",
    "InMemoryRetriever",
    "JsonApiClient",
    "JsonApiRequest",
    "JsonApiResponse",
    "NodeResult",
    "ObservabilityConfig",
    "OpenAIResponsesClient",
    "ParsedAction",
    "PromptBuilder",
    "PromptCatalog",
    "PromptTemplate",
    "RetrievalItem",
    "RunState",
    "StepRecord",
    "StrictLineActionParser",
    "ToolContext",
    "ToolDefinition",
    "ToolRegistry",
    "WorkflowMessage",
    "WorkflowNode",
    "WorkflowRunner",
    "WorkflowServices",
    "advance_step",
    "attach_cli_observer",
    "append_error",
    "append_step_record",
    "build_state_summary",
    "build_agent_prompt",
    "diff_state_snapshots",
    "get_default_prompt_template",
    "init_state",
    "load_prompt_template",
    "merge_shared",
    "publish_message",
    "run_agent_loop",
    "set_output",
    "snapshot_state",
]
