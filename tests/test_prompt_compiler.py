from mj_prompt_studio.domain.prompt_compiler import PromptCompiler
from mj_prompt_studio.domain.prompt_document import PromptBlocks, PromptDocument, PromptParameters
from mj_prompt_studio.infra.ruleset_loader import load_standard_ruleset


def test_prompt_compiler_orders_body_and_parameters() -> None:
    ruleset = load_standard_ruleset()
    document = PromptDocument.create("project_1", "Breakfast", ruleset.ruleset_id)
    document.blocks = PromptBlocks(
        intent="premium editorial product photography",
        subject="croissant and coffee cup",
        lighting="soft morning window light",
        text_in_image=["HOTEL MORNING"],
        positive_constraints="unoccupied table",
    )
    document.parameters = PromptParameters(
        aspect_ratio="4:5",
        raw=True,
        stylize=80,
        chaos=5,
        weird=0,
        seed=123456,
    )

    result = PromptCompiler().compile(document, ruleset)

    assert result.prompt.startswith("premium editorial product photography")
    assert '"HOTEL MORNING"' in result.prompt
    assert result.prompt.endswith("--ar 4:5 --raw --s 80 --c 5 --weird 0 --seed 123456")
    assert result.token_estimate > 0
