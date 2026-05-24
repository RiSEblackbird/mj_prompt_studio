from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget


class FreeEditorWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.source_edit = QPlainTextEdit()
        self.source_edit.setPlaceholderText("日本語ラフ入力 (アイデア・指示)")
        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setPlaceholderText("英語プロンプト (ライブ変換・編集可)")
        transform_row = QHBoxLayout()
        for label in ["語彙強化", "精密化", "短縮", "スタイル変換", "構造化", "ルールセット修正"]:
            transform_row.addWidget(QPushButton(label))
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
