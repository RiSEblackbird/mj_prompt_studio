from pathlib import Path

from PIL import Image

from mj_prompt_studio.app.app_context import AppContext
from mj_prompt_studio.config import LLMModelConfig, RuntimeSettings


def test_reference_import_records_local_image_metadata(tmp_path: Path) -> None:
    image_path = tmp_path / "reference.png"
    Image.new("RGB", (20, 10), "#F2E7D8").save(image_path)

    context = AppContext(
        RuntimeSettings(
            data_dir=tmp_path / "data",
            llm_mode="mock",
            response_storage="normal",
            model_config=LLMModelConfig(),
        )
    )
    project, _document = context.ensure_workspace()
    reference = context.reference_service.import_reference(project.id, image_path)

    assert reference.image_metadata.width == 20
    assert reference.image_metadata.height == 10
    assert reference.image_metadata.dominant_colors
    context.shutdown()
