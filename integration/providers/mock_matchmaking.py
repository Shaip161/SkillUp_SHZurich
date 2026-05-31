"""A matchmaking provider backed by canned data.

Lets the whole A -> B workflow run end-to-end without standing up System A's
database, embedding model, or Adzuna/Anthropic credentials. It satisfies the
:class:`integration.ports.MatchmakingProvider` protocol, so the orchestrator
cannot tell it apart from a real backend client.

The canned payload must conform to the :class:`MatchmakingOutput` contract; the
orchestrator validates it just as it would real System A output, so the mock
exercises the same validation path as production.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


class MockMatchmakingProvider:
    """Returns a fixed System A payload regardless of the CV / jobs passed in.

    Parameters
    ----------
    payload:
        A mapping shaped like ``MatchmakingOutput``.
    """

    def __init__(self, payload: Mapping[str, Any]) -> None:
        self._payload = dict(payload)

    @classmethod
    def from_file(cls, path: str | Path) -> "MockMatchmakingProvider":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data)

    def run(self, *, cv: Any, jobs: Any) -> Mapping[str, Any]:
        # The inputs are ignored by the mock, but a real provider would consume
        # them. We keep the signature identical so the swap is transparent.
        return dict(self._payload)
