from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from PIL import Image

from mj_prompt_studio.config import LLMModelConfig, RuntimeSettings
from mj_prompt_studio.server.app_state import create_state
from mj_prompt_studio.server.main import create_app


def _client(tmp_path: Path) -> TestClient:
    state = create_state(
        RuntimeSettings(
            data_dir=tmp_path,
            llm_mode="mock",
            response_storage="normal",
            model_config=LLMModelConfig(),
        )
    )
    return TestClient(create_app(state))


def _wait_for_job(client: TestClient, job_id: str) -> dict[str, Any]:
    for _attempt in range(40):
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        job = response.json()["job"]
        if job["status"] in {"succeeded", "failed", "cancelled"}:
            return dict(job)
        time.sleep(0.05)
    raise AssertionError(f"job did not finish: {job_id}")


def test_workspace_compile_and_agent_job_use_real_services(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        workspace = client.get("/api/workspace").json()
        document = workspace["document"]

        response = client.post(
            f"/api/prompt-documents/{document['id']}/compile",
            json={
                "user_brief": "朝食広告",
                "blocks": {
                    **document["blocks"],
                    "subject": "croissant and coffee",
                    "lighting": "soft morning window light",
                },
                "parameters": {**document["parameters"], "aspect_ratio": "4:5"},
                "notes": "",
                "tags": [],
            },
        )
        assert response.status_code == 200
        compiled = response.json()["document"]["compiled_prompt"]
        assert "croissant and coffee" in compiled

        job_response = client.post(
            "/api/agents/intent-intake",
            json={"document_id": document["id"], "brief": "高級ホテルの朝食広告"},
        )
        assert job_response.status_code == 200
        job = _wait_for_job(client, job_response.json()["job"]["id"])
        assert job["status"] == "succeeded"
        assert "document" in job["output_json"]


def test_reference_upload_serves_asset_without_local_path(tmp_path: Path) -> None:
    image_path = tmp_path / "reference.png"
    Image.new("RGB", (12, 8), "#F2E7D8").save(image_path)

    with _client(tmp_path / "data") as client:
        workspace = client.get("/api/workspace").json()
        project_id = workspace["project"]["id"]
        with image_path.open("rb") as file:
            response = client.post(
                f"/api/projects/{project_id}/references/upload",
                files={"file": ("reference.png", file, "image/png")},
            )
        assert response.status_code == 200
        reference = response.json()["reference"]
        assert "local_path" not in reference
        assert reference["image_metadata"]["width"] == 12

        asset = client.get(reference["asset_url"])
        assert asset.status_code == 200
        assert asset.content


def test_settings_response_storage_persists_across_contexts(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        response = client.put(
            "/api/settings/response-storage", json={"response_storage": "privacy"}
        )
        assert response.status_code == 200
        assert response.json()["settings"]["privacy_mode"] is True

    with _client(tmp_path) as client:
        settings = client.get("/api/settings").json()["settings"]
        assert settings["response_storage"] == "privacy"
        assert settings["privacy_mode"] is True


def test_openapi_schema_contains_react_contract_endpoints(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        schema = client.get("/openapi.json").json()

    paths = schema["paths"]
    assert "/api/workspace" in paths
    assert "/api/prompt-documents/{document_id}/compile" in paths
    assert "/api/projects/{project_id}/references/upload" in paths
    assert "/api/jobs/{job_id}" in paths
