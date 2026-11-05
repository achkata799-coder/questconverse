from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from .config import LMStudioConfig


@dataclass
class LMStudioClient:
    config: LMStudioConfig

    def __post_init__(self) -> None:
        self._client = OpenAI(base_url=self.config.base_url, api_key=self.config.api_key)

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> Any:
        return self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            tools=tools,
            tool_choice="auto" if tools else None,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
