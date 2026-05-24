from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
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
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("環境変数OPENAI_API_KEYがあれば起動時に自動使用")
        self.privacy_checkbox = QCheckBox("Privacy mode")
        self.privacy_checkbox.setChecked(context.settings.privacy_mode)
        self.apply_api_key_button = QPushButton("APIキーをこのセッションに適用")
        self.save_settings_button = QPushButton("設定を保存")
        self.test_button = QPushButton("接続テスト")
        form_group = QGroupBox("設定概要")
        form = QFormLayout(form_group)
        form.addRow("AIモデル", QLabel(context.settings.model_config.default_model))
        form.addRow("Current Ruleset", QLabel(context.ruleset.display_name))
        form.addRow("APIキー", self.api_key_edit)
        form.addRow("Response Storage", self.privacy_checkbox)
        form.addRow("接続状態", self.connection_label)
        layout = QVBoxLayout(self)
        layout.addWidget(form_group)
        layout.addWidget(self.apply_api_key_button)
        layout.addWidget(self.save_settings_button)
        layout.addWidget(self.test_button)
        layout.addStretch(1)
        self.apply_api_key_button.clicked.connect(self._apply_session_api_key)
        self.save_settings_button.clicked.connect(self._save_settings)
        self.test_button.clicked.connect(self._connection_test)
        if context.orchestrator.api_key:
            self.connection_label.setText("環境変数または保存済みキーを検出")

    def _apply_session_api_key(self) -> None:
        self.context.set_session_api_key(self.api_key_edit.text().strip() or None)
        self.connection_label.setText("セッション設定済み")

    def _save_settings(self) -> None:
        storage_mode = "privacy" if self.privacy_checkbox.isChecked() else "normal"
        self.context.repository.set_setting("response_storage", storage_mode)
        self.context.set_response_storage(storage_mode)
        api_key = self.api_key_edit.text().strip()
        if api_key:
            stored = self.context.secret_store.write_openai_api_key(api_key)
            self.context.set_session_api_key(api_key)
            if not stored:
                self.connection_label.setText("設定を保存しました。APIキーはセッションのみ有効です")
                return
        self.connection_label.setText("設定を保存しました")

    def _connection_test(self) -> None:
        ok = self.context.orchestrator.connection_test()
        self.connection_label.setText("有効" if ok else "失敗")
