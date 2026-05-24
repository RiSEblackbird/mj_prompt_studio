from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from mj_prompt_studio.domain.prompt_document import PromptBlocks, PromptDocument

BLOCK_LABELS = [
    ("intent", "Intent"),
    ("subject", "Subject"),
    ("action_state", "Action / State"),
    ("environment", "Environment"),
    ("composition", "Composition"),
    ("camera_lens", "Camera / Lens"),
    ("lighting", "Lighting"),
    ("material_texture", "Material / Texture"),
    ("color_palette", "Color Palette"),
    ("style", "Style"),
    ("text_in_image", "Text in Image"),
    ("positive_constraints", "Positive Constraints"),
    ("notes", "Notes"),
]


class ComposerWidget(QWidget):
    brief_requested = Signal(str)
    compile_requested = Signal()
    vocabulary_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.brief_edit = QPlainTextEdit()
        self.brief_edit.setPlaceholderText("日本語で制作意図を入力")
        self.build_brief_button = QPushButton("AIで構成案を作る")
        self.build_brief_button.setObjectName("PrimaryButton")
        self.compile_button = QPushButton("Compile")
        self.copy_button = QPushButton("コピー")
        self.block_edits: dict[str, QLineEdit] = {}
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.compiled_prompt = QPlainTextEdit()
        self.compiled_prompt.setReadOnly(True)
        self.suggestions = QPlainTextEdit()
        self.suggestions.setReadOnly(True)
        self._build_layout()
        self.build_brief_button.clicked.connect(
            lambda: self.brief_requested.emit(self.brief_text())
        )
        self.compile_button.clicked.connect(self.compile_requested.emit)

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        brief_group = QGroupBox("AI Brief (日本語でざっくり入力)")
        brief_layout = QHBoxLayout(brief_group)
        brief_layout.addWidget(self.brief_edit, 1)
        brief_layout.addWidget(self.build_brief_button)
        layout.addWidget(brief_group)
        blocks_group = QGroupBox("プロンプト構成ブロック")
        blocks_grid = QGridLayout(blocks_group)
        for row, (field_name, label) in enumerate(BLOCK_LABELS):
            edit = QLineEdit()
            edit.textChanged.connect(self._update_preview_from_blocks)
            ai_button = QPushButton("AI補完")
            ai_button.clicked.connect(
                lambda _checked=False, editor=edit: self.vocabulary_requested.emit(editor.text())
            )
            self.block_edits[field_name] = edit
            blocks_grid.addWidget(QLabel(label), row, 0)
            blocks_grid.addWidget(edit, row, 1)
            blocks_grid.addWidget(ai_button, row, 2)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(blocks_group)
        layout.addWidget(scroll, 3)
        lower = QHBoxLayout()
        preview_group = _text_group("Live Prompt Preview", self.preview)
        compiled_group = _text_group("Compiled Prompt (最終プロンプト)", self.compiled_prompt)
        lower.addWidget(preview_group, 1)
        lower.addWidget(compiled_group, 1)
        layout.addLayout(lower, 2)
        button_row = QHBoxLayout()
        button_row.addWidget(self.compile_button)
        button_row.addWidget(self.copy_button)
        button_row.addStretch(1)
        layout.addLayout(button_row)
        layout.addWidget(_text_group("AI Suggestions", self.suggestions), 1)

    def brief_text(self) -> str:
        return self.brief_edit.toPlainText().strip()

    def update_document(self, document: PromptDocument) -> None:
        self.brief_edit.setPlainText(document.user_brief)
        for field_name, edit in self.block_edits.items():
            value = getattr(document.blocks, field_name)
            if isinstance(value, list):
                edit.setText(", ".join(value))
            else:
                edit.setText(str(value))
        self.preview.setPlainText(self._preview_text())
        self.compiled_prompt.setPlainText(document.compiled_prompt)

    def read_blocks(self) -> PromptBlocks:
        data: dict[str, object] = {}
        for field_name, edit in self.block_edits.items():
            value = edit.text().strip()
            data[field_name] = (
                [item.strip() for item in value.split(",") if item.strip()]
                if field_name == "text_in_image"
                else value
            )
        return PromptBlocks.from_dict(data)

    def set_suggestions(self, payload: dict[str, object]) -> None:
        self.suggestions.setPlainText(str(payload))

    def _update_preview_from_blocks(self) -> None:
        self.preview.setPlainText(self._preview_text())

    def _preview_text(self) -> str:
        blocks = self.read_blocks()
        parts: list[str] = []
        for field_name, value in blocks.as_ordered_items():
            if field_name == "notes":
                continue
            if isinstance(value, list):
                parts.extend(value)
            elif value:
                parts.append(value)
        return ", ".join(parts)


def _text_group(title: str, widget: QWidget) -> QGroupBox:
    group = QGroupBox(title)
    layout = QVBoxLayout(group)
    layout.addWidget(widget)
    return group
