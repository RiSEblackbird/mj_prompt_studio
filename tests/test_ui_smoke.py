import os

import pytest


def test_main_window_can_be_constructed_with_mock_context(tmp_path):
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

    assert window.windowTitle() == "MJ Prompt Studio"
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
