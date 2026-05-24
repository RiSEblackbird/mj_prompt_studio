from __future__ import annotations

from typing import Any


def format_free_editor_result(
    mode: str, source_text: str, existing_prompt: str, payload: dict[str, Any]
) -> str:
    terms = terms_from_vocabulary_payload(payload)
    base = existing_prompt or source_text
    if mode == "短縮":
        words = base.replace("。", ".").split()
        return " ".join(words[:42]).strip()
    if mode == "構造化":
        return ", ".join(part for part in [base, *terms[:4]] if part)
    if mode == "ルールセット修正":
        return f"{base}, compatible parameter-ready phrasing".strip(", ")
    if mode == "スタイル変換":
        return f"{base}, {', '.join(terms[:3])}, cohesive editorial style".strip(", ")
    if mode == "精密化":
        return f"{base}, specific subject detail, clear lighting, controlled composition".strip(
            ", "
        )
    return f"{base}, {', '.join(terms[:4])}".strip(", ")


def terms_from_vocabulary_payload(payload: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    suggestions = payload.get("suggestions", [])
    if not isinstance(suggestions, list):
        return terms
    for suggestion in suggestions:
        if isinstance(suggestion, dict):
            values = suggestion.get("terms", [])
            if isinstance(values, list):
                terms.extend(str(value) for value in values)
    return terms
