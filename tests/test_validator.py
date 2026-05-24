from mj_prompt_studio.domain.prompt_document import PromptDocument, PromptParameters
from mj_prompt_studio.domain.validator import PromptValidator
from mj_prompt_studio.infra.ruleset_loader import load_standard_ruleset


def test_validator_detects_parameter_range_and_unknown_parameter() -> None:
    ruleset = load_standard_ruleset()
    document = PromptDocument.create("project_1", "Validation", ruleset.ruleset_id)
    document.parameters = PromptParameters(stylize=2000, custom={"unsupported": "value"})

    report = PromptValidator().validate(document, ruleset)

    codes = {issue.code for issue in report.issues}
    assert "parameter_above_maximum" in codes
    assert "unsupported_parameter" in codes
    assert report.has_errors
