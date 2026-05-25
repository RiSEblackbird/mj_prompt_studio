from __future__ import annotations

import json
from pathlib import Path

from mj_prompt_studio.config import LLMModelConfig, RuntimeSettings
from mj_prompt_studio.server.app_state import create_state
from mj_prompt_studio.server.main import create_app


def test_committed_openapi_schema_matches_python_api(tmp_path: Path) -> None:
    state = create_state(
        RuntimeSettings(
            data_dir=tmp_path,
            llm_mode="mock",
            response_storage="normal",
            model_config=LLMModelConfig(),
        )
    )
    app = create_app(state)
    expected = app.openapi()
    committed = json.loads(Path("client/src/shared/types/openapi.json").read_text())

    assert committed == expected
    state.context.shutdown()
