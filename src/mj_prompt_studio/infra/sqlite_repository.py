from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mj_prompt_studio.domain.prompt_document import PromptDocument, new_id, utc_now
from mj_prompt_studio.domain.reference import ReferenceAsset, ResultImage, ResultReview


@dataclass
class ProjectRecord:
    id: str
    name: str
    created_at: str
    updated_at: str


class SQLiteRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS prompt_documents (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    prompt_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                );
                CREATE TABLE IF NOT EXISTS prompt_revisions (
                    id TEXT PRIMARY KEY,
                    prompt_document_id TEXT NOT NULL,
                    revision_number INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    prompt_json TEXT NOT NULL,
                    compiled_prompt TEXT NOT NULL,
                    diff_summary TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(prompt_document_id) REFERENCES prompt_documents(id)
                );
                CREATE TABLE IF NOT EXISTS reference_assets (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    reference_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                );
                CREATE TABLE IF NOT EXISTS result_images (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    prompt_document_id TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS result_reviews (
                    id TEXT PRIMARY KEY,
                    result_image_id TEXT NOT NULL,
                    review_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS llm_jobs (
                    id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    job_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS user_vocab_profiles (
                    id TEXT PRIMARY KEY,
                    profile_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS matrix_experiments (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    experiment_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def create_project(self, name: str) -> ProjectRecord:
        now = utc_now().isoformat()
        project = ProjectRecord(id=new_id("project"), name=name, created_at=now, updated_at=now)
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO projects (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (project.id, project.name, project.created_at, project.updated_at),
            )
        return project

    def list_projects(self) -> list[ProjectRecord]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
        return [ProjectRecord(**dict(row)) for row in rows]

    def save_prompt_document(self, document: PromptDocument) -> None:
        document.touch()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO prompt_documents (id, project_id, title, prompt_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    prompt_json=excluded.prompt_json,
                    updated_at=excluded.updated_at
                """,
                (
                    document.id,
                    document.project_id,
                    document.title,
                    _to_json(document.to_dict()),
                    document.updated_at.isoformat(),
                ),
            )

    def list_prompt_documents(self, project_id: str | None = None) -> list[PromptDocument]:
        query = "SELECT prompt_json FROM prompt_documents"
        params: tuple[str, ...] = ()
        if project_id:
            query += " WHERE project_id = ?"
            params = (project_id,)
        query += " ORDER BY updated_at DESC"
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [PromptDocument.from_dict(json.loads(row["prompt_json"])) for row in rows]

    def get_prompt_document(self, document_id: str) -> PromptDocument | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT prompt_json FROM prompt_documents WHERE id = ?", (document_id,)
            ).fetchone()
        if row is None:
            return None
        return PromptDocument.from_dict(json.loads(row["prompt_json"]))

    def save_prompt_revision(
        self,
        document: PromptDocument,
        source: str,
        diff_summary: str,
    ) -> int:
        with self.connect() as connection:
            current = connection.execute(
                """
                SELECT COALESCE(MAX(revision_number), 0)
                FROM prompt_revisions
                WHERE prompt_document_id = ?
                """,
                (document.id,),
            ).fetchone()[0]
            revision_number = int(current) + 1
            connection.execute(
                """
                INSERT INTO prompt_revisions (
                    id, prompt_document_id, revision_number, source, prompt_json,
                    compiled_prompt, diff_summary, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("revision"),
                    document.id,
                    revision_number,
                    source,
                    _to_json(document.to_dict()),
                    document.compiled_prompt,
                    diff_summary,
                    utc_now().isoformat(),
                ),
            )
        return revision_number

    def list_prompt_revisions(self, document_id: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    revision_number, source, prompt_json, compiled_prompt,
                    diff_summary, created_at
                FROM prompt_revisions
                WHERE prompt_document_id = ?
                ORDER BY revision_number
                """,
                (document_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_reference(self, reference: ReferenceAsset) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO reference_assets (id, project_id, reference_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    reference_json=excluded.reference_json,
                    updated_at=excluded.updated_at
                """,
                (
                    reference.id,
                    reference.project_id,
                    _to_json(reference.to_dict()),
                    reference.updated_at.isoformat(),
                ),
            )

    def list_references(self, project_id: str) -> list[ReferenceAsset]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT reference_json
                FROM reference_assets
                WHERE project_id = ?
                ORDER BY updated_at DESC
                """,
                (project_id,),
            ).fetchall()
        return [ReferenceAsset.from_dict(json.loads(row["reference_json"])) for row in rows]

    def save_result_image(self, result: ResultImage) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO result_images VALUES (?, ?, ?, ?, ?)",
                (
                    result.id,
                    result.project_id,
                    result.prompt_document_id,
                    _to_json(result.to_dict()),
                    result.created_at.isoformat(),
                ),
            )

    def save_result_review(self, review: ResultReview) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO result_reviews VALUES (?, ?, ?, ?)",
                (
                    review.id,
                    review.result_image_id,
                    _to_json(review.to_dict()),
                    review.created_at.isoformat(),
                ),
            )

    def save_matrix_experiment(
        self, project_id: str, experiment_id: str, payload: dict[str, Any]
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO matrix_experiments (id, project_id, experiment_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    experiment_json=excluded.experiment_json,
                    updated_at=excluded.updated_at
                """,
                (experiment_id, project_id, _to_json(payload), utc_now().isoformat()),
            )

    def save_job(self, job_id: str, agent_name: str, payload: dict[str, Any]) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO llm_jobs (id, agent_name, job_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    job_json=excluded.job_json,
                    updated_at=excluded.updated_at
                """,
                (job_id, agent_name, _to_json(payload), utc_now().isoformat()),
            )

    def get_setting(self, key: str, default: Any = None) -> Any:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT value_json FROM settings WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return default
        return json.loads(row["value_json"])

    def set_setting(self, key: str, value: Any) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO settings (key, value_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value_json=excluded.value_json,
                    updated_at=excluded.updated_at
                """,
                (key, _to_json(value), utc_now().isoformat()),
            )

    def healthcheck(self) -> dict[str, Any]:
        with self.connect() as connection:
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        return {"db_path": str(self.db_path), "tables": [row["name"] for row in tables]}


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
