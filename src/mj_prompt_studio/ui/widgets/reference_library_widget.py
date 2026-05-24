from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
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
        self.mode_filter = QComboBox()
        self.mode_filter.addItems(
            [
                "すべて",
                "Image Reference",
                "Style Reference",
                "Moodboard",
                "Personalization Profile",
                "Palette",
            ]
        )
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("タグをカンマ区切りで入力")
        self.preview = QLabel("プレビュー")
        self.preview.setMinimumHeight(220)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.palette_label = QLabel("")
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
        search_row = QHBoxLayout()
        search_row.addWidget(self.search_edit, 1)
        search_row.addWidget(self.mode_filter)
        layout.addLayout(search_row)
        layout.addLayout(button_row)
        body = QHBoxLayout()
        body.addWidget(self.list_widget, 1)
        detail_layout = QVBoxLayout()
        detail_layout.addWidget(self.preview)
        detail_layout.addWidget(self.palette_label)
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
        self.mode_filter.currentTextChanged.connect(lambda _text: self._apply_filter())
        self.list_widget.currentRowChanged.connect(self._show_current)

    def set_references(self, references: list[ReferenceAsset]) -> None:
        self.references = {reference.id: reference for reference in references}
        self._apply_filter()

    def _apply_filter(self) -> None:
        needle = self.search_edit.text().strip().lower()
        selected_mode = self._selected_mode()
        self.list_widget.clear()
        self.visible_reference_ids = []
        for reference in self.references.values():
            if selected_mode and reference.type != selected_mode:
                continue
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
            self.preview.setText("プレビュー")
            self.palette_label.clear()
            return
        analysis = reference.ai_analysis
        metadata = reference.image_metadata
        self.tags_edit.setText(", ".join(reference.tags))
        self.detail.setPlainText(
            "\n".join(
                [
                    f"Name: {reference.name}",
                    f"Mode: {reference.type}",
                    f"Size: {metadata.width} x {metadata.height} {metadata.format_name}",
                    f"File: {metadata.file_size_bytes} bytes",
                    f"Summary: {analysis.summary}",
                    f"Colors: {', '.join(analysis.colors or metadata.dominant_colors)}",
                    f"Lighting: {analysis.lighting}",
                    f"Composition: {analysis.composition}",
                    f"Vocabulary: {', '.join(analysis.extracted_vocabulary)}",
                ]
            )
        )
        self._show_preview(reference)
        self.palette_label.setText(_palette_html(analysis.colors or metadata.dominant_colors))

    def _show_preview(self, reference: ReferenceAsset) -> None:
        if not reference.local_path:
            self.preview.setText("プレビューなし")
            return
        pixmap = QPixmap(reference.local_path)
        if pixmap.isNull():
            self.preview.setText("画像プレビューを表示できません")
            return
        self.preview.setPixmap(
            pixmap.scaled(
                360,
                220,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _selected_mode(self) -> str | None:
        mapping = {
            "Image Reference": "image_reference",
            "Style Reference": "style_reference",
            "Moodboard": "moodboard",
            "Personalization Profile": "personalization_profile",
            "Palette": "palette",
        }
        return mapping.get(self.mode_filter.currentText())

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.import_requested.emit(url.toLocalFile())
        event.acceptProposedAction()


def _palette_html(colors: list[str]) -> str:
    if not colors:
        return "Palette: 未解析"
    swatches = [
        (
            f'<span style="background:{color}; color:{color}; '
            'border:1px solid #334; padding:2px 14px;">__</span>'
        )
        for color in colors
    ]
    return "Palette: " + " ".join(swatches)
