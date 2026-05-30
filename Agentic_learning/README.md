# AI Systems Starter Kit

This repository now contains two layers:

- `starter_kit/`: a lightweight reusable foundation for hackathon-style AI systems.
- `Phase2/` and `Phase3/`: the original project-specific implementations kept as reference material and extraction source.

The goal of the starter kit is not to preserve the NIDS/domain logic. It preserves the working style that was already present here:

- explicit agent loops
- explicit shared state
- explicit tool dispatch
- simple workflow sequencing
- easy logging and debugging
- easy replacement of prompts, tools, retrieval, and API clients

## What Was Extracted

`starter_kit/` keeps the reusable patterns that appeared across the existing project:

- `agent.py`: bounded loop with parser, tool dispatch, hooks, and final actions
- `workflow.py`: sequential node runner that also supports lightweight multi-agent patterns through shared state and messages
- `state.py`: compact shared state, step history, outputs, errors, and messages
- `tools.py`: small tool registry with validation and uniform results
- `prompts.py`: explicit prompt composition instead of hidden prompt magic
- `validation.py`: strict structured-output parsing for fast debugging
- `retrieval.py`: minimal retrieval interface for local RAG-like experiments
- `llm.py`: callable LLM adapter plus OpenAI Responses API wrapper
- `api.py`: small JSON API client for non-LLM service calls
- `logging.py`: lightweight event logging and JSON artifact writing

## What Stayed Project-Specific

The following remain in the old phases because they are tied to the original smell-audit/domain workflow:

- dataset loading and validation
- feature-analysis tools
- NIDS-specific prompt wording
- investigation, ranking, critic, and batch-auditor components
- project-specific scoring and reporting logic

## Quick Start

Run the focused starter-kit tests:

```powershell
python -m pytest starter_kit/tests/test_starter_kit.py
```

Run the minimal example:

```powershell
python -m starter_kit.examples.simple_agent
```

Run the observable CLI-first demo:

```powershell
python main.py
```

Optional observability mode override:

```powershell
$env:STARTER_KIT_LOG_MODE = "debug"
python main.py
```

## Recommended Use

For a new hackathon project:

1. Copy `starter_kit/` into the new repo.
2. Replace the example tools with project tools.
3. Swap in your own prompts and parser rules if the output format changes.
4. Use `run_agent_loop()` for a single-agent loop.
5. Use `WorkflowRunner` when you need explicit multi-step or multi-agent sequencing.

## CLI Observability

The starter kit includes a lightweight CLI observability layer under `starter_kit/cli/`.

- `display.py`: small formatting helpers and truncation
- `logger.py`: CLI observer with verbosity modes
- `workflow_view.py`: workflow step rendering plus ASCII or Mermaid graph output
- `retrieval_debug.py`: retrieval query and chunk inspection
- `state_view.py`: state summary and partial diff rendering
- `tool_trace.py`: tool call traces with args, timing, and results

Attach it to any run with `attach_cli_observer()` and `DebugLogger`. The default design goal is transparent debugging, not a terminal UI framework.

## Prompt Templates And Builder

The starter kit now includes a reusable prompt layer in `starter_kit/prompts.py` plus built-in templates under `starter_kit/prompt_templates/`.

- `PromptTemplate`: load from inline sections or `.txt` files
- `PromptCatalog`: register and load template directories
- `PromptBuilder`: assemble runtime sections like objective, tools, state, history, and retrieved context
- `load_prompt_template()`: load one template file directly
- `get_default_prompt_template()`: use the built-in default agent template

This keeps prompts explicit and easy to swap during hackathons, while still supporting file-based prompt iteration.

See `notes/reusable-core-audit.md` for the extraction rationale and mapping back to the original codebase.