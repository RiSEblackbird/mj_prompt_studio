from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
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

from mj_prompt_studio.domain.reference import ResultImage, ResultReview


class ResultReviewWidget(QWidget):
    import_requested = Signal(str)
    review_requested = Signal()
    audit_requested = Signal()
    compare_requested = Signal()
    next_prompt_requested = Signal(str)
    result_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.image_list = QListWidget()
        self.result_image_ids: list[str] = []
        self.preview = QLabel("画像プレビュー")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(280)
        self.source_prompt = QPlainTextEdit()
        self.source_prompt.setReadOnly(True)
        self.source_prompt.setPlaceholderText("Source prompt")
        self.parameters_snapshot = QPlainTextEdit()
        self.parameters_snapshot.setReadOnly(True)
        self.parameters_snapshot.setPlaceholderText("Parameters snapshot")
        self.summary = QPlainTextEdit()
        self.summary.setReadOnly(True)
        self.import_button = QPushButton("画像を取り込む")
        self.review_button = QPushButton("AIレビュー")
        self.compare_button = QPushButton("比較")
        self.next_prompt_button = QPushButton("次プロンプト作成")
        self.audit_button = QPushButton("Final Audit")
        self.last_review: ResultReview | None = None
        row = QHBoxLayout()
        for button in [
            self.import_button,
            self.review_button,
            self.compare_button,
            self.next_prompt_button,
            self.audit_button,
        ]:
            row.addWidget(button)
        row.addStretch(1)
        body = QHBoxLayout()
        body.addWidget(self.image_list, 1)
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(self.preview)
        preview_layout.addWidget(QLabel("Source Prompt"))
        preview_layout.addWidget(self.source_prompt, 1)
        preview_layout.addWidget(QLabel("Parameters Snapshot"))
        preview_layout.addWidget(self.parameters_snapshot, 1)
        preview_panel = QWidget()
        preview_panel.setLayout(preview_layout)
        body.addWidget(preview_panel, 2)
        body.addWidget(self.summary, 2)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Result Review"))
        layout.addLayout(row)
        layout.addLayout(body, 1)
        self.import_button.clicked.connect(self._choose_file)
        self.review_button.clicked.connect(self.review_requested.emit)
        self.compare_button.clicked.connect(self.compare_requested.emit)
        self.next_prompt_button.clicked.connect(self._request_next_prompt)
        self.audit_button.clicked.connect(self.audit_requested.emit)
        self.image_list.currentRowChanged.connect(self._emit_selected_image)

    def add_result_image(self, label: str) -> None:
        self.image_list.addItem(label)

    def set_result_images(self, images: list[ResultImage]) -> None:
        self.image_list.clear()
        self.result_image_ids = []
        for image in images:
            label = (
                f"{image.local_path.rsplit('/', 1)[-1]} | "
                f"{image.image_metadata.width}x{image.image_metadata.height}"
            )
            self.result_image_ids.append(image.id)
            self.image_list.addItem(label)
        if images:
            self.set_current_image(images[0])

    def set_current_image(self, image: ResultImage) -> None:
        pixmap = QPixmap(image.local_path)
        if pixmap.isNull():
            self.preview.setText("画像プレビューを表示できません")
        else:
            self.preview.setPixmap(
                pixmap.scaled(
                    520,
                    320,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self.source_prompt.setPlainText(image.prompt_snapshot)
        self.parameters_snapshot.setPlainText(str(image.parameters_snapshot))

    def set_review(self, review: ResultReview) -> None:
        self.last_review = review
        self.summary.setPlainText(
            "\n".join(
                [
                    review.ai_summary,
                    "",
                    "Scores:",
                    *[f"- {key}: {value}" for key, value in review.scores.items()],
                    "",
                    "Strengths:",
                    *[f"- {item}" for item in review.strengths],
                    "",
                    "Issues:",
                    *[f"- {item}" for item in review.issues],
                    "",
                    "Next Prompt Candidates:",
                    *[f"- {item}" for item in review.next_prompt_candidates],
                ]
            )
        )

    def set_audit(self, payload: dict[str, object]) -> None:
        self.summary.setPlainText(str(payload))

    def set_comparison(self, lines: list[str]) -> None:
        self.summary.setPlainText("\n".join(lines))

    def _choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "生成結果画像を取り込む")
        if path:
            self.import_requested.emit(path)

    def _request_next_prompt(self) -> None:
        if not self.last_review or not self.last_review.next_prompt_candidates:
            return
        self.next_prompt_requested.emit(self.last_review.next_prompt_candidates[0])

    def _emit_selected_image(self, row: int) -> None:
        if 0 <= row < len(self.result_image_ids):
            self.result_selected.emit(self.result_image_ids[row])
