from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from mj_prompt_studio.app.app_context import AppContext


class SettingsWidget(QWidget):
    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self.context = context
        self.connection_label = QLabel("未確認")
        self.privacy_checkbox = QCheckBox("Privacy mode")
        self.privacy_checkbox.setChecked(context.settings.privacy_mode)
        self.test_button = QPushButton("接続テスト")
        form_group = QGroupBox("設定概要")
        form = QFormLayout(form_group)
        form.addRow("AIモデル", QLabel(context.settings.model_config.default_model))
        form.addRow("Current Ruleset", QLabel(context.ruleset.display_name))
        form.addRow("Response Storage", self.privacy_checkbox)
        form.addRow("接続状態", self.connection_label)
        layout = QVBoxLayout(self)
        layout.addWidget(form_group)
        layout.addWidget(self.test_button)
        layout.addStretch(1)
        self.test_button.clicked.connect(self._connection_test)

    def _connection_test(self) -> None:
        ok = self.context.orchestrator.connection_test()
        self.connection_label.setText("有効" if ok else "失敗")
