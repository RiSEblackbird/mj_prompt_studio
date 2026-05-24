from __future__ import annotations

import sys

from mj_prompt_studio.app.app_context import AppContext


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency boundary
        raise RuntimeError("PySide6 is required to run the desktop app") from exc

    from mj_prompt_studio.app.main_window import MainWindow

    app = QApplication(sys.argv)
    context = AppContext()
    window = MainWindow(context)
    window.show()
    exit_code = app.exec()
    context.shutdown()
    return int(exit_code)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
