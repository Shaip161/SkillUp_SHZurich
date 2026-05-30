"""Minimal retrieval interfaces for quick local RAG-style experiments."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Iterable, Protocol


def _normalize_token(token: str) -> str:
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def _tokenize(text: str) -> set[str]:
    return {
        _normalize_token(token)
        for token in re.findall(r"[a-zA-Z0-9_]+", text.lower())
        if token
    }


@dataclass
class RetrievalItem:
    item_id: str
    text: str
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "text": self.text,
            "score": self.score,
            "metadata": dict(self.metadata),
        }


class Retriever(Protocol):
    def search(self, query: str, *, limit: int = 5) -> list[RetrievalItem]:
        ...


class InMemoryRetriever:
    def __init__(
        self,
        items: Iterable[RetrievalItem | dict[str, Any]],
        *,
        logger: Any = None,
        name: str = "in_memory_retriever",
    ) -> None:
        self._items: list[RetrievalItem] = []
        self._logger = logger
        self.name = name
        for item in items:
            if isinstance(item, RetrievalItem):
                self._items.append(item)
            else:
                self._items.append(RetrievalItem(**dict(item)))

    def search(self, query: str, *, limit: int = 5) -> list[RetrievalItem]:
        started_at = perf_counter()
        query_tokens = _tokenize(query)
        ranked: list[RetrievalItem] = []
        for item in self._items:
            item_tokens = _tokenize(item.text)
            overlap = len(query_tokens & item_tokens)
            if overlap == 0:
                continue
            ranked.append(
                RetrievalItem(
                    item_id=item.item_id,
                    text=item.text,
                    score=float(overlap),
                    metadata=dict(item.metadata),
                )
            )
        ranked.sort(key=lambda item: (-item.score, item.item_id))
        results = ranked[:limit]
        if self._logger is not None:
            self._logger.record(
                "retrieval.search",
                {
                    "retriever": self.name,
                    "query": query,
                    "limit": limit,
                    "result_count": len(results),
                    "duration_ms": round((perf_counter() - started_at) * 1000, 3),
                    "results": [item.to_dict() for item in results],
                    "selected_context": [item.text for item in results],
                },
                level="standard",
            )
        return results
