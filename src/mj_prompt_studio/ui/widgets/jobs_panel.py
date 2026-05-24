from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget

from mj_prompt_studio.llm.job_queue import LLMJobQueue


class JobsPanel(QWidget):
    cancel_requested = Signal(str)
    retry_requested = Signal(str)

    def __init__(self, queue: LLMJobQueue) -> None:
        super().__init__()
        self.queue = queue
        self.list_widget = QListWidget()
        self.refresh_button = QPushButton("更新")
        self.cancel_button = QPushButton("キャンセル")
        self.retry_button = QPushButton("再実行")
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(QLabel("Status / Jobs / Validation"))
        header.addStretch(1)
        header.addWidget(self.cancel_button)
        header.addWidget(self.retry_button)
        header.addWidget(self.refresh_button)
        layout.addLayout(header)
        layout.addWidget(self.list_widget)
        self.refresh_button.clicked.connect(self.refresh)
        self.cancel_button.clicked.connect(self._cancel_selected)
        self.retry_button.clicked.connect(self._retry_selected)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def refresh(self) -> None:
        self.list_widget.clear()
        for job in sorted(self.queue.list_jobs(), key=lambda item: item.created_at, reverse=True):
            label = f"{job.agent_name} | {job.status} | {job.model} | {job.reasoning_effort}"
            if job.error_message:
                label += f" | {job.error_message}"
            self.list_widget.addItem(label)
            self.list_widget.item(self.list_widget.count() - 1).setData(
                Qt.ItemDataRole.UserRole, job.id
            )

    def selected_job_id(self) -> str | None:
        row = self.list_widget.currentRow()
        if row < 0:
            return None
        item = self.list_widget.item(row)
        value = item.data(Qt.ItemDataRole.UserRole)
        return str(value) if value else None

    def _cancel_selected(self) -> None:
        job_id = self.selected_job_id()
        if job_id:
            self.cancel_requested.emit(job_id)

    def _retry_selected(self) -> None:
        job_id = self.selected_job_id()
        if job_id:
            self.retry_requested.emit(job_id)
