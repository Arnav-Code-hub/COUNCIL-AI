from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="COUNCIL_", extra="ignore")
    data_dir: Path = Path("private")
    mode: Literal["simulation", "gemini"] = "simulation"
    service_key: SecretStr = SecretStr("")
    gemini_key: SecretStr = SecretStr("")
    gemini_model: str = ""
    live_quality_approved: bool = False
    timeout_seconds: int = Field(default=45, ge=1, le=120)
    cors_origin: str = "http://127.0.0.1:5173"
    # Docker's host-loopback publishing forwards requests from a bridge address.
    trust_loopback_proxy: bool = False

    @model_validator(mode="after")
    def live_gate(self):
        if self.service_key.get_secret_value() and len(self.service_key.get_secret_value()) < 32:
            raise ValueError("Service key must contain at least 32 characters.")
        if self.mode == "gemini" and not (
            self.live_quality_approved
            and self.gemini_key.get_secret_value()
            and self.gemini_model
            and self.service_key.get_secret_value()
        ):
            raise ValueError(
                "Live mode requires quality approval, model, Gemini key and service key."
            )
        return self
