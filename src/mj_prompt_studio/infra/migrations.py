from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 1


def apply_migrations(connection: sqlite3.Connection) -> None:
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
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
