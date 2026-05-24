import os

import pytest


def test_main_window_can_be_constructed_with_mock_context(tmp_path):
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QComboBox

    from mj_prompt_studio.app.app_context import AppContext
    from mj_prompt_studio.app.main_window import MainWindow
    from mj_prompt_studio.config import LLMModelConfig, RuntimeSettings

    app = QApplication.instance() or QApplication([])
    context = AppContext(
        RuntimeSettings(
            data_dir=tmp_path,
            llm_mode="mock",
            response_storage="normal",
            model_config=LLMModelConfig(),
        )
    )
    window = MainWindow(context)

    assert window.windowTitle() == "MJ Prompt Studio"
    assert window.undo_action.isEnabled() is False
    assert window.redo_action.isEnabled() is False
    assert window.parameter_inspector.advice_button.text() == "AIで目的別提案"
    table = window.settings_widget.llm_profile_table
    assert table.rowCount() == 9
    model_combo = table.cellWidget(0, 1)
    reasoning_combo = table.cellWidget(0, 2)
    assert isinstance(model_combo, QComboBox)
    assert isinstance(reasoning_combo, QComboBox)
    assert model_combo.currentText() == "gpt-5.5"
    assert reasoning_combo.currentText() == "medium"
    window.close()
    context.shutdown()
    app.quit()


def test_ai_patch_is_not_applied_without_user_confirmation(tmp_path):
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from mj_prompt_studio.app.app_context import AppContext
    from mj_prompt_studio.app.main_window import MainWindow
    from mj_prompt_studio.config import LLMModelConfig, RuntimeSettings

    app = QApplication.instance() or QApplication([])
    context = AppContext(
        RuntimeSettings(
            data_dir=tmp_path,
            llm_mode="mock",
            response_storage="normal",
            model_config=LLMModelConfig(),
        )
    )
    window = MainWindow(context)
    window.document.blocks.style = "original style"

    window._handle_job_completed(
        "VocabularyAgent",
        {
            "suggestions": [],
            "patches": [
                {
                    "field_path": "blocks.style",
                    "old_value": "original style",
                    "new_value": "changed style",
                    "reason": "test",
                    "confidence": 0.8,
                    "requires_user_confirmation": True,
                }
            ],
        },
    )

    assert window.document.blocks.style == "original style"
    assert len(window.pending_patches) == 1
    window.close()
    context.shutdown()
    app.quit()
