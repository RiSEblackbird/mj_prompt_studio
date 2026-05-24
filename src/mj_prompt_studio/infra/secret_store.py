from __future__ import annotations

from typing import Any

from mj_prompt_studio.config import read_openai_api_key_from_environment

SERVICE_NAME = "MJ Prompt Studio"
ACCOUNT_NAME = "openai_api_key"


class SecretStore:
    def read_openai_api_key(self) -> str | None:
        value = read_openai_api_key_from_environment()
        if value:
            return value
        keyring = _load_keyring()
        if keyring is None:
            return None
        try:
            stored = keyring.get_password(SERVICE_NAME, ACCOUNT_NAME)
        except Exception:
            return None
        return str(stored) if stored else None

    def write_openai_api_key(self, api_key: str) -> bool:
        keyring = _load_keyring()
        if keyring is None:
            return False
        try:
            keyring.set_password(SERVICE_NAME, ACCOUNT_NAME, api_key)
        except Exception:
            return False
        return True


def _load_keyring() -> Any | None:
    try:
        import keyring  # type: ignore[import-not-found]
    except Exception:
        return None
    return keyring
