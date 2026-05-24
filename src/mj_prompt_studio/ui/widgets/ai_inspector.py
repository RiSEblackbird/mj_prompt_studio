from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QLabel, QListWidget, QVBoxLayout, QWidget

from mj_prompt_studio.domain.prompt_document import PromptDocument, ValidationReport


class AIInspector(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.intent_label = QLabel("未分析")
        self.missing_list = QListWidget()
        self.weak_list = QListWidget()
        self.next_actions = QListWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(_group("Intent Summary", self.intent_label))
        layout.addWidget(_group("不足している要素", self.missing_list))
        layout.addWidget(_group("弱い表現", self.weak_list))
        layout.addWidget(_group("次のアクション候補", self.next_actions))
        layout.addStretch(1)

    def update_document(self, document: PromptDocument, report: ValidationReport | None) -> None:
        self.intent_label.setText(document.blocks.intent or "未分析")
        self.missing_list.clear()
        self.weak_list.clear()
        self.next_actions.clear()
        if report:
            for issue in report.issues:
                target = self.weak_list if issue.severity == "warning" else self.missing_list
                target.addItem(f"{issue.severity}: {issue.message}")
        self.next_actions.addItems(["AIで構成案を作る", "Prompt Doctorを実行", "Matrix Labで比較"])

    def update_agent_result(self, result: dict[str, object]) -> None:
        self.next_actions.clear()
        actions = result.get("next_actions")
        if isinstance(actions, list):
            self.next_actions.addItems([str(item) for item in actions])


def _group(title: str, widget: QWidget) -> QGroupBox:
    group = QGroupBox(title)
    layout = QVBoxLayout(group)
    layout.addWidget(widget)
    return group
