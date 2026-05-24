from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
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

    def __init__(self) -> None:
        super().__init__()
        self.references: dict[str, ReferenceAsset] = {}
        self.list_widget = QListWidget()
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        self.import_button = QPushButton("参照画像を追加")
        self.analyze_button = QPushButton("AI分析")
        self.insert_vocab_button = QPushButton("語彙を使う")
        button_row = QHBoxLayout()
        button_row.addWidget(self.import_button)
        button_row.addWidget(self.analyze_button)
        button_row.addWidget(self.insert_vocab_button)
        button_row.addStretch(1)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Reference Library"))
        layout.addLayout(button_row)
        body = QHBoxLayout()
        body.addWidget(self.list_widget, 1)
        body.addWidget(self.detail, 1)
        layout.addLayout(body, 1)
        self.import_button.clicked.connect(self._choose_file)
        self.analyze_button.clicked.connect(self._request_analysis)
        self.list_widget.currentRowChanged.connect(self._show_current)

    def set_references(self, references: list[ReferenceAsset]) -> None:
        self.references = {reference.id: reference for reference in references}
        self.list_widget.clear()
        for reference in references:
            self.list_widget.addItem(f"{reference.name} | {reference.type}")

    def current_reference(self) -> ReferenceAsset | None:
        row = self.list_widget.currentRow()
        if row < 0:
            return None
        return list(self.references.values())[row]

    def _choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "参照画像を追加")
        if path:
            self.import_requested.emit(path)

    def _request_analysis(self) -> None:
        reference = self.current_reference()
        if reference:
            self.analyze_requested.emit(reference.id)

    def _show_current(self) -> None:
        reference = self.current_reference()
        if not reference:
            self.detail.clear()
            return
        analysis = reference.ai_analysis
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
