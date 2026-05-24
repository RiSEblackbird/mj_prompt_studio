from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget


class FreeEditorWidget(QWidget):
    transform_requested = Signal(str, str, str)

    def __init__(self) -> None:
        super().__init__()
        self.source_edit = QPlainTextEdit()
        self.source_edit.setPlaceholderText("日本語ラフ入力 (アイデア・指示)")
        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setPlaceholderText("英語プロンプト (ライブ変換・編集可)")
        transform_row = QHBoxLayout()
        for label in ["語彙強化", "精密化", "短縮", "スタイル変換", "構造化", "ルールセット修正"]:
            button = QPushButton(label)
            button.clicked.connect(
                lambda _checked=False, mode=label: self.transform_requested.emit(
                    mode,
                    self.source_edit.toPlainText().strip(),
                    self.prompt_edit.toPlainText().strip(),
                )
            )
            transform_row.addWidget(button)
        transform_row.addStretch(1)
        editors = QHBoxLayout()
        editors.addWidget(self.source_edit, 1)
        editors.addWidget(self.prompt_edit, 1)
        layout = QVBoxLayout(self)
        layout.addLayout(transform_row)
        layout.addLayout(editors, 1)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("ライブ変換プレビュー")
        layout.addWidget(self.preview)
        self.prompt_edit.textChanged.connect(
            lambda: self.preview.setPlainText(self.prompt_edit.toPlainText())
        )

    def set_transform_result(self, text: str, detail: str) -> None:
        self.prompt_edit.setPlainText(text)
        self.preview.setPlainText("\n".join([text, "", detail]).strip())
