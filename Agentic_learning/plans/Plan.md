# Career Transition Learning System — Technical Specification

## 1. Product Vision

Build a guided learning system for workers transitioning to a new role or sector due to AI-driven labor market changes. The system takes a user profile, a target job, and a precomputed skill gap, then generates a structured learning journey that helps the user learn the missing skills through a fixed pedagogical pipeline.

The product is **not** a general-purpose AI tutor and **not** a free-form autonomous multi-agent system. It is a **structured learning orchestration system** with controlled outputs, hardcoded skill templates for the MVP, deterministic progression rules where possible, and LLM-based contextualization and conceptual evaluation where useful.

---

## 2. Core Product Principles

1. **Structure is fixed; content is dynamic.**

   * The learning pipeline is predefined.
   * The system adapts prompts, examples, analogies, and difficulty using user context.

2. **Skills are hardcoded for the MVP.**

   * The first version uses a curated skill library.
   * Each skill has subskills and a standard progression pipeline.

3. **Progression should be simple and explainable.**

   * Progress is measured as percentage of completed steps.
   * Passing a step unlocks the next one.
   * Failed evaluations trigger remediation or retries.

4. **The LLM is used for generation and qualitative evaluation, not for arbitrary control.**

   * LLMs generate introductions, questions, explanations, reflections, and feedback.
   * Deterministic logic controls step order, completion, and progress.

5. **Contextual learning is central.**

   * Every step should connect with the user’s previous experience when possible.
   * The system should create analogies between known experience and the target skill.

---

## 3. Scope of the MVP

### In scope

* User profile input
* Target job input
* Precomputed missing skills input
* Skill library with hardcoded skills and subskills
* Fixed learning pipeline for each subskill
* Dynamic contextualization based on user background
* Conceptual evaluation with LLM + rubric
* Practical evaluation with deterministic checks when possible
* Error reflection and remediation
* Progress tracking per skill and per subskill
* Persistent storage of user state, evaluations, errors, and completed steps
* Basic interactive frontend

### Out of scope for the MVP

* Fully automated scraping pipeline for all jobs
* Dynamic ontology generation from the entire labor market
* Open-ended agent autonomy
* Complex recommender systems across all occupations
* Fully personalized curriculum generation without skill templates
* Large-scale certification marketplace integration
* Real-time labor market forecasting engine

---

## 4. System Overview

The system is composed of five main layers:

1. **Skill Library Layer**

   * Hardcoded skills, subskills, and learning objectives.

2. **Planning / Matching Layer**

   * Receives the user profile, target job, and missing skills.
   * Selects which skills and subskills to activate.
   * Produces the learning plan for the user.

3. **Routing / Context Layer**

   * Extracts the relevant user background and learning state.
   * Prepares stage-specific context for each step.

4. **Learning Execution Layer**

   * Runs the fixed pedagogical stages for each subskill:

     * introduction
     * conceptual understanding
     * practical exercise
     * evaluation
     * error reflection

5. **Progress / State Layer**

   * Stores all progress, scores, mistakes, step completion, and unlocks.
   * Calculates percentage progress and mastery.

---

## 5. User Journey

### 5.1 Entry

The user enters the system with:

* current profile / background
* target job
* missing skills or gap

This input is assumed to have been preprocessed already.

### 5.2 Dashboard

The user sees:

* target role
* selected skills to learn
* progress per skill
* progress overall
* next recommended step

### 5.3 Skill Selection

The user selects a skill from the dashboard.

Each skill has:

* subskills
* a fixed pipeline per subskill
* progress status
* evaluations and failed attempts history

### 5.4 Learning Loop per Subskill

For each subskill, the user goes through the same pedagogical pipeline:

1. Introduction
2. Conceptual understanding
3. Practical exercise
4. Evaluation
5. Error reflection
6. Progress update
7. Next subskill or remediation

### 5.5 Progression

* If the user passes the evaluations for a subskill, it is marked as completed.
* The next subskill is unlocked.
* If the user fails, the system creates remediation or retries.
* Overall skill progress is computed as the ratio of completed subskills/steps.

---

## 6. Skill Model

### 6.1 Skill Definition

A skill is a hardcoded learning entity representing a work-relevant capability.

Example:

* SQL
* Dashboarding
* Incident analysis
* Workflow reporting
* Data interpretation

### 6.2 Subskill Definition

Each skill is decomposed into subskills.

Example for SQL:

* Filtering
* Aggregation
* Joins
* Business reporting
* Workflow application

### 6.3 Skill Template Structure

Each skill template should contain:

* `skill_id`
* `skill_name`
* `description`
* `subskills[]`
* `target_jobs[]`
* `difficulty_level`
* `prerequisites[]`
* `related_certifications[]`

Each subskill should contain:

* `subskill_id`
* `subskill_name`
* `objective`
* `prerequisites[]`
* `expected_outcomes[]`
* `conceptual_criteria[]`
* `practical_criteria[]`
* `example_workflows[]`
* `common_mistakes[]`

### 6.4 Hardcoded vs Dynamic

* **Hardcoded:** skill list, subskill list, evaluation criteria structure, pipeline structure.
* **Dynamic:** contextual examples, explanations, analogies, practice tasks, prompt wording, remediation content.

---

## 7. Learning Pipeline per Subskill

Each subskill follows a fixed structure.

### Stage 1 — Introduction

Purpose:

* Introduce the subskill.
* Build intuition.
* Connect the concept to the user’s prior experience.

Output:

* brief conceptual explanation
* example
* analogy to prior background
* key takeaways

### Stage 2 — Conceptual Understanding

Purpose:

* Test whether the user understands the concept.
* Identify misconceptions.

Mechanism:

* LLM-generated Socratic questions.
* Rubric-based evaluation of answers.

Output:

* list of questions
* evaluation score
* detected misconceptions
* feedback

### Stage 3 — Practical Exercise

Purpose:

* Test whether the user can apply the concept in a realistic task.

Mechanism:

* structured exercise or mini scenario
* deterministic validation when possible
* LLM evaluation for qualitative cases

Output:

* exercise prompt
* user answer
* score
* pass/fail
* feedback

### Stage 4 — Evaluation

Purpose:

* Decide whether the subskill has been mastered.
* Gate progression to the next step.

Evaluation types:

* conceptual evaluation
* practical evaluation
* combined score

### Stage 5 — Error Reflection

Purpose:

* Review mistakes.
* Reinforce correct reasoning.
* Store errors for future remediation.

Output:

* list of repeated mistakes
* explanation of the correct reasoning
* targeted reinforcement suggestion

---

## 8. Orchestration Model

The system should be implemented as a controlled orchestration pipeline, not as a free-form multi-agent swarm.

### Main components

1. **Planner**
2. **Router / Context Builder**
3. **Stage Executors**
4. **Evaluation Engine**
5. **State Manager**

### 8.1 Planner

The planner decides:

* which skills are active
* in which order the user should learn them
* which subskills should be used
* what the active learning plan is

Important:

* The planner does **not** invent the whole learning structure from scratch in the MVP.
* The skill/subskill structure is predefined.
* The planner selects and orders from predefined templates.

### 8.2 Router / Context Builder

The router prepares the context for each stage.

It extracts:

* user background
* previous roles
* previous tasks
* analogous experiences
* current skill/subskill
* current mistakes
* prior scores

It then builds stage-specific context for:

* introduction
* conceptual understanding
* practical exercise
* reflection

### 8.3 Stage Executors

A stage executor is a module or prompt pattern that produces the content for a specific stage.

Examples:

* Introduction executor
* Conceptual question executor
* Practical exercise executor
* Reflection executor
* Evaluation executor

### 8.4 Evaluation Engine

The evaluation engine computes:

* score
* pass/fail
* mistakes
* misconceptions
* readiness for next step

The engine can combine:

* deterministic checks
* rubric-based scoring
* LLM-based assessment

### 8.5 State Manager

Tracks:

* completed steps
* scores
* progress
* unlocks
* failed attempts
* repeated mistakes
* current active skill/subskill

---

## 9. Evaluation Design

### 9.1 Conceptual Evaluation

Conceptual evaluation can use the LLM because it is suited to reasoning and misconception detection.

The evaluation should be rubric-based, not free-form.

Possible criteria:

* understands core concept
* can explain the concept back
* distinguishes related concepts
* avoids common misconceptions

Output fields:

* `conceptual_score`
* `passed`
* `misconceptions[]`
* `feedback`

### 9.2 Practical Evaluation

Practical evaluation should be deterministic when possible.

Examples:

* SQL query output comparison
* structured multiple-choice check
* specific answer format validation
* expected result matching

For tasks that cannot be deterministically checked, use LLM evaluation with rubrics.

Output fields:

* `practical_score`
* `passed`
* `errors[]`
* `feedback`

### 9.3 Mastery Definition

A subskill is mastered when:

* conceptual score exceeds a threshold
* practical score exceeds a threshold
* no critical misconceptions remain

Example thresholds:

* conceptual score >= 0.80
* practical score >= 0.70
* no critical misconceptions

These thresholds can be tuned later.

---

## 10. Progress Model

### 10.1 Progress Granularity

Progress is intentionally simple.

Recommended measurement:

* subskill completion ratio
* step completion ratio
* skill completion percentage

Example:

* 10 total steps in a skill
* 6 completed steps
* progress = 60%

### 10.2 Progress State

Track progress at:

* step level
* subskill level
* skill level
* overall program level

### 10.3 Unlock Logic

If a step is passed:

* mark step as completed
* unlock next step

If a subskill is completed:

* unlock next subskill

If a skill is completed:

* unlock next skill or certification step

---

## 11. Reflection and Error Handling

Reflection is not a free-form journal. It is a structured error review system.

### Reflection should:

* store mistakes
* classify mistakes
* explain the correct reasoning
* generate corrective reinforcement
* allow future retries with better context

### Error categories

* conceptual misunderstanding
* practical execution mistake
* incomplete reasoning
* repeated misconception
* careless error

### Stored reflection output

* `error_type`
* `error_description`
* `correct_reasoning`
* `reinforcement_prompt`
* `needs_retry`

---

## 12. Contextualization Strategy

Every generated explanation or exercise should use the user’s previous experience where possible.

### Context sources

* current CV / profile
* previous roles
* industries worked in
* tasks previously performed
* certifications already held
* known tools and workflows

### Contextualization examples

* For someone from Excel-heavy reporting, SQL can be explained as a more powerful way to query structured tables.
* For someone from operations, dashboards can be compared to KPI monitoring.
* For someone from logistics, incident workflows can be linked to operational coordination.

### Goals of contextualization

* reduce cognitive load
* improve transfer of knowledge
* increase confidence
* make the learning feel relevant

---

## 13. Data Model

The system needs persistent storage.

### 13.1 Core Entities

#### User

* `user_id`
* `name`
* `profile_data`
* `target_job`
* `skill_gap[]`
* `preferences`
* `created_at`

#### Skill

* `skill_id`
* `name`
* `description`
* `subskills[]`
* `difficulty`
* `tags[]`

#### Subskill

* `subskill_id`
* `skill_id`
* `name`
* `objective`
* `conceptual_criteria[]`
* `practical_criteria[]`

#### LearningSession

* `session_id`
* `user_id`
* `skill_id`
* `subskill_id`
* `stage`
* `content`
* `created_at`

#### EvaluationResult

* `evaluation_id`
* `user_id`
* `skill_id`
* `subskill_id`
* `stage`
* `score`
* `passed`
* `errors[]`
* `feedback`
* `created_at`

#### ProgressState

* `user_id`
* `skill_id`
* `subskill_id`
* `completed_steps[]`
* `current_step`
* `progress_percent`
* `mastery_status`

#### ErrorRecord

* `error_id`
* `user_id`
* `skill_id`
* `subskill_id`
* `error_type`
* `description`
* `correct_reasoning`
* `timestamp`

### 13.2 Persistence Requirements

The system must persist:

* completed steps
* evaluation scores
* repeated mistakes
* unlocked skills/subskills
* current progress
* session history

The system must not reset progress on refresh or logout.

---

## 14. Suggested Backend Components

### 14.1 Services

* Auth service
* User profile service
* Skill library service
* Learning plan service
* Context generation service
* Evaluation service
* Progress tracking service
* Reflection / remediation service

### 14.2 API Contract Philosophy

All stage outputs should be structured and machine-readable.

The frontend should not depend on free-form text only.

Recommended approach:

* JSON response objects for stage outputs
* strict schema validation
* minimal variability in field names

---

## 15. Suggested API Shapes

### 15.1 Get Skill Plan

`GET /api/plan?user_id=...`

Returns:

* target role
* selected skills
* skill order
* progress summary

### 15.2 Get Skill Detail

`GET /api/skills/{skill_id}`

Returns:

* skill template
* subskills
* progress state
* next incomplete subskill

### 15.3 Start Stage

`POST /api/stage/start`

Input:

* `user_id`
* `skill_id`
* `subskill_id`
* `stage`

Returns:

* contextualized stage content
* expected rubric
* prompt data

### 15.4 Submit Answer

`POST /api/stage/submit`

Input:

* `user_id`
* `skill_id`
* `subskill_id`
* `stage`
* `answer`

Returns:

* score
* pass/fail
* feedback
* next action

### 15.5 Update Progress

`POST /api/progress/update`

Input:

* evaluation result
* completed step
* mistakes

Returns:

* updated progress
* unlocks
* next recommended step

---

## 16. UI / UX Specification

### 16.1 UI Philosophy

The UI should feel:

* hierarchical
* progressive
* visually motivating
* easy to navigate
* non-technical
* similar to Duolingo-style progression systems

The user should always understand:

* where they are
* what they are learning
* what comes next
* how much progress they have made
* how to go back

The experience should feel like:

* progressing through a career transition journey
* unlocking employable capabilities
* moving toward a target role

The system should avoid:

* complex dashboards
* overwhelming controls
* too many AI/agent concepts exposed to the user
* deeply nested menus

The AI orchestration should remain invisible.

---

### 16.2 Navigation Philosophy

The navigation system should be hierarchical but reversible.

The user progressively drills down into:

```text
Home Dashboard
    ↓
Skill
    ↓
Subskill
    ↓
Stage
```

At every level, the user must be able to:

* go back
* jump directly home
* switch skills
* continue current progress

The navigation should feel lightweight and intuitive.

---

### 16.3 Main Screens

The MVP UI is composed of three core screens:

1. Learning Dashboard
2. Skill Detail Page
3. Active Learning Stage Page

---

# SCREEN 1 — Learning Dashboard

## Purpose

Provide:

* overview
* motivation
* target clarity
* global progress
* access to all active skills

This is the main entry point after onboarding.

---

## Layout Structure

### Top Navigation Bar

Contains:

* Home button
* Current role target
* User profile icon
* Global progress indicator

Example:

```text
[Home]    AI Operations Analyst Journey    Progress 38%
```

---

### Hero Section

Large visual section at the top.

Displays:

* target role
* role icon / illustration
* short motivational text
* estimated readiness percentage

Example:

```text
Target Role
AI Operations Analyst

You are currently 42% compatible with this role.
```

---

### Skills Section

Displays all learning skills as cards.

Each skill card should contain:

* skill name
* icon
* progress bar
* completion percentage
* status
* estimated difficulty

Example:

```text
SQL Foundations
Progress: 60%
Status: In Progress
```

Possible statuses:

* Locked
* Not Started
* In Progress
* Completed

---

### Certification Section

Displays:

* suggested certifications
* linked real-world courses
* certification readiness

Example:

```text
Recommended Certifications
- Google Data Analytics
- AWS Cloud Practitioner
```

This section connects learning with real employability.

---

### Recommended Action Section

Displays the next recommended action.

Example:

```text
Continue Learning
Next Step:
SQL → Business Reporting
```

---

# SCREEN 2 — Skill Detail Page

## Purpose

Allow the user to:

* understand the structure of a skill
* visualize progress
* navigate subskills
* continue the learning path

---

## Layout Structure

### Top Navigation

Should contain:

* Back button
* Home button
* Skill title
* Skill progress

Example:

```text
← Back      SQL Foundations      Home
Progress: 60%
```

---

### Skill Header

Displays:

* skill name
* skill description
* related target capability
* certification relation

Example:

```text
SQL Foundations
Learn how to query and analyze structured business data.
```

---

### Subskills List

Displays all subskills.

Example:

```text
✔ Filtering
✔ Aggregation
⏳ Joins
🔒 Reporting
```

Each subskill should show:

* completion state
* progress
* estimated difficulty
* lock status

---

### Learning Path Visualization

This is the central visual component.

The UI should represent the progression path visually.

Recommended design:

* vertical path
* connected nodes
* Duolingo-style progression path
* glowing/completed states
* animated unlocks

Each subskill node expands into its learning stages.

Example:

```text
Filtering
○ Introduction
○ Conceptual Understanding
○ Practice
○ Evaluation
○ Reflection
```

Completed stages should:

* change color
* show a checkmark
* visually connect to the next stage

Locked stages should:

* appear dimmed
* be inaccessible

---

### Progress Sidebar (Optional)

Can display:

* current mistakes
* weak areas
* current score
* certification readiness

---

# SCREEN 3 — Active Learning Stage Page

## Purpose

Display the current learning interaction.

This is where:

* explanations
* questions
* exercises
* evaluations
* reflections
  occur.

---

## Layout Structure

### Top Bar

Displays:

* skill
* subskill
* current stage
* breadcrumb navigation

Example:

```text
Home > SQL > Filtering > Practice
```

---

### Main Content Area

Displays stage-specific content.

The layout changes depending on the stage type.

---

## Stage Type: Introduction

Displays:

* explanation
* analogy
* examples
* key points

UI Components:

* text blocks
* expandable examples
* highlight boxes

---

## Stage Type: Conceptual Understanding

Displays:

* questions
* answer input
* reasoning prompts

UI Components:

* chat-style answer box
* question cards
* feedback area

---

## Stage Type: Practice

Displays:

* practical exercise
* mini scenario
* expected objective

UI Components:

* task panel
* code editor or answer area
* submit button

---

## Stage Type: Evaluation

Displays:

* score
* pass/fail
* explanation
* unlock state

UI Components:

* score card
* progress update animation
* next step CTA

---

## Stage Type: Reflection

Displays:

* mistakes
* correct reasoning
* reinforcement explanations
* retry recommendations

UI Components:

* mistake cards
* corrected examples
* retry button

---

### Bottom Navigation Area

Always visible.

Contains:

* Previous step
* Next step
* Return to skill
* Return to home

Example:

```text
[Previous]    [Retry]    [Next Step]
```

---

### 16.4 Progress Visualization

Progress should always be visible.

Recommended progress representations:

* global progress bar
* per-skill progress bar
* per-subskill completion state
* stage completion indicators

Progress should feel:

* rewarding
* visual
* tangible

---

### 16.5 UX Constraints

The UI should:

* minimize cognitive overload
* expose only necessary information
* feel guided
* feel progression-oriented
* avoid exposing backend complexity

The user should never need to:

* choose agents
* configure orchestration
* manage prompts
* understand system internals

---

### 16.6 Frontend Technical Requirements

The frontend should support:

* persistent state
* nested navigation
* breadcrumb navigation
* dynamic stage rendering
* progress animations
* unlock logic
* retry logic
* responsive layout

Recommended frontend stack:

* Next.js
* React
* TailwindCSS
* Zustand or Redux for state management
* Framer Motion for transitions/animations

---

### 16.7 Required Frontend State

The frontend should track:

```text
- current_skill
- current_subskill
- current_stage
- completed_stages
- completed_subskills
- progress_percent
- unlocked_states
- scores
- mistakes
- retry_count
```

---

### 16.8 Database Requirements

The system requires persistent storage.

The database should support:

* user profiles
* skill progression
* completed stages
* evaluations
* mistakes
* retries
* unlocked stages
* session history

Recommended MVP database:

* PostgreSQL

Reason:

* structured relational data
* easy progression tracking
* robust querying
* easy integration with modern backend stacks

Optional additions later:

* Redis for caching/session speed
* Vector DB for future recommendation/matching systems

The MVP does NOT require a vector database for the learning pipeline itself.

---

## 17. Prompt Contract Design

Each stage should have a stable prompt contract.

### 17.1 Introduction Prompt

Inputs:

* skill
* subskill
* user background
* analogies

Outputs:

* explanation
* example
* analogy
* key points

### 17.2 Conceptual Prompt

Inputs:

* learning objectives
* known misconceptions
* user background
* rubric

Outputs:

* questions
* expected reasoning
* evaluation criteria

### 17.3 Practical Prompt

Inputs:

* practical task spec
* expected output format
* evaluation method

Outputs:

* task statement
* validation result
* feedback

### 17.4 Reflection Prompt

Inputs:

* user answer
* detected mistakes
* correct reasoning

Outputs:

* mistake summary
* corrected explanation
* reinforcement suggestion

---

## 18. MVP Implementation Strategy

### Recommended MVP shape

Build a demo for a single transition path.

Example:

* operations profile → data/AI operations role
* 3 to 5 skills
* 2 to 4 subskills per skill
* fixed stage pipeline per subskill

### Why this is the right MVP

* enough structure to look real
* enough flexibility to show intelligence
* limited scope for implementation
* easy to debug and demo

### Avoid in the MVP

* too many skills
* fully dynamic curriculum generation
* overcomplicated agent loops
* complex labor market scraping dependency

---

## 19. Recommended Technical Constraints

1. Keep the skill graph hardcoded for the demo.
2. Keep the learning pipeline fixed.
3. Use LLMs for contextualization and conceptual reasoning.
4. Use deterministic logic for progression and completion where possible.
5. Store all user state in a persistent database.
6. Define strict input/output schemas for every stage.
7. Make the frontend expect structured responses.
8. Focus on making the progression feel clear and human.

---

## 20. Open Design Questions

These should be answered before implementation begins:

1. What are the exact first 3–5 skills in the demo path?
2. How many subskills does each skill have?
3. What is the exact mastery threshold for each stage?
4. Which practical tasks can be deterministically evaluated?
5. What fields are stored in user state?
6. What is the exact schema for stage outputs?
7. How should progress percentage be computed?
8. What remediation flow happens after a failed evaluation?
9. How much of the introduction should be templated vs LLM-generated?
10. What is the exact UX layout for skill tracking and progression?

---

## 21. Finalized Architectural Decisions

This section contains the finalized high-level architectural decisions made after the initial specification phase.

---

### 21.1 System Philosophy

The system is NOT:

* an autonomous multi-agent swarm
* a parallel orchestration system
* a fully dynamic curriculum generator

The system IS:

* a structured sequential learning pipeline
* a constrained generation architecture
* a hierarchical curriculum generation system
* a guided adaptive learning platform

The architecture relies on:

* fixed structural scaffolding
* dynamic contextual content generation
* deterministic progression logic
* persistent learning state

---

### 21.2 Core Architectural Principle

The most important architectural principle is:

```text
Dynamic generation inside a finite structure.
```

This means:

* the structure is stable and predictable
* the generated content is adaptive and contextual

The LLM does NOT freely invent arbitrary course structures.
Instead, it fills predefined structures.

This guarantees:

* stable frontend rendering
* predictable state transitions
* easier debugging
* consistent UX
* deterministic persistence

---

### 21.3 Final Program Structure

```text
Program
├── Max 6 Skills
│
├── Each Skill
│   ├── 5 Sequential Subskills
│   │
│   ├── Each Subskill
│   │   ├── Introduction
│   │   ├── Conceptual Understanding
│   │   ├── Practical Exercise
│   │   ├── Evaluation
│   │   └── Reflection / Remediation
```

Important:

* Skills can be learned in parallel.
* Subskills are sequential.
* Stages are sequential.
* Users cannot skip stages.
* Users cannot skip subskills.

---

### 21.4 Skill Design Philosophy

Skills are:

* generated dynamically
* structurally constrained
* workflow-oriented
* employability-oriented

The system should NOT:

* generate random arbitrary skills
* create infinite course structures

Instead:

* the planner generates skills within constraints
* the planner follows predefined structural rules

Example constraints:

* max 6 skills
* exactly 5 subskills
* increasing conceptual complexity
* explicit dependency ordering

---

### 21.5 Subskill Design

Subskills are:

* dynamically generated
* sequentially ordered
* objective-driven

Subskills should contain:

* subskill name
* learning objective
* measurable expected outcome
* dependency information

Subskills are NOT fully hardcoded.
However:

* the generation logic is constrained
* the structure is fixed
* the progression logic is fixed

---

### 21.6 Stage System

Every subskill follows the same stage pipeline.

```text
1. Introduction
2. Conceptual Understanding
3. Practical Exercise
4. Evaluation
5. Reflection / Remediation
```

---

### 21.7 Introduction Stage

Purpose:

* introduce the concept
* create intuition
* contextualize using user background

Format:

* lightweight
* mostly non-interactive
* can include small multiple-choice checks

---

### 21.8 Conceptual Understanding Stage

Purpose:

* evaluate reasoning
* detect misconceptions
* verify conceptual understanding

Interaction style:

* open-ended
* Socratic
* conversational/chat-based

Evaluation:

* rubric-based
* LLM-evaluated

---

### 21.9 Practical Exercise Stage

Purpose:

* evaluate operational capability
* test practical application

Exercise style:

* one larger structured exercise preferred
* deterministic evaluation when possible

Examples:

* SQL queries
* workflow analysis
* scenario completion

---

### 21.10 Evaluation Stage

Evaluation is an independent stage.

The final evaluation:

* aggregates previous stage performance
* combines conceptual and practical understanding
* generates slightly modified evaluation tasks
* determines pass/fail progression

Evaluation outputs:

* continuous numeric score
* pass/fail state
* detected errors
* short feedback

---

### 21.11 Reflection / Remediation Stage

Reflection only appears if the evaluation fails.

This stage is NOT journaling.
It is structured remediation.

Purpose:

* reinforce failed concepts
* target specific mistakes
* retrain weak areas
* prepare retries

Important:

* remediation focuses primarily on final evaluation mistakes
* stage-level micro mistakes are less important for the MVP

Retries:

* infinite retries allowed
* retries generate new exercises around the same error patterns

---

### 21.12 Evaluation Philosophy

The evaluation system is one of the most important components.

Evaluation should be:

* rubric-based
* structured
* semantically grounded
* reusable across skills

The system uses:

* conceptual evaluation framework
* practical evaluation framework
* aggregated final evaluation

---

### 21.13 Rubric Philosophy

Rubrics should be lightweight for the MVP.

Example:

```text
10 criteria
Each criterion scored 0–1
Final aggregated score
```

Optional:

* criterion weights

The rubric structure should be generated and interpreted consistently.

---

### 21.14 Error Memory System

The system stores semantic errors.

The purpose is:

* targeted remediation
* retry generation
* weakness reinforcement

Important MVP simplification:

* focus mainly on final evaluation errors
* do not overcomplicate stage-level memory

Errors:

* persist across retries
* are removed once the user successfully masters the related content

---

### 21.15 Content Generation Engine

This is considered the main bottleneck of the system.

Responsibilities:

* generate stage content
* generate explanations
* generate practical tasks
* generate evaluations
* generate remediation
* contextualize everything to the user background

Generation style:

* modular prompts
* highly structured prompting
* constrained outputs

---

### 21.16 Prompt Architecture

Prompts should NOT be monolithic.

Instead:

* each functionality has its own prompt
* prompts are modular
* prompts are reusable
* prompts are separated by responsibility

Recommended prompt organization:

```text
/prompts
    /planning
    /subskill_generation
    /introduction
    /conceptual
    /practice
    /evaluation
    /reflection
```

---

### 21.17 Curriculum Generation Strategy

The curriculum is generated ONCE.

Generation occurs:

* after target role selection
* after skill gap identification

The generated curriculum is then persisted.

After generation:

* the user simply consumes the generated course
* runtime generation is minimal
* only retries/remediation may regenerate dynamically

This improves:

* consistency
* latency
* cost
* stability

---

### 21.18 Persistent State Philosophy

The database stores:

* current progress
* current position
* unlocked stages
* unlocked subskills
* evaluation results
* final evaluation errors
* system state

The state should allow:

* resume from current stage
* deterministic progression
* persistence across sessions

Important:

* no complex session system required for MVP
* immediate DB updates are acceptable

---

### 21.19 Retry Philosophy

Retries:

* do not overwrite error history immediately
* overwrite progression state
* generate new exercises around failed concepts

Retries should:

* preserve semantic error tracking
* reinforce weak areas
* maintain progression continuity

---

### 21.20 Frontend Philosophy

The frontend should:

* remain simple
* remain predictable
* render stable structures
* avoid exposing AI internals

Recommended interaction style:

* chat-based learning interaction
* guided progression
* gamified but professional UX

The MVP frontend should prioritize:

* simplicity
* clarity
* progression visibility
* navigation

---

### 21.21 Frontend Rendering Philosophy

All stages should use:

* similar base layouts
* predictable rendering patterns
* reusable rendering components

The frontend should receive:

* the whole generated curriculum structure upfront
* all subskills and stages pre-generated

This simplifies:

* navigation
* rendering
* caching
* state persistence

---

### 21.22 Gamification Philosophy

The product should include:

* progression indicators
* visual unlocks
* completion states
* progress bars
* structured advancement

However:

* avoid childish gamification
* maintain professional aesthetics
* keep the product employability-oriented

---

### 21.23 Developer Tooling Philosophy

Developer observability is extremely important.

The system should expose:

```text
Input
→ Prompt
→ Raw Output
→ Parsed Output
→ Evaluation
→ State Update
```

A debugging CLI/dashboard is strongly recommended.

This is essential for:

* prompt iteration
* debugging
* observability
* evaluation tuning

---

### 21.24 Database Philosophy

The learning system DB should primarily store:

* learning state
* progression
* evaluations
* errors
* generated curriculum

The vector database used elsewhere in the platform can remain separate.

The systems can connect using:

* shared user IDs
* shared course IDs

This separation simplifies the MVP.

---

### 21.25 MVP Philosophy

The MVP should prioritize:

* one coherent flow
* stable structure
* believable adaptivity
* clean UX
* deterministic progression

The MVP should avoid:

* overengineering
* infinite flexibility
* excessive autonomy
* unnecessary infrastructure complexity

The system should feel:

* intelligent
* adaptive
* guided
* professional
* employability-oriented

---

## 22. Summary

The product is a structured adaptive learning system for workforce transition.

The architecture combines:

* constrained curriculum generation
* structured pedagogical pipelines
* contextualized AI content generation
* rubric-based evaluation
* persistent progression tracking
* semantic remediation

The core design philosophy is:

```text
Stable structure + dynamic contextual generation.
```

This balance allows the system to:

* feel adaptive and intelligent
* remain implementable
* remain debuggable
* remain frontend-friendly
* remain scalable for future versions
