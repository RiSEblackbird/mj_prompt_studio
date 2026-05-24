from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QListWidget, QPushButton, QVBoxLayout, QWidget

from mj_prompt_studio.domain.prompt_document import ValidationReport


class PromptDoctorPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.issue_list = QListWidget()
        self.patch_list = QListWidget()
        self.run_button = QPushButton("AIで改善案を生成")
        self.run_button.setObjectName("PrimaryButton")
        layout = QVBoxLayout(self)
        issue_group = QGroupBox("Prompt Doctor")
        issue_layout = QVBoxLayout(issue_group)
        issue_layout.addWidget(self.issue_list)
        patch_group = QGroupBox("AI Fix Candidates")
        patch_layout = QVBoxLayout(patch_group)
        patch_layout.addWidget(self.patch_list)
        layout.addWidget(issue_group)
        layout.addWidget(patch_group)
        layout.addWidget(self.run_button)

    def set_validation_report(self, report: ValidationReport | None) -> None:
        self.issue_list.clear()
        if not report:
            self.issue_list.addItem("未検証")
            return
        if not report.issues:
            self.issue_list.addItem("問題なし")
            return
        for issue in report.issues:
            self.issue_list.addItem(f"{issue.severity}: {issue.message}")

    def set_agent_result(self, payload: dict[str, object]) -> None:
        self.patch_list.clear()
        patches = payload.get("patches")
        if isinstance(patches, list):
            for patch in patches:
                if isinstance(patch, dict):
                    self.patch_list.addItem(f"{patch.get('field_path')}: {patch.get('reason')}")
