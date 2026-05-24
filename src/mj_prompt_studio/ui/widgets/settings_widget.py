from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mj_prompt_studio.app.app_context import AppContext
from mj_prompt_studio.config import (
    AVAILABLE_LLM_MODELS,
    LLM_FEATURE_DISPLAY_NAMES,
    LLM_FEATURE_IDS,
    REASONING_EFFORTS,
    VOCABULARY_AMOUNT_LABELS,
    VOCABULARY_AMOUNTS,
    LLMFeatureProfile,
)


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
        self.llm_profile_table = QTableWidget(len(LLM_FEATURE_IDS), 4)
        form_group = QGroupBox("設定概要")
        form = QFormLayout(form_group)
        form.addRow("AIモデル", QLabel("Default: gpt-5.5 / medium"))
        form.addRow("Current Ruleset", QLabel(context.ruleset.display_name))
        form.addRow("APIキー", self.api_key_edit)
        form.addRow("Response Storage", self.privacy_checkbox)
        form.addRow("接続状態", self.connection_label)
        llm_group = QGroupBox("機能別LLM設定")
        llm_layout = QVBoxLayout(llm_group)
        self._build_llm_profile_table()
        llm_layout.addWidget(self.llm_profile_table)
        layout = QVBoxLayout(self)
        layout.addWidget(form_group)
        layout.addWidget(llm_group)
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
        self.context.set_llm_feature_profiles(self._read_llm_profiles())
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

    def _build_llm_profile_table(self) -> None:
        self.llm_profile_table.setHorizontalHeaderLabels(["機能", "モデル", "推論強度", "語彙量"])
        self.llm_profile_table.verticalHeader().setVisible(False)
        self.llm_profile_table.setAlternatingRowColors(True)
        header = self.llm_profile_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        for row, feature_id in enumerate(LLM_FEATURE_IDS):
            profile = self.context.settings.feature_profile_for(feature_id)
            item = QTableWidgetItem(LLM_FEATURE_DISPLAY_NAMES[feature_id])
            item.setData(Qt.ItemDataRole.UserRole, feature_id)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.llm_profile_table.setItem(row, 0, item)
            self.llm_profile_table.setCellWidget(
                row, 1, self._combo_box(list(AVAILABLE_LLM_MODELS), profile.model)
            )
            self.llm_profile_table.setCellWidget(
                row, 2, self._combo_box(list(REASONING_EFFORTS), profile.reasoning_effort)
            )
            vocabulary_labels = [VOCABULARY_AMOUNT_LABELS[value] for value in VOCABULARY_AMOUNTS]
            self.llm_profile_table.setCellWidget(
                row,
                3,
                self._combo_box(
                    vocabulary_labels,
                    VOCABULARY_AMOUNT_LABELS[profile.vocabulary_amount],
                ),
            )

    def _combo_box(self, values: list[str], current: str) -> QComboBox:
        combo = QComboBox()
        combo.addItems(values)
        combo.setCurrentText(current)
        return combo

    def _read_llm_profiles(self) -> dict[str, LLMFeatureProfile]:
        label_to_vocabulary = {label: value for value, label in VOCABULARY_AMOUNT_LABELS.items()}
        profiles: dict[str, LLMFeatureProfile] = {}
        for row in range(self.llm_profile_table.rowCount()):
            item = self.llm_profile_table.item(row, 0)
            if item is None:
                continue
            feature_id = item.data(Qt.ItemDataRole.UserRole)
            if not isinstance(feature_id, str):
                continue
            vocabulary_label = self._combo_at(row, 3).currentText()
            profiles[feature_id] = LLMFeatureProfile(
                model=self._combo_at(row, 1).currentText(),
                reasoning_effort=self._combo_at(row, 2).currentText(),
                vocabulary_amount=label_to_vocabulary.get(vocabulary_label, "standard"),
            )
        return profiles

    def _combo_at(self, row: int, column: int) -> QComboBox:
        widget = self.llm_profile_table.cellWidget(row, column)
        if not isinstance(widget, QComboBox):
            raise RuntimeError("LLM設定テーブルの選択欄を読み取れません。")
        return widget
