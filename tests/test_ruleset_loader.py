from mj_prompt_studio.infra.ruleset_loader import load_standard_ruleset


def test_standard_ruleset_hides_internal_identifier() -> None:
    ruleset = load_standard_ruleset()

    assert ruleset.display_name == "Standard Ruleset"
    assert ruleset.ui_expose_identifier is False
    assert ruleset.supports_reference_mode("style_reference")
    assert "aspect_ratio" in ruleset.parameters
