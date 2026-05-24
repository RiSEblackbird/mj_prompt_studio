from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget

from mj_prompt_studio.llm.job_queue import LLMJobQueue


class JobsPanel(QWidget):
    def __init__(self, queue: LLMJobQueue) -> None:
        super().__init__()
        self.queue = queue
        self.list_widget = QListWidget()
        self.refresh_button = QPushButton("更新")
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(QLabel("Status / Jobs / Validation"))
        header.addStretch(1)
        header.addWidget(self.refresh_button)
        layout.addLayout(header)
        layout.addWidget(self.list_widget)
        self.refresh_button.clicked.connect(self.refresh)
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
