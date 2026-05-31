# Integration Layer — System A → System B

A thin, modular layer that connects the two existing systems **without merging,
rewriting, or tightly coupling them**:

- **System A — Job Matchmaking Engine** (`backend/`): CV + job listings →
  matched jobs + per-job skill gaps.
- **System B — Learning Agent System** (`Agentic_learning/`): structured skill
  gaps + learning objectives → personalized, agent-driven curriculum.

This layer owns only the *seam* between them: typed contracts, a pure adapter,
and a lightweight orchestrator. Neither subsystem imports this layer, and this
layer imports System B from exactly one file.

```
   CV + jobs ─▶ [MatchmakingProvider] ─▶ MatchmakingOutput ─▶ [Adapter] ─▶ LearningRequest ─▶ [LearningEngine] ─▶ curriculum
                  (port → System A)          (contract)        (mapper)        (contract)        (port → System B)
                                     └──────────────────── Orchestrator (sequences + validates + logs) ────────────────────┘
```

## Why it's decoupled

| Concern | How it's handled |
| --- | --- |
| No rewrites of either system | The layer only reads each system's existing public surface. System A is reached through a port; System B through its existing `generate_curriculum(...)` entry point. |
| No tight coupling | The orchestrator depends only on `Protocol` ports (`ports.py`), never on concrete System A/B classes. |
| No circular dependencies | Dependencies point **one way**: `integration → System B`. System A/B never import `integration`. |
| Orchestration stays outside the components | All sequencing lives in `orchestrator.py`; the subsystems are unaware they're being orchestrated. |
| Replaceable / extensible | Swap `MockMatchmakingProvider` for a real backend client, or `TransitionLearningEngine` for another engine, with zero orchestrator changes. |

## Modules

| File | Responsibility |
| --- | --- |
| `contracts.py` | Pydantic v2 schemas for the boundary: `MatchmakingOutput` + `GapResponse` (the two System A surfaces) and `LearningRequest` (System B in). Validates required fields, types, optional fields, and rejects malformed payloads via `ContractError`. |
| `ports.py` | `Protocol` interfaces: `MatchmakingProvider`, `LearningEngine`, `StructuredLogger`. The decoupling boundary. |
| `adapter.py` | Pure transformation `MatchmakingOutput → LearningRequest`: aggregates + prioritizes per-job skill gaps, builds the learner profile, resolves the target role. Plus `LearningObjective` (the caller-supplied learning objective). |
| `orchestrator.py` | `run_end_to_end(...)` — the 6-step pipeline. Validates at each boundary, raises `PipelineError` with the failing stage, and records a structured trace. |
| `logging_utils.py` | `CapturingLogger` (implements `StructuredLogger`, also compatible with System B's logger) + canonical event-type constants. |
| `providers/mock_matchmaking.py` | `MockMatchmakingProvider` — serves canned System A output (no DB/API needed). |
| `providers/learning_engine.py` | `TransitionLearningEngine` — the **only** module that imports System B; wraps `generate_curriculum`. |
| `mocks/` | `mock_cv.json`, `mock_jobs.json`, `mock_match_response.json`. |
| `run_workflow.py` | One-command end-to-end demo. |
| `tests/` | Contract, adapter, and end-to-end workflow tests. |

## The pipeline (`orchestrator.run_end_to_end`)

1. **Run matchmaking** via the `MatchmakingProvider` port.
2. **Validate** System A's output against the `MatchmakingOutput` contract.
3. **Extract + prioritize** missing skills (adapter: ranked by job demand).
4. **Transform** into a `LearningRequest` (adapter).
5. **Validate** the transformed payload, then **send** it to the `LearningEngine`.
6. **Capture** all outputs and a structured log trace.

Each stage emits a structured event, so the **raw matchmaking output**, the
**transformed payload**, and the **final agent input** are independently
inspectable (`logger.raw_matchmaking_payload`, `.transformed_payload`,
`.agent_input_payload`). Schema mismatches are logged as
`integration.error.schema_mismatch` and raised as `PipelineError`.

## Run it

From the project root (`SkillUp_SHZurich/`):

```bash
# End-to-end demo: CV → matchmaking → skill gaps → learning agents
python integration/run_workflow.py

# Test suite (contract + adapter + workflow tests)
python -m pytest integration/tests/ -q
```

The demo needs **no database, embeddings, or API keys**: it uses canned System A
output and runs System B in its deterministic (LLM-free) mode. It prints the
three boundary payloads and a curriculum summary, and writes the full trace to
`integration/integration_trace.json`.

## Two System A surfaces

System A exposes two relevant outputs; the layer supports both:

- **`POST /match`** → `MatchmakingOutput` (many jobs, each with per-job skill
  gaps). Used by the full orchestrator pipeline via `build_learning_request`.
- **`POST /gap/{job_id}`** → `GapResponse` (one job, `required_skills −
  user_skills`). This is the **pure, no-LLM data contract the backend docs
  designate for the learning system** (`CLAUDE.md`). Mapped via
  `build_learning_request_from_gap` (accepts one or several gaps).

Both converge on the same validated `LearningRequest` headed into System B, so
whichever surface the backend offers, the learning side is unchanged.

## Wiring the *real* System A

`MockMatchmakingProvider` exists only so the workflow is runnable offline. To use
the live backend, implement the `MatchmakingProvider` port with a client that
calls `backend`'s `/match` endpoint (or invokes it in-process) and returns a
payload shaped like `MatchmakingOutput` — then pass it to `run_end_to_end(...)`.
Nothing else changes. If System A also surfaces the parsed candidate (the
optional `candidate_profile` block), the adapter automatically builds a richer
learner profile; otherwise it degrades gracefully.

## Design notes

- **No value-level assumptions.** The adapter passes skill names through
  untouched (only trimmed/deduplicated). System B decides which skills it can
  actually teach — e.g. in the demo, `Kubernetes` is forwarded but dropped by
  System B's catalog, while the three catalog skills become full curricula.
- **Shared trace.** Passing one `CapturingLogger` to both `run_end_to_end` and
  `TransitionLearningEngine(logger=...)` produces a single unified trace across
  both layers (integration events + System B's workflow events).
- **Stable error surface.** Boundary failures surface as `ContractError`
  (schema) and `PipelineError` (stage), so callers never depend on Pydantic or
  System B internals to handle failures.
