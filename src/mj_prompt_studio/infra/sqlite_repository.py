from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mj_prompt_studio.domain.prompt_document import PromptDocument, new_id, utc_now
from mj_prompt_studio.domain.reference import ReferenceAsset, ResultImage, ResultReview
from mj_prompt_studio.infra.migrations import SCHEMA_VERSION, apply_migrations


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
            apply_migrations(connection)

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

    def get_reference(self, reference_id: str) -> ReferenceAsset | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT reference_json FROM reference_assets WHERE id = ?",
                (reference_id,),
            ).fetchone()
        if row is None:
            return None
        return ReferenceAsset.from_dict(json.loads(row["reference_json"]))

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

    def delete_reference(self, reference_id: str) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM reference_assets WHERE id = ?", (reference_id,))

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

    def list_result_images(
        self, project_id: str, prompt_document_id: str | None = None
    ) -> list[ResultImage]:
        query = "SELECT result_json FROM result_images WHERE project_id = ?"
        params: list[str] = [project_id]
        if prompt_document_id:
            query += " AND prompt_document_id = ?"
            params.append(prompt_document_id)
        query += " ORDER BY created_at DESC"
        with self.connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [ResultImage.from_dict(json.loads(row["result_json"])) for row in rows]

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

    def list_result_reviews(self, result_image_id: str | None = None) -> list[ResultReview]:
        query = "SELECT review_json FROM result_reviews"
        params: tuple[str, ...] = ()
        if result_image_id:
            query += " WHERE result_image_id = ?"
            params = (result_image_id,)
        query += " ORDER BY created_at DESC"
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [ResultReview.from_dict(json.loads(row["review_json"])) for row in rows]

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

    def load_user_vocab_profile(self, profile_id: str = "default") -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT profile_json FROM user_vocab_profiles WHERE id = ?",
                (profile_id,),
            ).fetchone()
        if row is None:
            return {}
        return dict(json.loads(row["profile_json"]))

    def save_user_vocab_profile(
        self, profile: dict[str, Any], profile_id: str = "default"
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO user_vocab_profiles (id, profile_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    profile_json=excluded.profile_json,
                    updated_at=excluded.updated_at
                """,
                (profile_id, _to_json(profile), utc_now().isoformat()),
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
            user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        return {
            "db_path": str(self.db_path),
            "schema_version": SCHEMA_VERSION,
            "user_version": int(user_version),
            "tables": [row["name"] for row in tables],
        }


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
