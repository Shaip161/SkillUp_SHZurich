"""Run the TransitionAI Zurich workflow demo from the repository root."""

from __future__ import annotations

import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parent


def _bootstrap_agentic_learning() -> None:
    agentic_learning_root = _project_root() / "Agentic_learning"
    if str(agentic_learning_root) not in sys.path:
        sys.path.insert(0, str(agentic_learning_root))


def main() -> None:
    _bootstrap_agentic_learning()
    from starter_kit.examples.transition_demo import main as run_demo

    run_demo()


if __name__ == "__main__":
    main()
