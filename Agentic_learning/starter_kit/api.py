"""Small JSON API layer for non-LLM service calls."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class JsonApiRequest:
    url: str
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)
    payload: dict[str, Any] | None = None
    timeout_seconds: int = 30


@dataclass
class JsonApiResponse:
    ok: bool
    status_code: int
    headers: dict[str, str]
    data: Any = None
    text: str = ""
    error: str | None = None


class JsonApiClient:
    def send(self, request: JsonApiRequest) -> JsonApiResponse:
        headers = dict(request.headers)
        body: bytes | None = None
        if request.payload is not None:
            headers.setdefault("Content-Type", "application/json")
            body = json.dumps(request.payload).encode("utf-8")

        prepared_request = Request(
            url=request.url,
            data=body,
            headers=headers,
            method=request.method.upper(),
        )

        try:
            with urlopen(prepared_request, timeout=request.timeout_seconds) as response:
                raw_bytes = response.read()
                text = raw_bytes.decode("utf-8") if raw_bytes else ""
                return JsonApiResponse(
                    ok=True,
                    status_code=int(getattr(response, "status", 200)),
                    headers={str(key): str(value)
                             for key, value in response.headers.items()},
                    data=self._parse_json(text),
                    text=text,
                )
        except HTTPError as exc:
            text = exc.read().decode("utf-8") if exc.fp else ""
            return JsonApiResponse(
                ok=False,
                status_code=exc.code,
                headers={str(key): str(value)
                         for key, value in exc.headers.items()},
                data=self._parse_json(text),
                text=text,
                error=str(exc),
            )
        except URLError as exc:
            return JsonApiResponse(
                ok=False,
                status_code=0,
                headers={},
                error=str(exc),
            )

    @staticmethod
    def _parse_json(text: str) -> Any:
        if not text.strip():
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
