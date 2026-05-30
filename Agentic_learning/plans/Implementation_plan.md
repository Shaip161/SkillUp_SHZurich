# Career Transition Learning System — Implementation Plan

## 1. Goal

This document translates the final conceptual architecture from `Plan.md` into an implementation plan that can be executed with the current repository resources.

The objective is to:

- reuse the existing S&T framework as much as possible
- avoid rebuilding generic orchestration primitives from scratch
- implement the MVP in stable phases
- validate each phase before moving to the next one
- preserve the core product principle: fixed structure with constrained dynamic generation

This is still an implementation strategy document, not a task-by-task coding spec.

---

## 2. Ground Rules

The implementation should follow these architectural rules from the final plan:

- the learning structure is fixed
- the LLM fills predefined structures instead of inventing arbitrary flows
- the curriculum is generated once after inputs are received
- the generated curriculum is persisted and later consumed by the user
- progression logic is deterministic and explainable
- evaluation for the MVP is simplified around final evaluation and remediation
- frontend-facing outputs must be stable and schema-driven

---

## 3. What Can Be Reused From the Current Framework

The current framework already provides useful reusable primitives.

### 3.1 Workflow orchestration

Reusable:

- `workflow.py`
- `state.py`
- `logging.py`

Use for:

- offline curriculum-generation workflows
- online learning-runtime workflows
- observability and state-diff tracing

Why reuse it:

- it already supports sequential workflows cleanly
- it matches the product requirement of deterministic progression
- it is easier to test than an open autonomous agent loop

### 3.2 Prompt construction

Reusable:

- `prompts.py`

Use for:

- modular prompt families
- fixed output sections
- stage-specific prompt assembly

Why reuse it:

- it already fits the idea of structured prompting with explicit sections

### 3.3 Validation and parsing helpers

Reusable:

- `validation.py`
- `tools.py`

Use for:

- strict schema checks
- stage-level action validation when needed
- wrapping deterministic validators behind clean tool interfaces

### 3.4 Retrieval and external service wrappers

Reusable:

- `retrieval.py`
- `api.py`
- `llm.py`

Use for:

- retrieving skill context and examples
- wrapping future external data sources
- injecting mocked or real LLM clients during testing

### 3.5 CLI observability and tests

Reusable:

- CLI observer support
- current framework tests
- workflow examples

Use for:

- end-to-end debugging
- prompt inspection
- state transition validation
- smoke tests during early product iteration

---

## 4. Current Constraint Before Product Work

Before implementing the learning system itself, the current framework needs one stabilization pass.

Observed issue:

- the code currently lives under `agent framework/`
- existing imports and tests still expect `starter_kit`
- `python main.py` and focused tests do not currently run from `Agentic_learning/`

Implication:

- Phase 0 must stabilize the package layout first
- otherwise every later feature will be built on an unstable baseline

This is not product logic, but it is a prerequisite.

---

## 5. Recommended Implementation Phases

## Phase 0 — Stabilize The Framework Baseline

Objective:

- make the framework executable and testable again as a reusable base

Main work:

- fix the package naming mismatch
- make `main.py` runnable from `Agentic_learning/`
- make focused framework tests pass again
- confirm the demo examples execute correctly

Deliverable:

- a green reusable baseline for future product work

Validation:

- framework unit tests pass
- observable demo runs successfully
- imports are consistent across code and tests

Reason this comes first:

- without this, all later work mixes product implementation with packaging noise

---

## Phase 1 — Separate Product Code From Framework Code

Objective:

- keep the reusable framework generic
- place product-specific learning-system logic in its own package/module area

Main work:

- create a dedicated product package for the career transition learning system
- define boundaries between generic framework and domain logic
- keep framework responsibilities limited to orchestration, prompts, logging, tools, and state primitives

Deliverable:

- a clean architecture where the learning product builds on the framework instead of modifying it everywhere

Validation:

- framework tests still pass
- product package can import and use framework primitives without circular coupling

Reason this is early:

- it prevents architecture drift and avoids embedding product assumptions into reusable infrastructure

---

## Phase 2 — Define The Domain Contracts First

Objective:

- lock the structures the system will generate, persist, and serve to the frontend

Main work:

- define the input contract for user profile, target role, and skill gap
- define the schema for skill templates
- define the schema for subskills
- define the schema for stage payloads
- define the schema for generated curriculum
- define the schema for progress state
- define the schema for evaluation results
- define the schema for remediation/error memory

Key principle:

- structure fixed, content variable

Deliverable:

- a stable schema layer that all later components depend on

Validation:

- schema tests
- fixture examples for each contract
- contract snapshots reviewed against frontend expectations

Reason this comes before business logic:

- if the contracts are unstable, prompts, persistence, runtime logic, and frontend work all drift at the same time

---

## Phase 3 — Build The Hardcoded MVP Knowledge Layer

Objective:

- encode the constrained learning structure for the MVP

Main work:

- define the initial hardcoded skill library
- define allowed subskill structure per skill family
- define stage templates and fixed stage ordering
- define rubric structures for conceptual and practical evaluation
- define common error categories and remediation slots

Important clarification:

- this phase hardcodes the structure
- it does not mean hardcoding every final generated explanation or exercise

Deliverable:

- an explicit internal catalog describing what can be generated and how it is organized

Validation:

- unit tests for skill-template loading
- unit tests for structural constraints
- fixture-driven checks that each skill expands into a valid curriculum skeleton

Reason this comes before generation:

- the LLM can only be constrained if the allowed shapes already exist in code

---

## Phase 4 — Implement The Offline Curriculum Generation Workflow

Objective:

- generate the full course once from processed inputs

Main work:

- create a sequential offline workflow using the framework workflow runner
- start from normalized inputs: user profile, target role, missing skills
- map missing skills to allowed skill templates
- instantiate subskills inside the predefined structure
- generate stage content inside those structures
- assemble the complete curriculum object
- validate the generated curriculum against the contracts

Suggested workflow shape:

1. input intake
2. skill selection
3. subskill instantiation
4. stage generation
5. curriculum assembly
6. schema validation
7. persistence handoff

Deliverable:

- a persistent, frontend-ready curriculum generated one time per plan creation event

Validation:

- end-to-end workflow test with mocked LLM
- deterministic fixture test for a known user profile and target role
- schema validation on final curriculum output
- observability output reviewed in CLI logs

Reason this is the core MVP milestone:

- once this exists, the system can stop being an abstract planner and become a structured learning product

---

## Phase 5 — Implement Persistence And State Access

Objective:

- persist the generated curriculum and all runtime learning state

Main work:

- store generated curriculum objects
- store current stage position and unlock state
- store progress per skill and subskill
- store final evaluation results
- store remediation/error memory
- provide simple read and write interfaces for the runtime layer

Important MVP principle:

- keep persistence simple and explicit
- optimize for determinism and clarity, not for maximum architectural complexity

Deliverable:

- a persistence layer that allows resume, progress tracking, and retries

Validation:

- repository tests
- round-trip persistence tests
- resume-from-state tests

Reason this must come before the runtime UX:

- the product assumes the user consumes a persisted course, not a freshly improvised one each time

---

## Phase 6 — Implement The Online Learning Runtime

Objective:

- allow the user to navigate and complete the generated curriculum

Main work:

- load the persisted curriculum
- expose skill overview and current next step
- render stage content in fixed order
- collect answers for conceptual and practical stages
- run final evaluation
- trigger remediation only when evaluation fails
- unlock next subskill when completion conditions are met
- update progress continuously in persistence

Important MVP simplification:

- the main gating logic should happen at final evaluation
- remediation should stay tightly tied to failure cases

Deliverable:

- a stable runtime that lets a user progress through a prebuilt course with deterministic progression

Validation:

- runtime workflow tests for success path
- runtime workflow tests for fail-then-remediate path
- progress-unlock tests
- retry-state tests

Reason this comes after offline generation:

- the runtime depends on a generated and validated curriculum already existing

---

## Phase 7 — Add Product API Contracts For The Frontend

Objective:

- expose stable product-facing endpoints for the frontend

Main work:

- endpoint for plan overview/dashboard
- endpoint for skill detail
- endpoint for stage retrieval
- endpoint for answer submission
- endpoint for evaluation result
- endpoint for progress refresh

Design rule:

- the frontend should receive predictable structured payloads
- it should not need to understand orchestration internals or prompt details

Deliverable:

- a frontend-safe API layer on top of the product runtime and persistence layer

Validation:

- API contract tests
- payload snapshot tests
- frontend fixture validation

Reason this comes late:

- endpoint design is much easier once internal contracts and runtime behavior are already stable

---

## Phase 8 — Replace Mocks With Real Integrations Incrementally

Objective:

- connect the MVP to real upstream and downstream components without destabilizing the core flow

Main work:

- replace mocked inputs with real profile and gap inputs
- connect real LLM prompts where currently mocked
- connect course recommendation or external resource providers if needed
- connect future labor-market and matching outputs to the curriculum entrypoint

Deliverable:

- the same validated learning flow, now fed by real system inputs

Validation:

- integration tests at the seams
- fallback behavior checks
- observability review for real runs

Reason this is last:

- it preserves a working MVP core before external variability is introduced

---

## 6. Most Important Build Order

The most efficient build order is:

1. stabilize framework baseline
2. define product package boundaries
3. lock schemas/contracts
4. encode hardcoded structural catalog
5. implement offline curriculum generation
6. implement persistence
7. implement online runtime
8. expose API layer
9. attach real integrations

This ordering minimizes rework because:

- contracts are fixed before prompts and persistence depend on them
- workflow logic is tested before UI/API assumptions are layered on top
- integrations arrive only after the product flow works in isolation

---

## 7. Validation Strategy

Validation should be phased, not left to the end.

### 7.1 Baseline validation

- package import tests
- framework smoke tests
- demo execution tests

### 7.2 Contract validation

- schema tests
- fixture-based validation
- stable payload examples for frontend review

### 7.3 Workflow validation

- node-level tests for offline generation
- end-to-end curriculum-generation test with mocked LLM
- runtime workflow tests for progression and retry logic

### 7.4 Persistence validation

- save/load round-trip tests
- state resume tests
- unlock progression tests

### 7.5 Observability validation

- prompt inspection in CLI logs
- workflow graph inspection
- state-diff review for key transitions

### 7.6 Integration validation

- real LLM smoke tests
- real API seam tests
- regression tests on sample users and target roles

---

## 8. Implementation Evaluation Plan

The validation strategy above explains how to test each phase.

This section defines how to evaluate whether the implementation behaves as intended at product level, not only whether individual tests pass.

The goal is to verify that the implemented system matches the final architecture from `Plan.md` in behavior, structure, outputs, and user flow.

### 8.1 Evaluation objective

The implementation is considered correct only if it satisfies all of the following:

- it preserves fixed structure with constrained generation
- it generates the curriculum once and persists it before runtime consumption
- it enforces deterministic progression and unlock logic
- it applies final evaluation and remediation as defined for the MVP
- it exposes stable frontend-ready payloads
- it keeps the system observable and debuggable

This means evaluation must cover:

- architectural correctness
- output correctness
- runtime correctness
- persistence correctness
- frontend contract stability
- qualitative learning-flow correctness

### 8.2 Evaluation dimensions

The implementation should be evaluated across the following dimensions.

#### A. Architectural compliance

Questions to verify:

- is the structure fixed in code?
- are stages always produced in the same allowed order?
- is the curriculum generated once, then persisted?
- is runtime generation limited to retries/remediation or tightly scoped content?
- is the implementation using sequential workflow logic instead of uncontrolled agent autonomy?

Pass condition:

- no runtime path bypasses the fixed curriculum structure
- no component invents arbitrary new stage or curriculum shapes outside the declared contracts

#### B. Contract and schema compliance

Questions to verify:

- do all generated outputs satisfy the product schemas?
- do all stage payloads expose the exact fields expected by the frontend?
- are evaluation and remediation payloads consistent across skills?

Pass condition:

- all schema validations pass on fixture runs and regression scenarios
- frontend-facing payload snapshots remain stable unless intentionally versioned

#### C. Curriculum generation correctness

Questions to verify:

- are the right skills selected from the input gap?
- are subskills instantiated within the expected structure?
- are stage payloads generated for every required subskill?
- is the generated curriculum complete, coherent, and persistable?

Pass condition:

- the offline generation workflow produces a valid complete curriculum for all core fixtures
- no partially generated curriculum is accepted as successful

#### D. Evaluation and rubric correctness

Questions to verify:

- are conceptual evaluations rubric-based and structured?
- are practical evaluations deterministic where possible?
- is final evaluation aggregated as intended?
- are scores and pass/fail outputs interpretable and stable?

Pass condition:

- every evaluation returns structured score, pass/fail result, detected errors, and feedback
- no evaluation path returns free-form unstructured output to downstream systems

#### E. Progression and unlock correctness

Questions to verify:

- does passing unlock the next step, next subskill, or next skill exactly as intended?
- does failing route the user into remediation instead of allowing incorrect advancement?
- is progress percentage computed consistently?

Pass condition:

- progression state always matches the last completed validated action
- no invalid state allows skipping required stages or subskills

#### F. Error memory and retry correctness

Questions to verify:

- are final evaluation errors stored semantically?
- do retries preserve relevant error memory?
- are errors removed or cleared only after mastery?
- does remediation target failed concepts instead of producing generic filler?

Pass condition:

- retry flows keep enough memory to reinforce weak areas without corrupting progression state

#### G. Persistence and resume correctness

Questions to verify:

- can the system resume exactly from the stored stage?
- are curriculum, progress, evaluation, and error records all persisted correctly?
- are immediate updates enough to preserve deterministic behavior across sessions?

Pass condition:

- save/load round trips reproduce the same runtime state for all key scenarios

#### H. Frontend readiness and UX correctness

Questions to verify:

- does the frontend receive the whole generated curriculum structure upfront?
- are stage payloads predictable enough for reusable rendering?
- does the user always see a guided next action?
- does the runtime feel simple, stable, and progression-oriented?

Pass condition:

- a frontend can render dashboard, skill detail, stages, progress, evaluation, and remediation without custom logic per skill

#### I. Observability and debuggability

Questions to verify:

- can developers inspect workflow graph, prompts, outputs, state diffs, and evaluation transitions?
- can failures be traced to a specific prompt, node, or persistence update?

Pass condition:

- every critical workflow path is inspectable through logs, traces, and deterministic fixtures

### 8.3 Evaluation artifacts to prepare

To evaluate the implementation well, the team should define a small but explicit evaluation corpus.

Recommended artifacts:

- 3 to 5 canonical user-profile fixtures
- 3 to 5 target-role fixtures
- fixed missing-skill inputs for each scenario
- expected curriculum skeletons for each scenario
- expected progression snapshots
- expected fail/remediation/retry scenarios
- expected frontend payload snapshots

These fixtures should act as the reference set for regression testing.

### 8.4 Core evaluation scenarios

The implementation should be judged against a small number of end-to-end scenarios.

#### Scenario 1. Happy path

- user input is valid
- curriculum is generated successfully
- user completes stages correctly
- final evaluation passes
- next subskill unlocks
- progress updates correctly

Expected result:

- the entire flow is coherent, deterministic, and persistently stored

#### Scenario 2. Fail then remediate

- user reaches final evaluation
- user fails
- semantic errors are stored
- remediation is generated
- user retries with corrected understanding

Expected result:

- the user does not advance incorrectly
- retries preserve weakness context
- progress remains consistent

#### Scenario 3. Stop and resume

- user exits in the middle of a curriculum
- system reloads stored state later
- runtime resumes at the correct place

Expected result:

- no state corruption
- no repeated unlocking errors
- no loss of relevant evaluation history

#### Scenario 4. Contract stability

- multiple skills and stage payloads are generated
- frontend snapshots are checked

Expected result:

- all payloads stay structurally stable across scenarios

#### Scenario 5. Integration variability

- real LLM or external adapters are used instead of mocks

Expected result:

- the system still respects schemas, structure, and progression rules
- external variability does not break deterministic control flow

### 8.5 Evaluation methods by layer

The implementation should be evaluated with multiple complementary methods.

#### Unit-level evaluation

Use for:

- schema validators
- rubric logic
- unlock logic
- error classification
- persistence helpers

Purpose:

- verify local correctness cheaply and repeatedly

#### Workflow-level evaluation

Use for:

- offline curriculum generator
- runtime progression flow
- remediation and retry loop

Purpose:

- verify sequencing, outputs, and state transitions

#### Snapshot evaluation

Use for:

- curriculum payloads
- stage payloads
- API responses
- progress objects

Purpose:

- detect accidental drift in contracts and frontend-facing structures

#### Golden-scenario evaluation

Use for:

- canonical end-to-end user journeys

Purpose:

- verify that the whole product behaves as intended, not just isolated modules

#### Human review evaluation

Use for:

- explanation quality
- remediation usefulness
- contextualization relevance
- perceived UX coherence

Purpose:

- catch issues that pure automated tests will not detect in generated educational content

### 8.6 Acceptance criteria by phase

Each phase should have a clear implementation evaluation gate.

#### Phase 0 acceptance

- framework imports are stable
- focused tests run
- demo execution works

#### Phase 1 acceptance

- product code is separated from framework code cleanly
- no circular dependency appears

#### Phase 2 acceptance

- all core contracts are defined and fixture-backed
- payloads are precise enough for frontend and persistence use

#### Phase 3 acceptance

- skill library and structural catalog generate only allowed curriculum skeletons
- rubric and remediation slots are explicitly encoded

#### Phase 4 acceptance

- offline workflow generates complete valid curricula for canonical fixtures
- generated objects pass schema validation and can be persisted directly

#### Phase 5 acceptance

- saved state can be restored faithfully
- progress and error memory survive round-trip persistence

#### Phase 6 acceptance

- runtime correctly handles pass, fail, remediation, retry, and unlock behavior
- no user can bypass required progression

#### Phase 7 acceptance

- frontend receives stable, documented payloads for all primary screens

#### Phase 8 acceptance

- real integrations do not break schemas, progression logic, or observability

### 8.7 Release gate for the MVP

The MVP should not be considered ready just because the code runs.

The MVP release gate should require:

- all canonical scenarios passing
- no schema drift in frontend-facing payloads
- deterministic progression verified
- remediation and retry behavior verified
- persistence and resume behavior verified
- observability sufficient to debug prompt and state issues
- at least one human review pass on generated curriculum quality and remediation usefulness

If any of these fail, the MVP is not yet aligned with the intended product behavior.

### 8.8 Most important evaluation principle

The implementation should be evaluated against the intended behavior of the product, not only against internal technical success.

In practice, this means:

- it is not enough that a workflow completes
- it must complete with the right structure
- it is not enough that an LLM returns output
- it must return schema-safe and pedagogically useful output
- it is not enough that progress is stored
- the stored progress must preserve deterministic learning flow

This is the key difference between a technically working prototype and an MVP that actually behaves as designed.

---

## 9. What Not To Build Too Early

To protect the MVP, the following should be delayed:

- open-ended autonomous multi-agent behavior
- highly dynamic curriculum structures
- broad labor-market integration inside the learning layer
- complex graph-driven personalization inside the runtime
- overbuilt frontend state machinery before payload contracts are stable
- excessive persistence abstraction before actual state needs are proven

---

## 10. Practical Recommendation For The Immediate Next Step

The best immediate next step is not to start coding random product components.

The best immediate next step is:

1. stabilize the framework baseline
2. define the product domain contracts
3. only then begin the offline curriculum generator

That gives the team the shortest path to a testable vertical slice.

---

## 11. Target MVP Vertical Slice

The first complete vertical slice should be very small but end-to-end.

Recommended slice:

- one processed user input fixture
- one target role fixture
- one missing-skill set
- one generated curriculum with a small number of skills/subskills
- one persisted course
- one runtime flow with final evaluation and remediation

If this slice works, the architecture is validated.
If this slice does not work, expanding scope will only multiply problems.

---

## 12. Summary

The optimal implementation strategy is to reuse the current framework for orchestration, state, logging, prompts, and testability, while building the learning product as a separate domain layer on top of it.

The most important idea is:

- do not start from UI or LLM prompting
- start from executable baseline, fixed contracts, constrained structure, and one generated curriculum flow

That sequence gives the team the best chance to validate architecture early, keep outputs stable for the frontend, and avoid overengineering the MVP.