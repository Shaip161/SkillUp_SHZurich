"""Simple file-backed persistence layer for TransitionAI learning state."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from SkillUp_SHZurich.Agentic_learning.transition_learning.contracts import (
    ErrorRecord,
    EvaluationResult,
    GeneratedCurriculum,
    ProgressState,
)


@dataclass(frozen=True)
class LearningStateBundle:
    curriculum: GeneratedCurriculum | None
    progress_states: list[ProgressState] = field(default_factory=list)
    evaluation_results: list[EvaluationResult] = field(default_factory=list)
    error_records: list[ErrorRecord] = field(default_factory=list)


class JsonLearningRepository:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.curricula_dir = self.root_dir / "curricula"
        self.progress_dir = self.root_dir / "progress"
        self.evaluations_dir = self.root_dir / "evaluations"
        self.errors_dir = self.root_dir / "errors"
        for directory in (
            self.root_dir,
            self.curricula_dir,
            self.progress_dir,
            self.evaluations_dir,
            self.errors_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def _write_json(self, destination: Path, payload: dict[str, Any]) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(
            payload, indent=2, ensure_ascii=True), encoding="utf-8")
        return destination

    def _read_json(self, source: Path) -> dict[str, Any]:
        return json.loads(source.read_text(encoding="utf-8"))

    @staticmethod
    def _progress_file_name(user_id: str, skill_id: str, subskill_id: str) -> str:
        return f"{user_id}__{skill_id}__{subskill_id}.json"

    def save_curriculum(self, curriculum: GeneratedCurriculum) -> Path:
        return self._write_json(
            self.curricula_dir / f"{curriculum.curriculum_id}.json",
            curriculum.to_dict(),
        )

    def load_curriculum(self, curriculum_id: str) -> GeneratedCurriculum | None:
        source = self.curricula_dir / f"{curriculum_id}.json"
        if not source.is_file():
            return None
        return GeneratedCurriculum.from_mapping(self._read_json(source))

    def save_progress(self, progress: ProgressState) -> Path:
        return self._write_json(
            self.progress_dir /
            self._progress_file_name(
                progress.user_id, progress.skill_id, progress.subskill_id),
            progress.to_dict(),
        )

    def load_progress(self, user_id: str, skill_id: str, subskill_id: str) -> ProgressState | None:
        source = self.progress_dir / \
            self._progress_file_name(user_id, skill_id, subskill_id)
        if not source.is_file():
            return None
        return ProgressState.from_mapping(self._read_json(source))

    def save_evaluation(self, evaluation: EvaluationResult) -> Path:
        return self._write_json(
            self.evaluations_dir / f"{evaluation.evaluation_id}.json",
            evaluation.to_dict(),
        )

    def list_evaluations(
        self,
        *,
        user_id: str,
        skill_id: str | None = None,
        subskill_id: str | None = None,
    ) -> list[EvaluationResult]:
        items: list[EvaluationResult] = []
        for path in sorted(self.evaluations_dir.glob("*.json")):
            record = EvaluationResult.from_mapping(self._read_json(path))
            if record.user_id != user_id:
                continue
            if skill_id is not None and record.skill_id != skill_id:
                continue
            if subskill_id is not None and record.subskill_id != subskill_id:
                continue
            items.append(record)
        return items

    def save_error(self, error: ErrorRecord) -> Path:
        return self._write_json(
            self.errors_dir / f"{error.error_id}.json",
            error.to_dict(),
        )

    def list_errors(
        self,
        *,
        user_id: str,
        skill_id: str | None = None,
        subskill_id: str | None = None,
    ) -> list[ErrorRecord]:
        items: list[ErrorRecord] = []
        for path in sorted(self.errors_dir.glob("*.json")):
            record = ErrorRecord.from_mapping(self._read_json(path))
            if record.user_id != user_id:
                continue
            if skill_id is not None and record.skill_id != skill_id:
                continue
            if subskill_id is not None and record.subskill_id != subskill_id:
                continue
            items.append(record)
        return items

    def load_learning_state(
        self,
        *,
        curriculum_id: str,
        user_id: str,
        skill_id: str | None = None,
        subskill_id: str | None = None,
    ) -> LearningStateBundle:
        curriculum = self.load_curriculum(curriculum_id)
        progress_states: list[ProgressState] = []
        for path in sorted(self.progress_dir.glob("*.json")):
            progress = ProgressState.from_mapping(self._read_json(path))
            if progress.user_id != user_id:
                continue
            if skill_id is not None and progress.skill_id != skill_id:
                continue
            if subskill_id is not None and progress.subskill_id != subskill_id:
                continue
            progress_states.append(progress)
        return LearningStateBundle(
            curriculum=curriculum,
            progress_states=progress_states,
            evaluation_results=self.list_evaluations(
                user_id=user_id,
                skill_id=skill_id,
                subskill_id=subskill_id,
            ),
            error_records=self.list_errors(
                user_id=user_id,
                skill_id=skill_id,
                subskill_id=subskill_id,
            ),
        )
