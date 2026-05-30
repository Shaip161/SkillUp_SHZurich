"""Minimal prompt template helpers for backend learning workflows."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_SECTION_HEADER_PATTERN = re.compile(r"^([A-Z0-9_ ]+):\s*$")
_PLACEHOLDER_PATTERN = re.compile(r"{{\s*([A-Z0-9_]+)\s*}}")


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, indent=2, ensure_ascii=True)


def _parse_template_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_title: str | None = None
    current_lines: list[str] = []

    for raw_line in str(text).splitlines():
        header_match = _SECTION_HEADER_PATTERN.match(raw_line.strip())
        if header_match is not None:
            if current_title is not None:
                sections[current_title] = "\n".join(current_lines).strip()
            current_title = header_match.group(1).strip()
            current_lines = []
            continue
        current_lines.append(raw_line)

    if current_title is not None:
        sections[current_title] = "\n".join(current_lines).strip()

    if sections:
        return sections
    return {"PROMPT": str(text).strip()}


def _render_placeholders(text: str, dynamic_sections: dict[str, Any]) -> tuple[str, set[str]]:
    used_keys: set[str] = set()

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        used_keys.add(key)
        return _stringify(dynamic_sections.get(key, ""))

    return _PLACEHOLDER_PATTERN.sub(_replace, text), used_keys


@dataclass
class PromptTemplate:
    """Named prompt template composed from explicit sections or a template file."""

    name: str
    sections: dict[str, str] = field(default_factory=dict)
    source_path: str | None = None

    @classmethod
    def from_text(
        cls,
        name: str,
        text: str,
        *,
        source_path: str | Path | None = None,
    ) -> "PromptTemplate":
        return cls(
            name=name,
            sections=_parse_template_sections(text),
            source_path=str(source_path) if source_path else None,
        )

    @classmethod
    def from_file(
        cls,
        file_path: str | Path,
        *,
        name: str | None = None,
    ) -> "PromptTemplate":
        path = Path(file_path)
        text = path.read_text(encoding="utf-8")
        template_name = name or path.stem
        return cls.from_text(template_name, text, source_path=path)

    def render_sections(self, dynamic_sections: dict[str, Any] | None = None) -> dict[str, str]:
        normalized_dynamic_sections = dict(dynamic_sections or {})
        rendered_sections: dict[str, str] = {}
        consumed_keys: set[str] = set()

        for title, content in self.sections.items():
            normalized_title = str(title).strip()
            rendered_content, used_keys = _render_placeholders(
                _stringify(content),
                normalized_dynamic_sections,
            )
            consumed_keys.update(used_keys)
            stripped_content = rendered_content.strip()
            if stripped_content:
                rendered_sections[normalized_title] = stripped_content

        for key, value in normalized_dynamic_sections.items():
            normalized_key = str(key).strip()
            if not normalized_key or normalized_key in rendered_sections or normalized_key in consumed_keys:
                continue
            normalized_value = _stringify(value)
            if normalized_value:
                rendered_sections[normalized_key] = normalized_value
        return rendered_sections

    def render(self, dynamic_sections: dict[str, Any] | None = None) -> str:
        lines: list[str] = []
        for title, content in self.render_sections(dynamic_sections).items():
            if not content:
                continue
            lines.append(f"{title}:\n{content}")
        return "\n\n".join(lines).strip()
