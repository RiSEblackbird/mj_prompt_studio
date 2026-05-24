from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

from mj_prompt_studio.application.services import (
    ExportService,
    MatrixWorkflowService,
    PromptWorkflowService,
    ReferenceWorkflowService,
    ResultReviewWorkflowService,
)
from mj_prompt_studio.config import (
    LLM_FEATURE_PROFILES_SETTING_KEY,
    LLMFeatureProfile,
    RuntimeSettings,
    load_runtime_settings,
    serialize_feature_profiles,
)
from mj_prompt_studio.domain.prompt_document import PromptDocument
from mj_prompt_studio.infra.asset_store import AssetStore
from mj_prompt_studio.infra.ruleset_loader import load_standard_ruleset
from mj_prompt_studio.infra.secret_store import SecretStore
from mj_prompt_studio.infra.settings_store import SettingsStore
from mj_prompt_studio.infra.sqlite_repository import ProjectRecord, SQLiteRepository
from mj_prompt_studio.llm.job_queue import JobCallable, JobCallback, LLMJob, LLMJobQueue
from mj_prompt_studio.llm.orchestrator import LLMOrchestrator


class AppContext:
    def __init__(self, settings: RuntimeSettings | None = None) -> None:
        self.settings = settings or load_runtime_settings()
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.settings.data_dir / "mj_prompt_studio.sqlite3"
        self.repository = SQLiteRepository(self.db_path)
        self.asset_store = AssetStore(self.settings.data_dir / "assets")
        self.settings_store = SettingsStore(self.settings.data_dir / "settings.json")
        self.secret_store = SecretStore()
        self.ruleset = load_standard_ruleset()
        self.settings = self._load_persisted_llm_settings(self.settings)
        api_key = self.secret_store.read_openai_api_key()
        self.orchestrator = LLMOrchestrator(self.settings, api_key)
        self.job_queue = LLMJobQueue(
            max_workers=self.settings.max_parallel_jobs, on_change=self._persist_job
        )
        self._rebuild_services()
        self.export_service = ExportService()

    def set_session_api_key(self, api_key: str | None) -> None:
        effective_settings = replace(self.settings, llm_mode="real") if api_key else self.settings
        self.orchestrator = LLMOrchestrator(effective_settings, api_key or None)
        self.settings = effective_settings
        self._rebuild_services()

    def set_llm_feature_profiles(self, profiles: dict[str, LLMFeatureProfile]) -> None:
        serialized = serialize_feature_profiles(profiles)
        self.repository.set_setting(LLM_FEATURE_PROFILES_SETTING_KEY, serialized)
        self.settings = self.settings.with_feature_profiles(serialized)
        self.orchestrator = LLMOrchestrator(self.settings, self.orchestrator.api_key)
        self._rebuild_services()

    def _rebuild_services(self) -> None:
        self.prompt_service = PromptWorkflowService(
            self.repository, self.ruleset, self.orchestrator
        )
        self.reference_service = ReferenceWorkflowService(
            self.repository, self.asset_store, self.orchestrator
        )
        self.matrix_service = MatrixWorkflowService(self.repository, self.orchestrator)
        self.result_review_service = ResultReviewWorkflowService(
            self.repository, self.asset_store, self.orchestrator
        )

    def set_response_storage(self, response_storage: str) -> None:
        self.settings = replace(self.settings, response_storage=response_storage)
        self.orchestrator = LLMOrchestrator(self.settings, self.orchestrator.api_key)
        self._rebuild_services()

    def ensure_workspace(self) -> tuple[ProjectRecord, PromptDocument]:
        return self.prompt_service.ensure_default_workspace()

    def submit_agent_job(
        self,
        agent_name: str,
        input_snapshot: dict[str, Any],
        work: JobCallable,
        callback: JobCallback | None = None,
    ) -> LLMJob:
        model, effort = self.orchestrator.agent_route(agent_name)
        return self.job_queue.submit(
            agent_name=agent_name,
            model=model,
            reasoning_effort=effort,
            input_snapshot=input_snapshot,
            work=work,
            callback=callback,
        )

    def export_to_file(self, path: Path, content_factory: Callable[[], str]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content_factory(), encoding="utf-8")
        return path

    def shutdown(self) -> None:
        self.job_queue.shutdown()

    def _persist_job(self, job: LLMJob) -> None:
        self.repository.save_job(job.id, job.agent_name, job.to_dict())

    def _load_persisted_llm_settings(self, settings: RuntimeSettings) -> RuntimeSettings:
        stored_profiles = self.repository.get_setting(LLM_FEATURE_PROFILES_SETTING_KEY, {})
        if not isinstance(stored_profiles, dict):
            return settings
        return settings.with_feature_profiles(stored_profiles)
