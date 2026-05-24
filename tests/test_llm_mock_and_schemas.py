from mj_prompt_studio.config import LLMModelConfig, RuntimeSettings
from mj_prompt_studio.llm.orchestrator import LLMOrchestrator
from mj_prompt_studio.llm.response_schemas import validate_schema_payload


def test_mock_intent_agent_returns_schema_valid_payload(tmp_path) -> None:
    settings = RuntimeSettings(
        data_dir=tmp_path,
        llm_mode="mock",
        response_storage="normal",
        model_config=LLMModelConfig(),
    )
    orchestrator = LLMOrchestrator(settings)

    result = orchestrator.run_agent("IntentIntakeAgent", {"brief": "高級ホテルの朝食"})

    validate_schema_payload("IntentIntakeAgent", result.output_json)
    assert result.response_id is not None
    assert result.output_json["suggested_parameters"]["aspect_ratio"] == "4:5"


def test_schema_validation_rejects_wrong_types() -> None:
    invalid_payload = {
        "intent": "x",
        "subject": "y",
        "prompt_blocks": {},
        "suggested_parameters": {},
        "missing_decisions": "not a list",
    }

    try:
        validate_schema_payload("IntentIntakeAgent", invalid_payload)
    except Exception as exc:
        assert "missing_decisions" in str(exc)
    else:
        raise AssertionError("schema validation should fail")
