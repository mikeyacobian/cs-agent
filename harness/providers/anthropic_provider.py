"""Anthropic provider implementation.

Wraps anthropic.Anthropic(). Translates between normalized harness messages
and Anthropic's Messages API. Reads ANTHROPIC_API_KEY from environment via
SDK defaults; never directly.

The harness never references the anthropic SDK class; it only imports
through harness.providers.create_provider().
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from anthropic import Anthropic

from harness.providers.base import (
    GenerationResult,
    Message,
    ToolCall,
    ToolResult,
    ToolSpec,
)


class AnthropicProvider:
    """Anthropic-backed ModelProvider implementation."""

    name = "claude"

    def __init__(self, model: str):
        self.model = model
        self._client = Anthropic()

    def generate(
        self,
        system: str,
        messages: List[Message],
        tools: List[ToolSpec],
        output_schema: Optional[Dict[str, Any]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.2,
    ) -> GenerationResult:
        anthropic_messages = self._to_anthropic_messages(messages)
        anthropic_tools = self._to_anthropic_tools(tools) if tools else None

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "system": system,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        t0 = time.time()
        response = self._client.messages.create(**kwargs)
        latency_ms = int((time.time() - t0) * 1000)

        text_parts: List[str] = []
        tool_calls: List[ToolCall] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input or {},
                    )
                )

        return GenerationResult(
            text="\n".join(text_parts) if text_parts else None,
            tool_calls=tool_calls,
            stop_reason=response.stop_reason or "",
            model=self.model,
            provider=self.name,
            input_tokens=response.usage.input_tokens if response.usage else None,
            output_tokens=response.usage.output_tokens if response.usage else None,
            latency_ms=latency_ms,
            raw=None,
        )

    def _to_anthropic_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for m in messages:
            if m.role == "user":
                content = m.content if isinstance(m.content, str) else json.dumps(m.content)
                out.append({"role": "user", "content": content})
            elif m.role == "assistant":
                content_blocks: List[Dict[str, Any]] = []
                if isinstance(m.content, str) and m.content:
                    content_blocks.append({"type": "text", "text": m.content})
                for tc in m.tool_calls:
                    content_blocks.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    })
                if content_blocks:
                    out.append({"role": "assistant", "content": content_blocks})
            elif m.role == "tool":
                tr: ToolResult = m.content
                out.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tr.call_id,
                        "content": json.dumps(tr.result),
                        "is_error": tr.is_error,
                    }],
                })
        return out

    def _to_anthropic_tools(self, tools: List[ToolSpec]) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
            }
            for t in tools
        ]
