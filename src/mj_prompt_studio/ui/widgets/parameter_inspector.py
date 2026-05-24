from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from mj_prompt_studio.domain.prompt_document import PromptParameters
from mj_prompt_studio.domain.ruleset import GenerationRuleset, ParameterSpec


class ParameterInspector(QWidget):
    def __init__(self, ruleset: GenerationRuleset) -> None:
        super().__init__()
        self.ruleset = ruleset
        self.editors: dict[str, QWidget] = {}
        self.apply_button = QPushButton("Parameter Rulesを適用")
        form_group = QGroupBox("Parameter Advisor")
        self.form_layout = QFormLayout(form_group)
        layout = QVBoxLayout(self)
        layout.addWidget(form_group)
        layout.addWidget(self.apply_button)
        layout.addStretch(1)
        self._build()

    def _build(self) -> None:
        for spec in self.ruleset.visible_parameters():
            editor = self._editor_for_spec(spec)
            self.editors[spec.name] = editor
            self.form_layout.addRow(spec.display_name, editor)

    def _editor_for_spec(self, spec: ParameterSpec) -> QWidget:
        if spec.kind == "boolean":
            return QCheckBox()
        if spec.kind == "integer":
            if spec.maximum is not None and spec.maximum > 2_147_483_647:
                return QLineEdit()
            spin = QSpinBox()
            spin.setRange(int(spec.minimum or 0), int(spec.maximum or 999999))
            return spin
        if spec.kind == "enum":
            combo = QComboBox()
            combo.addItems(list(spec.choices))
            return combo
        return QLineEdit()

    def set_parameters(self, parameters: PromptParameters) -> None:
        values = parameters.iter_values()
        for name, editor in self.editors.items():
            value = values.get(name)
            if isinstance(editor, QCheckBox):
                editor.setChecked(bool(value))
            elif isinstance(editor, QSpinBox):
                editor.setValue(int(value or 0))
            elif isinstance(editor, QComboBox):
                index = editor.findText(str(value or ""))
                editor.setCurrentIndex(max(index, 0))
            elif isinstance(editor, QLineEdit):
                editor.setText(str(value or ""))

    def read_parameters(self) -> PromptParameters:
        values: dict[str, object] = {}
        for name, editor in self.editors.items():
            if isinstance(editor, QCheckBox):
                values[name] = editor.isChecked()
            elif isinstance(editor, QSpinBox):
                values[name] = editor.value()
            elif isinstance(editor, QComboBox):
                values[name] = editor.currentText()
            elif isinstance(editor, QLineEdit):
                values[name] = editor.text().strip() or None
        return PromptParameters.from_dict(values)
