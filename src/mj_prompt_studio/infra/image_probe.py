from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import cast

from PIL import Image, UnidentifiedImageError

from mj_prompt_studio.domain.reference import ImageMetadata


def probe_image(path: Path) -> ImageMetadata:
    file_size = path.stat().st_size if path.exists() else 0
    try:
        with Image.open(path) as image:
            return ImageMetadata(
                width=image.width,
                height=image.height,
                format_name=(image.format or path.suffix.removeprefix(".")).upper(),
                file_size_bytes=file_size,
                dominant_colors=_dominant_colors(image),
            )
    except (FileNotFoundError, UnidentifiedImageError, OSError):
        return ImageMetadata(
            file_size_bytes=file_size,
            format_name=path.suffix.removeprefix(".").upper(),
        )


def _dominant_colors(image: Image.Image) -> list[str]:
    sampled = image.convert("RGBA")
    sampled.thumbnail((32, 32))
    counter: Counter[str] = Counter()
    get_flattened_data = getattr(sampled, "get_flattened_data", None)
    raw_pixels = get_flattened_data() if callable(get_flattened_data) else sampled.getdata()
    pixels = cast(Iterable[tuple[int, int, int, int]], raw_pixels)
    for red, green, blue, alpha in pixels:
        if alpha < 16:
            continue
        bucket = (
            (red // 32) * 32,
            (green // 32) * 32,
            (blue // 32) * 32,
        )
        counter[_hex_color(bucket)] += 1
    return [color for color, _count in counter.most_common(6)]


def _hex_color(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
