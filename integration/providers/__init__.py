"""Concrete implementations of the integration ports.

* :class:`MockMatchmakingProvider` -- serves canned System A output for tests
  and the demo runner (no database / external API required).
* :class:`TransitionLearningEngine` -- the real adapter into System B; the only
  module in the integration layer that imports ``Agentic_learning``.
"""

from .mock_matchmaking import MockMatchmakingProvider
from .learning_engine import TransitionLearningEngine

__all__ = ["MockMatchmakingProvider", "TransitionLearningEngine"]
