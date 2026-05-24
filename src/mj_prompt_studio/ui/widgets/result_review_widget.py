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

from mj_prompt_studio.domain.reference import ResultReview


class ResultReviewWidget(QWidget):
    import_requested = Signal(str)
    review_requested = Signal()
    audit_requested = Signal()
    compare_requested = Signal()
    next_prompt_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.image_list = QListWidget()
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

    def add_result_image(self, label: str) -> None:
        self.image_list.addItem(label)

    def set_result_images(self, labels: list[str]) -> None:
        self.image_list.clear()
        self.image_list.addItems(labels)

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
