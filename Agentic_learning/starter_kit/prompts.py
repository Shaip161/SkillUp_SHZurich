"""Prompt templates and builders for reusable agent workflows."""

from __future__ import annotations

from functools import lru_cache
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .state import RunState, StepRecord
from .tools import ToolRegistry

DEFAULT_PROMPT_TEMPLATE_DIR = Path(__file__).with_name("prompt_templates")
_SECTION_HEADER_PATTERN = re.compile(r"^([A-Z0-9_ ]+):\s*$")
_PLACEHOLDER_PATTERN = re.compile(r"{{\s*([A-Z0-9_]+)\s*}}")


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, indent=2, ensure_ascii=True)


def _format_history(history: list[StepRecord], limit: int = 4) -> str:
    if not history:
        return "NONE"
    lines: list[str] = []
    for entry in history[-limit:]:
        lines.append(
            " | ".join(
                [
                    f"step={entry.step_id}",
                    f"action={entry.action or 'n/a'}",
                    f"status={entry.status}",
                    f"observation={json.dumps(entry.observation, ensure_ascii=True)}",
                ]
            )
        )
    return "\n".join(lines)


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


class PromptCatalog:
    def __init__(self, templates: list[PromptTemplate] | None = None) -> None:
        self._templates: dict[str, PromptTemplate] = {}
        for template in templates or []:
            self.register(template)

    def register(self, template: PromptTemplate) -> None:
        self._templates[template.name] = template

    def get(self, name: str) -> PromptTemplate:
        return self._templates[name]

    def names(self) -> list[str]:
        return sorted(self._templates.keys())

    def load_file(
        self,
        file_path: str | Path,
        *,
        name: str | None = None,
    ) -> PromptTemplate:
        template = PromptTemplate.from_file(file_path, name=name)
        self.register(template)
        return template

    def load_directory(
        self,
        directory: str | Path | None = None,
        *,
        pattern: str = "*.txt",
    ) -> "PromptCatalog":
        template_dir = Path(directory) if directory is not None else DEFAULT_PROMPT_TEMPLATE_DIR
        if not template_dir.is_dir():
            return self
        for path in sorted(template_dir.glob(pattern)):
            self.load_file(path)
        return self

    @classmethod
    def load_builtin(cls) -> "PromptCatalog":
        return cls().load_directory()


@dataclass
class PromptBuilder:
    """Small explicit builder that assembles prompt context around a template."""

    template: PromptTemplate
    history_limit: int = 4
    base_sections: dict[str, Any] = field(default_factory=dict)

    def build_sections(
        self,
        state: RunState,
        tool_registry: ToolRegistry,
        *,
        extra_sections: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        sections: dict[str, Any] = {
            "OBJECTIVE": state.objective,
            "STEP": f"{state.current_step + 1}/{state.max_steps}",
            "STATUS": state.status,
            "AVAILABLE_TOOLS": tool_registry.render_for_prompt(),
            "SHARED_STATE": state.shared,
            "RECENT_HISTORY": _format_history(state.history, limit=self.history_limit),
        }
        sections.update(dict(self.base_sections))
        if extra_sections:
            sections.update(dict(extra_sections))
        return sections

    def build(
        self,
        state: RunState,
        tool_registry: ToolRegistry,
        *,
        extra_sections: dict[str, Any] | None = None,
    ) -> str:
        return self.template.render(
            self.build_sections(
                state,
                tool_registry,
                extra_sections=extra_sections,
            )
        )


def load_prompt_template(
    file_path: str | Path,
    *,
    name: str | None = None,
) -> PromptTemplate:
    return PromptTemplate.from_file(file_path, name=name)


@lru_cache(maxsize=1)
def get_default_prompt_template() -> PromptTemplate:
    return load_prompt_template(DEFAULT_PROMPT_TEMPLATE_DIR / "default_agent.txt", name="default_agent")


def build_agent_prompt(
    state: RunState,
    tool_registry: ToolRegistry,
    *,
    template: PromptTemplate | None = None,
    extra_sections: dict[str, Any] | None = None,
    history_limit: int = 4,
) -> str:
    builder = PromptBuilder(
        template=template or get_default_prompt_template(),
        history_limit=history_limit,
    )
    return builder.build(
        state,
        tool_registry,
        extra_sections=extra_sections,
    )
