import os
from dataclasses import dataclass

from prolific_mcp.errors import ConfigurationError

DEFAULT_PROLIFIC_URL = "https://api.prolific.com"
DEFAULT_PROLIFIC_APPLICATION_URL = "https://app.prolific.com"


@dataclass(frozen=True)
class Config:
    token: str
    base_url: str
    app_url: str = DEFAULT_PROLIFIC_APPLICATION_URL

    def masked_token(self) -> str:
        if len(self.token) <= 8:
            return "****"
        return f"{self.token[:4]}…{self.token[-4:]}"


def load_config() -> Config:
    token = os.environ.get("PROLIFIC_TOKEN", "").strip()
    if not token:
        raise ConfigurationError("PROLIFIC_TOKEN environment variable is required")
    base_url = os.environ.get("PROLIFIC_URL", DEFAULT_PROLIFIC_URL).rstrip("/")
    app_url = os.environ.get("PROLIFIC_APPLICATION_URL", DEFAULT_PROLIFIC_APPLICATION_URL).rstrip(
        "/"
    )
    return Config(token=token, base_url=base_url, app_url=app_url)
