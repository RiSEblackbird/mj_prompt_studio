from pathlib import Path

from mj_prompt_studio.domain.prompt_document import PromptBlocks, PromptDocument
from mj_prompt_studio.domain.reference import ReferenceAsset, ResultImage, ResultReview
from mj_prompt_studio.infra.migrations import SCHEMA_VERSION
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


def test_repository_tracks_schema_version_and_result_review(tmp_path: Path) -> None:
    repo = SQLiteRepository(tmp_path / "test.sqlite3")
    project = repo.create_project("Campaign")
    document = PromptDocument.create(project.id, "Prompt", "internal_default")
    repo.save_prompt_document(document)
    reference = ReferenceAsset.create(project.id, "Ref", "image_reference", "ref.png")
    repo.save_reference(reference)
    result = ResultImage.create(project.id, document.id, "result.png", "prompt", {})
    review = ResultReview.create(result.id, {"commercial_usability": 8.2}, [], [], [], "ok")

    repo.save_result_image(result)
    repo.save_result_review(review)

    assert repo.healthcheck()["user_version"] == SCHEMA_VERSION
    assert repo.get_reference(reference.id) is not None
    assert repo.list_result_images(project.id)[0].id == result.id
    assert repo.list_result_reviews(result.id)[0].ai_summary == "ok"

    repo.delete_reference(reference.id)
    assert repo.get_reference(reference.id) is None
