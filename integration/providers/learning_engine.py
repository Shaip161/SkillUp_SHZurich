"""The real adapter into System B (the Learning Agent System).

This is the single point of coupling to ``Agentic_learning``. The import is
performed lazily inside the constructor so that merely importing the integration
layer (contracts, adapter, orchestrator) never requires System B to be on the
path -- only code that actually *runs* a curriculum does.

``TransitionLearningEngine`` satisfies the :class:`integration.ports.LearningEngine`
protocol: it takes a validated :class:`LearningRequest` and returns the generated
curriculum as a plain dict. It translates the contract into System B's native
kwargs (System B accepts plain mappings via its ``from_mapping`` constructors),
threads the integration logger into System B's ``WorkflowServices`` so both
layers share one trace, and optionally wires System B's JSON repository for
persistence.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .._bootstrap import ensure_systems_importable
from ..contracts import LearningRequest
from ..ports import StructuredLogger


class TransitionLearningEngine:
    """Wraps System B's ``generate_curriculum`` behind the LearningEngine port.

    Parameters
    ----------
    logger:
        Optional structured logger; threaded into System B's
        ``WorkflowServices`` so System B's own events land in the same trace.
    persist_dir:
        Optional directory. When given, System B's ``JsonLearningRepository``
        persists the generated curriculum there.
    llm:
        Optional System B LLM seam. Left ``None`` -> System B runs its
        deterministic fallback (no external API calls).
    """

    def __init__(
        self,
        *,
        logger: StructuredLogger | None = None,
        persist_dir: str | Path | None = None,
        llm: Any = None,
    ) -> None:
        ensure_systems_importable()
        # Lazy imports: only happen once System B is actually wanted.
        from SkillUp_SHZurich.Agentic_learning.starter_kit.workflow import WorkflowServices
        from SkillUp_SHZurich.Agentic_learning.transition_learning.offline_generation import (
            generate_curriculum,
        )

        self._generate_curriculum = generate_curriculum
        self._logger = logger

        extras: dict[str, Any] = {}
        if persist_dir is not None:
            from SkillUp_SHZurich.Agentic_learning.transition_learning.persistence import (
                JsonLearningRepository,
            )

            extras["repository"] = JsonLearningRepository(persist_dir)

        self._services = WorkflowServices(llm=llm, logger=logger, extras=extras)

    def generate(self, request: LearningRequest) -> Mapping[str, Any]:
        """Run System B's curriculum generation for a validated request."""
        # System B's ``from_mapping`` constructors accept plain dicts, so we
        # dump the contract rather than importing System B's dataclasses here.
        curriculum = self._generate_curriculum(
            user_profile=request.user_profile.model_dump(),
            target_role=request.target_role.model_dump(),
            missing_skills=[gap.model_dump() for gap in request.missing_skills],
            curriculum_id=request.curriculum_id,
            services=self._services,
        )
        return curriculum.to_dict()
