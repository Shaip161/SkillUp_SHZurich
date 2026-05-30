# Reusable Core Audit

This note records the extraction boundary used to turn the original project into a reusable starter framework.

## Reusable Patterns Already Present

These patterns were strong enough in the existing codebase to preserve directly:

- explicit bounded agent loops
- structured parser plus tool dispatch
- append-only step history and shared state
- node-based workflow orchestration
- prompt building as a separate concern
- uniform machine-readable tool outputs
- run logging and reproducibility hooks
- small LLM client wrapper around the API layer

The clearest source files for those patterns were concentrated in `Phase3/`:

- `Phase3/agent/loop.py`
- `Phase3/agent/parser.py`
- `Phase3/agent/executor.py`
- `Phase3/state/schema.py`
- `Phase3/state/store.py`
- `Phase3/tools/registry.py`
- `Phase3/phase3_runtime/orchestrator.py`
- `Phase3/utils/openai_response.py`

## Project-Specific Pieces That Should Not Be the Skeleton

These parts are tightly coupled to the smell-audit domain and were intentionally not moved into the reusable core:

- dataset-specific loaders and validation
- feature-analysis tools and capability metadata
- domain-specific prompt heuristics
- canonical batch state shaped around structural substrate and interpretive hypotheses
- phase-specific components such as semantic extraction, planner, critic, ranking, and final batch auditor
- report exporters, run-evaluation scripts, and dataset reports

## Resulting Starter-Kit Shape

The extracted framework lives in `starter_kit/` and stays intentionally flat:

- `agent.py`: single-agent loop
- `workflow.py`: configurable workflow runner
- `state.py`: shared state and message passing
- `tools.py`: tool registry and execution envelope
- `prompts.py`: prompt templates and prompt builder
- `validation.py`: structured output parser
- `retrieval.py`: minimal retrieval abstraction
- `llm.py`: model adapter
- `api.py`: JSON service adapter
- `logging.py`: debug and artifact hooks

## Why This Shape

The original project already favored explicit orchestration over hidden framework behavior. The reusable skeleton keeps that philosophy:

- functions and dataclasses stay easy to inspect
- replacement points are passed in as callables or registries
- state is plain and serializable
- workflow transitions are visible in code
- debugging does not require custom runtime infrastructure

## Extension Points

Use the starter kit by swapping only the surfaces that change per project:

- tools: register new `ToolDefinition` entries
- prompts: pass a custom `PromptTemplate` or custom prompt builder
- parser: replace `StrictLineActionParser` if the output protocol changes
- retrieval: replace `InMemoryRetriever` with a vector or database-backed retriever
- API layer: swap `JsonApiClient` with a project adapter
- workflow nodes: add or remove `WorkflowNode` handlers
- hooks: use `AgentHooks` and `DebugLogger` for custom tracing

## Practical Guidance

For fast hackathon adaptation, prefer this order:

1. Start with `run_agent_loop()` if one agent can do the job.
2. Introduce `WorkflowRunner` only when sequencing becomes clearer as named nodes.
3. Use messages and shared state before building heavier coordination layers.
4. Keep tools small and deterministic where possible.
5. Push domain-specific logic to tool handlers and workflow nodes, not into the framework core.