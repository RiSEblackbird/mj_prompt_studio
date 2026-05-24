from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mj_prompt_studio.config import RuntimeSettings
from mj_prompt_studio.llm.mock_client import MockLLMClient
from mj_prompt_studio.llm.openai_client import OpenAIResponsesClient, image_input_item
from mj_prompt_studio.llm.response_schemas import schema_for_agent, validate_schema_payload


@dataclass(frozen=True)
class AgentResult:
    agent_name: str
    output_json: dict[str, Any]
    response_id: str | None
    model: str
    reasoning_effort: str


class LLMOrchestrator:
    def __init__(self, settings: RuntimeSettings, api_key: str | None = None) -> None:
        self.settings = settings
        self.api_key = api_key
        self.mock_client = MockLLMClient()
        self.real_client: OpenAIResponsesClient | None = None
        if settings.llm_mode == "real" and api_key:
            self.real_client = OpenAIResponsesClient(api_key)

    def run_agent(
        self,
        agent_name: str,
        payload: dict[str, Any],
        *,
        previous_response_id: str | None = None,
        image_paths: list[Path] | None = None,
    ) -> AgentResult:
        model, effort = self._route(agent_name)
        if self.real_client is None:
            mock_response = self.mock_client.create_agent_response(agent_name, payload)
            output = mock_response.output_json
            response_id: str | None = mock_response.response_id
        else:
            openai_response = self.real_client.create_response(
                model=model,
                input_payload=self._build_input(agent_name, payload, image_paths or []),
                reasoning_effort=effort,
                text_format=schema_for_agent(agent_name),
                previous_response_id=None if self.settings.privacy_mode else previous_response_id,
                store=not self.settings.privacy_mode,
            )
            output = openai_response.output_json
            response_id = openai_response.response_id
        validate_schema_payload(agent_name, output)
        return AgentResult(agent_name, output, response_id, model, effort)

    def connection_test(self) -> bool:
        if self.real_client is None:
            return True
        return self.real_client.connection_test(self.settings.model_config.default_model)

    def agent_route(self, agent_name: str) -> tuple[str, str]:
        return self._route(agent_name)

    def _route(self, agent_name: str) -> tuple[str, str]:
        config = self.settings.model_config
        if agent_name in {"ReferenceAnalyzerAgent", "ResultReviewAgent"}:
            return config.vision_model, "high"
        if agent_name == "FinalAuditorAgent":
            return config.deep_review_model, "high"
        if agent_name in {"PromptCompilerAgent", "IntentIntakeAgent", "MatrixPlannerAgent"}:
            return config.default_model, "medium"
        if agent_name == "VocabularyAgent":
            return config.inline_model, "low"
        return config.default_model, "medium"

    def _build_input(
        self, agent_name: str, payload: dict[str, Any], image_paths: list[Path]
    ) -> list[dict[str, Any]]:
        content: list[dict[str, Any] | str] = [
            f"You are {agent_name} for MJ Prompt Studio. Return only schema-valid JSON.",
            {"type": "input_text", "text": _redacted_payload(payload)},
        ]
        content.extend(image_input_item(path) for path in image_paths)
        return [{"role": "user", "content": content}]


def _redacted_payload(payload: dict[str, Any]) -> str:
    safe_payload = {
        key: ("<redacted>" if "key" in key.lower() or "token" in key.lower() else value)
        for key, value in payload.items()
    }
    return str(safe_payload)
