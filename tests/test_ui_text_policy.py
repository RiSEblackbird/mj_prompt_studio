from scripts.verify_ui_text import FORBIDDEN_PATTERNS

from mj_prompt_studio.ui.strings import USER_VISIBLE_STRINGS


def test_ui_text_does_not_expose_midjourney_version_numbers() -> None:
    for text in USER_VISIBLE_STRINGS:
        assert not any(pattern.search(text) for pattern in FORBIDDEN_PATTERNS), text
