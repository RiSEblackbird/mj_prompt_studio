from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from mj_prompt_studio.domain.reference import ReferenceAsset


class ReferenceLibraryWidget(QWidget):
    import_requested = Signal(str)
    analyze_requested = Signal(str)
    delete_requested = Signal(str)
    tags_save_requested = Signal(str, list)
    vocabulary_insert_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.references: dict[str, ReferenceAsset] = {}
        self.visible_reference_ids: list[str] = []
        self.list_widget = QListWidget()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("参照素材を検索 (タイトル、タグ、語彙)")
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("タグをカンマ区切りで入力")
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        self.import_button = QPushButton("参照画像を追加")
        self.analyze_button = QPushButton("AI分析")
        self.insert_vocab_button = QPushButton("語彙を使う")
        self.save_tags_button = QPushButton("タグ保存")
        self.delete_button = QPushButton("削除")
        button_row = QHBoxLayout()
        button_row.addWidget(self.import_button)
        button_row.addWidget(self.analyze_button)
        button_row.addWidget(self.insert_vocab_button)
        button_row.addWidget(self.save_tags_button)
        button_row.addWidget(self.delete_button)
        button_row.addStretch(1)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Reference Library"))
        layout.addWidget(self.search_edit)
        layout.addLayout(button_row)
        body = QHBoxLayout()
        body.addWidget(self.list_widget, 1)
        detail_layout = QVBoxLayout()
        detail_layout.addWidget(self.tags_edit)
        detail_layout.addWidget(self.detail, 1)
        detail_panel = QWidget()
        detail_panel.setLayout(detail_layout)
        body.addWidget(detail_panel, 1)
        layout.addLayout(body, 1)
        self.import_button.clicked.connect(self._choose_file)
        self.analyze_button.clicked.connect(self._request_analysis)
        self.delete_button.clicked.connect(self._request_delete)
        self.save_tags_button.clicked.connect(self._request_save_tags)
        self.insert_vocab_button.clicked.connect(self._request_insert_vocab)
        self.search_edit.textChanged.connect(lambda _text: self._apply_filter())
        self.list_widget.currentRowChanged.connect(self._show_current)

    def set_references(self, references: list[ReferenceAsset]) -> None:
        self.references = {reference.id: reference for reference in references}
        self._apply_filter()

    def _apply_filter(self) -> None:
        needle = self.search_edit.text().strip().lower()
        self.list_widget.clear()
        self.visible_reference_ids = []
        for reference in self.references.values():
            haystack = " ".join(
                [
                    reference.name,
                    reference.type,
                    " ".join(reference.tags),
                    " ".join(reference.ai_analysis.extracted_vocabulary),
                ]
            ).lower()
            if needle and needle not in haystack:
                continue
            self.visible_reference_ids.append(reference.id)
            self.list_widget.addItem(f"{reference.name} | {reference.type}")

    def current_reference(self) -> ReferenceAsset | None:
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.visible_reference_ids):
            return None
        return self.references.get(self.visible_reference_ids[row])

    def _choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "参照画像を追加")
        if path:
            self.import_requested.emit(path)

    def _request_analysis(self) -> None:
        reference = self.current_reference()
        if reference:
            self.analyze_requested.emit(reference.id)

    def _request_delete(self) -> None:
        reference = self.current_reference()
        if reference:
            self.delete_requested.emit(reference.id)

    def _request_save_tags(self) -> None:
        reference = self.current_reference()
        if not reference:
            return
        tags = [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()]
        self.tags_save_requested.emit(reference.id, tags)

    def _request_insert_vocab(self) -> None:
        reference = self.current_reference()
        if not reference:
            return
        vocabulary = ", ".join(reference.ai_analysis.extracted_vocabulary)
        if vocabulary:
            self.vocabulary_insert_requested.emit(vocabulary)

    def _show_current(self) -> None:
        reference = self.current_reference()
        if not reference:
            self.detail.clear()
            self.tags_edit.clear()
            return
        analysis = reference.ai_analysis
        self.tags_edit.setText(", ".join(reference.tags))
        self.detail.setPlainText(
            "\n".join(
                [
                    f"Name: {reference.name}",
                    f"Mode: {reference.type}",
                    f"Summary: {analysis.summary}",
                    f"Lighting: {analysis.lighting}",
                    f"Composition: {analysis.composition}",
                    f"Vocabulary: {', '.join(analysis.extracted_vocabulary)}",
                ]
            )
        )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.import_requested.emit(url.toLocalFile())
        event.acceptProposedAction()
