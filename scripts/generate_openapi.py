from __future__ import annotations

import json
import tempfile
from pathlib import Path

from mj_prompt_studio.config import LLMModelConfig, RuntimeSettings
from mj_prompt_studio.server.app_state import create_state
from mj_prompt_studio.server.main import create_app


def main() -> int:
    output = Path("client/src/shared/types/openapi.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    settings = RuntimeSettings(
        data_dir=Path(tempfile.mkdtemp(prefix="mjps-openapi-")),
        llm_mode="mock",
        response_storage="normal",
        model_config=LLMModelConfig(),
    )
    app = create_app(create_state(settings))
    output.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    app.state.mjps_state.context.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
