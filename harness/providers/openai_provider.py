"""OpenAI provider implementation.

Wraps openai.OpenAI(). Translates between normalized harness messages and
OpenAI's Chat Completions API. Reads OPENAI_API_KEY from environment via
SDK defaults; never directly.

The harness never references the openai SDK class; it only imports through
harness.providers.create_provider().
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI

from harness.providers.base import (
    GenerationResult,
    Message,
    ToolCall,
    ToolResult,
    ToolSpec,
)


class OpenAIProvider:
    """OpenAI-backed ModelProvider implementation."""

    name = "openai"

    def __init__(self, model: str):
        self.model = model
        self._client = OpenAI()

    def generate(
        self,
        system: str,
        messages: List[Message],
        tools: List[ToolSpec],
        output_schema: Optional[Dict[str, Any]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.2,
    ) -> GenerationResult:
        openai_messages = self._to_openai_messages(system, messages)
        openai_tools = self._to_openai_tools(tools) if tools else None

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if openai_tools:
            kwargs["tools"] = openai_tools
            kwargs["tool_choice"] = "auto"

        # Force JSON object output. This applies to the model's TEXT response;
        # tool calls are unaffected. Requires the word "JSON" in the prompt
        # (the system prompt's "## Output" section satisfies this).
        kwargs["response_format"] = {"type": "json_object"}

        t0 = time.time()
        completion = self._client.chat.completions.create(**kwargs)
        latency_ms = int((time.time() - t0) * 1000)

        choice = completion.choices[0]
        message = choice.message
        tool_calls: List[ToolCall] = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments or "{}"),
                    )
                )

        return GenerationResult(
            text=message.content,
            tool_calls=tool_calls,
            stop_reason=choice.finish_reason or "",
            model=self.model,
            provider=self.name,
            input_tokens=completion.usage.prompt_tokens if completion.usage else None,
            output_tokens=completion.usage.completion_tokens if completion.usage else None,
            latency_ms=latency_ms,
            raw=None,
        )

    def _to_openai_messages(self, system: str, messages: List[Message]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = [{"role": "system", "content": system}]
        for m in messages:
            if m.role == "user":
                content = m.content if isinstance(m.content, str) else json.dumps(m.content)
                out.append({"role": "user", "content": content})
            elif m.role == "assistant":
                msg: Dict[str, Any] = {"role": "assistant"}
                if isinstance(m.content, str) and m.content:
                    msg["content"] = m.content
                if m.tool_calls:
                    msg["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in m.tool_calls
                    ]
                out.append(msg)
            elif m.role == "tool":
                tr: ToolResult = m.content
                out.append({
                    "role": "tool",
                    "tool_call_id": tr.call_id,
                    "content": json.dumps(tr.result),
                })
        return out

    def _to_openai_tools(self, tools: List[ToolSpec]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]
