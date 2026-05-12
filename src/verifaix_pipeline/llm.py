from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib import request

from .config import LLMConfig


PROMPT_ROOT = Path(__file__).resolve().parents[2] / "prompts"


class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config

    @property
    def enabled(self) -> bool:
        return self.config.llm_provider != "none"

    def generate_text(self, prompt: str) -> str:
        if self.config.llm_provider == "none":
            raise RuntimeError("LLM provider is disabled")
        if self.config.llm_provider == "openai":
            return self._openai_generate_text(prompt)
        if self.config.llm_provider == "anthropic":
            return self._anthropic_generate_text(prompt)
        raise ValueError(f"Unsupported LLM provider: {self.config.llm_provider}")

    def generate_json(self, prompt: str) -> dict[str, Any]:
        text = self.generate_text(prompt)
        cleaned = strip_markdown_fence(text)
        return json.loads(cleaned)

    def _openai_generate_text(self, prompt: str) -> str:
        api_key = os.environ.get(self.config.api_key_env)
        if not api_key:
            raise RuntimeError(
                f"Missing API key environment variable: {self.config.api_key_env}"
            )

        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            return self._openai_generate_text_http(prompt, api_key)

        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=self.config.model_name,
            input=prompt,
            temperature=self.config.temperature,
        )
        output_text = getattr(response, "output_text", None)
        if output_text:
            return str(output_text)
        return str(response)

    def _openai_generate_text_http(self, prompt: str, api_key: str) -> str:
        body = json.dumps(
            {
                "model": self.config.model_name,
                "input": prompt,
                "temperature": self.config.temperature,
            }
        ).encode("utf-8")
        http_request = request.Request(
            "https://api.openai.com/v1/responses",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with request.urlopen(http_request, timeout=120) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise RuntimeError(_format_http_error("OpenAI", exc)) from exc
        if "output_text" in raw:
            return str(raw["output_text"])

        chunks: list[str] = []
        for item in raw.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"}:
                    chunks.append(str(content.get("text", "")))
        if chunks:
            return "\n".join(chunks)
        return json.dumps(raw)

    def _anthropic_generate_text(self, prompt: str) -> str:
        api_key = os.environ.get(self.config.api_key_env)
        if not api_key:
            raise RuntimeError(
                f"Missing API key environment variable: {self.config.api_key_env}"
            )

        body = json.dumps(
            {
                "model": self.config.model_name,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")
        http_request = request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            method="POST",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )
        try:
            with request.urlopen(http_request, timeout=120) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise RuntimeError(_format_http_error("Anthropic", exc)) from exc

        chunks: list[str] = []
        for item in raw.get("content", []):
            if item.get("type") == "text":
                chunks.append(str(item.get("text", "")))
        if chunks:
            return "\n".join(chunks)
        return json.dumps(raw)


def _format_http_error(provider: str, exc: HTTPError) -> str:
    body = exc.read().decode("utf-8", errors="replace")
    if len(body) > 1000:
        body = body[:1000] + "..."
    return f"{provider} API request failed with HTTP {exc.code}: {body}"


def load_prompt(name: str, **values: str) -> str:
    return render_template(read_prompt_part(name), **values)


def compose_prompt(parts: list[str], **values: str) -> str:
    blocks = [read_prompt_part(part).strip() for part in parts]
    template = "\n\n---\n\n".join(block for block in blocks if block)
    return render_template(template, **values)


def read_prompt_part(name: str) -> str:
    prompt_path = PROMPT_ROOT / name
    return prompt_path.read_text(encoding="utf-8")


def render_template(template: str, **values: str) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()
