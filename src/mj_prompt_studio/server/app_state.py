from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from mj_prompt_studio.app.app_context import AppContext
from mj_prompt_studio.config import RuntimeSettings
from mj_prompt_studio.domain.matrix import MatrixPlan, MatrixVariant
from mj_prompt_studio.domain.prompt_document import PromptDocument
from mj_prompt_studio.infra.sqlite_repository import ProjectRecord


@dataclass
class AppState:
    context: AppContext
    project: ProjectRecord | None = None
    document: PromptDocument | None = None
    matrix_plan: MatrixPlan | None = None
    matrix_variants: list[MatrixVariant] = field(default_factory=list)
    undo_stack: list[dict[str, Any]] = field(default_factory=list)
    redo_stack: list[dict[str, Any]] = field(default_factory=list)
    latest_auto_suggestion_text: str = ""
    lock: RLock = field(default_factory=RLock)

    def ensure_workspace(self) -> tuple[ProjectRecord, PromptDocument]:
        with self.lock:
            if self.project is None or self.document is None:
                self.project, self.document = self.context.ensure_workspace()
            return self.project, self.document

    def set_workspace(self, project: ProjectRecord, document: PromptDocument) -> None:
        with self.lock:
            self.project = project
            self.document = document
            self.undo_stack.clear()
            self.redo_stack.clear()

    def get_document(self, document_id: str) -> PromptDocument:
        document = self.context.repository.get_prompt_document(document_id)
        if document is None:
            raise KeyError(document_id)
        with self.lock:
            if self.document and self.document.id == document.id:
                self.document = document
        return document

    def set_document(self, document: PromptDocument) -> None:
        with self.lock:
            self.document = document

    def push_undo(self, document: PromptDocument) -> None:
        with self.lock:
            self.undo_stack.append(document.to_dict())
            self.undo_stack = self.undo_stack[-30:]
            self.redo_stack.clear()

    def undo(self, document_id: str) -> PromptDocument:
        with self.lock:
            if not self.undo_stack:
                raise ValueError("Undo stack is empty")
            current = self.get_document(document_id)
            self.redo_stack.append(current.to_dict())
            restored = PromptDocument.from_dict(self.undo_stack.pop())
        self.context.repository.save_prompt_document(restored)
        self.context.repository.save_prompt_revision(restored, "undo", "Undoを実行")
        self.set_document(restored)
        return restored

    def redo(self, document_id: str) -> PromptDocument:
        with self.lock:
            if not self.redo_stack:
                raise ValueError("Redo stack is empty")
            current = self.get_document(document_id)
            self.undo_stack.append(current.to_dict())
            restored = PromptDocument.from_dict(self.redo_stack.pop())
        self.context.repository.save_prompt_document(restored)
        self.context.repository.save_prompt_revision(restored, "redo", "Redoを実行")
        self.set_document(restored)
        return restored


def create_state(settings: RuntimeSettings | None = None) -> AppState:
    return AppState(context=AppContext(settings))
