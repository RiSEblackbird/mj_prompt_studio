from __future__ import annotations

import base64
import json
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class OpenAIResponse:
    output_json: dict[str, Any]
    response_id: str | None


class OpenAIResponsesClient:
    def __init__(self, api_key: str | None = None) -> None:
        try:
            from openai import OpenAI
        except ModuleNotFoundError as exc:  # pragma: no cover - dependency boundary
            raise RuntimeError("openai package is not installed") from exc
        self._client = OpenAI(api_key=api_key)

    def create_response(
        self,
        *,
        model: str,
        input_payload: list[dict[str, Any]],
        reasoning_effort: str,
        text_format: dict[str, Any],
        previous_response_id: str | None,
        store: bool,
    ) -> OpenAIResponse:
        kwargs: dict[str, Any] = {
            "model": model,
            "input": input_payload,
            "reasoning": {"effort": reasoning_effort},
            "text": {"format": text_format},
            "store": store,
        }
        if previous_response_id:
            kwargs["previous_response_id"] = previous_response_id
        response = self._client.responses.create(**kwargs)
        output_text = getattr(response, "output_text", None)
        if not output_text:
            raise ValueError("OpenAI response did not include output_text")
        return OpenAIResponse(
            output_json=json.loads(output_text), response_id=getattr(response, "id", None)
        )

    def connection_test(self, model: str) -> bool:
        test_schema = {
            "type": "json_schema",
            "name": "connection_test",
            "strict": True,
            "schema": {
                "type": "object",
                "required": ["ok"],
                "properties": {"ok": {"type": "boolean"}},
                "additionalProperties": False,
            },
        }
        response = self.create_response(
            model=model,
            input_payload=[{"role": "user", "content": 'Return {"ok": true} as JSON.'}],
            reasoning_effort="low",
            text_format=test_schema,
            previous_response_id=None,
            store=False,
        )
        return bool(response.output_json.get("ok"))


def image_input_item(image_path: Path) -> dict[str, Any]:
    mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return {
        "type": "input_image",
        "image_url": f"data:{mime_type};base64,{encoded}",
    }
