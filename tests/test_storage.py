from pathlib import Path

from mj_prompt_studio.domain.prompt_document import PromptBlocks, PromptDocument
from mj_prompt_studio.infra.sqlite_repository import SQLiteRepository


def test_repository_saves_project_document_and_revision(tmp_path: Path) -> None:
    repo = SQLiteRepository(tmp_path / "test.sqlite3")
    project = repo.create_project("Campaign")
    document = PromptDocument.create(project.id, "Prompt", "internal_default")
    document.blocks = PromptBlocks(subject="coffee cup")
    document.compiled_prompt = "coffee cup --ar 4:5"

    repo.save_prompt_document(document)
    revision = repo.save_prompt_revision(document, "test", "initial")

    loaded = repo.list_prompt_documents(project.id)
    revisions = repo.list_prompt_revisions(document.id)
    assert revision == 1
    assert loaded[0].blocks.subject == "coffee cup"
    assert revisions[0]["compiled_prompt"] == "coffee cup --ar 4:5"
