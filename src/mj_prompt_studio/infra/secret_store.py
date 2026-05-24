from __future__ import annotations

import os


class SecretStore:
    def read_openai_api_key(self) -> str | None:
        value = os.environ.get("OPENAI_API_KEY")
        return value if value else None
