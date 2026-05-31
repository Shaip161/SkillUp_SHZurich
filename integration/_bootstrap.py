"""Import-path bootstrap.

System B is addressed via the absolute namespace ``SkillUp_SHZurich.Agentic_learning.*``
(its own modules import each other that way). For that to resolve, the *parent*
of the project directory must be on ``sys.path``. This helper inserts it idempotently.

Only the entry points that actually need System B (the learning-engine provider,
the test ``conftest``, the example runner) call this -- importing the rest of the
integration layer never triggers it, which keeps a pure contract/adapter import
free of any System B dependency.
"""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_systems_importable() -> None:
    project_root = Path(__file__).resolve().parent.parent  # .../SkillUp_SHZurich
    parent = project_root.parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))
