from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SettingsStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return dict(data)

    def save(self, settings: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(settings, file, ensure_ascii=False, indent=2, sort_keys=True)
