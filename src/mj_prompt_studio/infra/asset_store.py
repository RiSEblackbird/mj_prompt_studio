from __future__ import annotations

import shutil
from pathlib import Path


class AssetStore:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.references_dir = root_dir / "references"
        self.results_dir = root_dir / "results"
        self.references_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def import_reference(self, source_path: Path, asset_id: str) -> Path:
        return self._copy_asset(source_path, self.references_dir, asset_id)

    def import_result(self, source_path: Path, asset_id: str) -> Path:
        return self._copy_asset(source_path, self.results_dir, asset_id)

    def _copy_asset(self, source_path: Path, target_dir: Path, asset_id: str) -> Path:
        if not source_path.exists():
            raise FileNotFoundError(f"Asset not found: {source_path}")
        suffix = source_path.suffix.lower() or ".asset"
        target = target_dir / f"{asset_id}{suffix}"
        shutil.copy2(source_path, target)
        return target
