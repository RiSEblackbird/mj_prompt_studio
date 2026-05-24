from __future__ import annotations

from collections import Counter
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

from mj_prompt_studio.domain.reference import ImageMetadata


def probe_image(path: Path) -> ImageMetadata:
    file_size = path.stat().st_size if path.exists() else 0
    image = QImage(str(path))
    if image.isNull():
        return ImageMetadata(
            file_size_bytes=file_size,
            format_name=path.suffix.removeprefix(".").upper(),
        )
    return ImageMetadata(
        width=image.width(),
        height=image.height(),
        format_name=path.suffix.removeprefix(".").upper(),
        file_size_bytes=file_size,
        dominant_colors=_dominant_colors(image),
    )


def _dominant_colors(image: QImage) -> list[str]:
    sampled = image.scaled(
        32,
        32,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    counter: Counter[str] = Counter()
    for x in range(sampled.width()):
        for y in range(sampled.height()):
            color = sampled.pixelColor(x, y)
            if color.alpha() < 16:
                continue
            bucket = (
                (color.red() // 32) * 32,
                (color.green() // 32) * 32,
                (color.blue() // 32) * 32,
            )
            counter[_hex_color(bucket)] += 1
    return [color for color, _count in counter.most_common(6)]


def _hex_color(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
