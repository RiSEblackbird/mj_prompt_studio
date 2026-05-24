from mj_prompt_studio.domain.matrix import (
    MatrixAxis,
    MatrixGenerator,
    MatrixPlan,
    export_variants_csv,
    export_variants_markdown,
)


def test_matrix_generator_exports_csv_and_markdown() -> None:
    plan = MatrixPlan.create(
        "style comparison",
        {"aspect_ratio": "4:5"},
        [MatrixAxis("stylize", [60, 80]), MatrixAxis("chaos", [0, 5])],
        ["style match"],
    )

    variants = MatrixGenerator().generate(plan, "premium breakfast")

    assert len(variants) == 4
    assert "--s 60" in variants[0].prompt
    assert "prompt" in export_variants_csv(variants)
    assert "Matrix Experiment" in export_variants_markdown(plan, variants)
