"""Example end-to-end workflow runner.

A single command that demonstrates the full path without touching either
subsystem by hand:

    CV  ->  matchmaking (System A)  ->  skill gaps  ->  learning agents (System B)

Run it from the project root with either:

    python integration/run_workflow.py
    python -m SkillUp_SHZurich.integration.run_workflow      # from the parent dir

It uses the canned mock matchmaking output (so no database / API keys are
needed) and the *real* System B learning engine running in its deterministic
mode. It prints the three boundary payloads we care about -- raw matchmaking
output, the transformed payload, and the final agent input -- plus a summary of
the generated curriculum, and writes the full structured trace to
``integration_trace.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Make ``SkillUp_SHZurich.*`` importable when run as a plain script.
_THIS = Path(__file__).resolve()
sys.path.insert(0, str(_THIS.parent.parent.parent))

from SkillUp_SHZurich.integration.adapter import LearningObjective  # noqa: E402
from SkillUp_SHZurich.integration.contracts import TargetRoleInput  # noqa: E402
from SkillUp_SHZurich.integration.logging_utils import CapturingLogger  # noqa: E402
from SkillUp_SHZurich.integration.orchestrator import run_end_to_end  # noqa: E402
from SkillUp_SHZurich.integration.providers import (  # noqa: E402
    MockMatchmakingProvider,
    TransitionLearningEngine,
)

MOCKS = _THIS.parent / "mocks"


def _print_header(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def _pretty(payload) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=True)


def main() -> int:
    cv = json.loads((MOCKS / "mock_cv.json").read_text(encoding="utf-8"))
    jobs = json.loads((MOCKS / "mock_jobs.json").read_text(encoding="utf-8"))

    # One shared logger gives a single trace spanning the integration layer and
    # System B's internal workflow events.
    logger = CapturingLogger()

    # System A behind the matchmaking port (canned), System B behind the
    # learning port (real, deterministic). The orchestrator can't tell.
    matchmaking = MockMatchmakingProvider.from_file(MOCKS / "mock_match_response.json")
    learning_engine = TransitionLearningEngine(logger=logger)

    # The "learning objective" that complements System A's skill gaps.
    objective = LearningObjective(
        target_role=TargetRoleInput(
            role_id="operations-analyst",
            title="Operations Analyst",
            industry="Logistics",
        ),
        curriculum_id="demo-operations-analyst",
    )
    result = run_end_to_end(
        cv=cv,
        jobs=jobs,
        matchmaking=matchmaking,
        learning_engine=learning_engine,
        objective=objective,
        logger=logger,
    )

    _print_header("1. RAW MATCHMAKING OUTPUT  (System A -> integration)")
    print(_pretty(logger.raw_matchmaking_payload))

    _print_header("2. TRANSFORMED PAYLOAD  (adapter: A-output -> B-input)")
    print(_pretty(logger.transformed_payload))

    _print_header("3. FINAL AGENT INPUT  (integration -> System B)")
    print(_pretty(logger.agent_input_payload))

    _print_header("4. RESULT SUMMARY")
    print(f"User:            {result.matchmaking_output.user_id}")
    print(f"Jobs matched:    {len(result.matchmaking_output.matches)}")
    print(f"Skill gaps:      {result.missing_skill_names}")
    print(f"Target role:     {result.learning_request.target_role.title}")
    print(f"Curriculum id:   {result.learning_result.get('curriculum_id')}")
    print(f"Curriculum status: {result.learning_result.get('status')}")
    print(f"Skills taught:   {result.curriculum_skill_names}")

    trace_path = _THIS.parent / "integration_trace.json"
    trace_path.write_text(_pretty(logger.dump()), encoding="utf-8")
    print(f"\nFull structured trace ({len(logger.events)} events) written to {trace_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
