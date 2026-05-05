from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

STORES_BASE_URL = "https://stores.lidlplus.com/api/"
OFFERS_BASE_URL = "https://offers.lidlplus.com/app/api/"
APP_VERSION = "17.0.5"

COUNTRY_DEFAULTS: dict[str, dict[str, Any]] = {
    "DE": {"language": "de-DE", "latitude": 52.5200, "longitude": 13.4050},
    "AT": {"language": "de-AT", "latitude": 48.2082, "longitude": 16.3738},
    "ES": {"language": "es-ES", "latitude": 40.4168, "longitude": -3.7038},
    "FR": {"language": "fr-FR", "latitude": 48.8566, "longitude": 2.3522},
    "NL": {"language": "nl-NL", "latitude": 52.3676, "longitude": 4.9041},
    "PL": {"language": "pl-PL", "latitude": 52.2297, "longitude": 21.0122},
}


class LidlSettings(BaseSettings):
    model_config: SettingsConfigDict = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="LIDL_",
        extra="ignore",
    )

    stores_base_url: str = STORES_BASE_URL
    offers_base_url: str = OFFERS_BASE_URL
    app_version: str = APP_VERSION
    country: str = Field(default="DE", min_length=2, max_length=2)
    timeout: float = Field(default=20.0, gt=0)
    language: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    @computed_field
    @property
    def normalized_country(self) -> str:
        return self.country.upper()

    @computed_field
    @property
    def defaults(self) -> dict[str, Any]:
        return COUNTRY_DEFAULTS.get(self.normalized_country, COUNTRY_DEFAULTS["DE"])

    @computed_field
    @property
    def resolved_language(self) -> str:
        return self.language or self.defaults["language"]

    @computed_field
    @property
    def resolved_latitude(self) -> float:
        return self.latitude if self.latitude is not None else self.defaults["latitude"]

    @computed_field
    @property
    def resolved_longitude(self) -> float:
        return (
            self.longitude if self.longitude is not None else self.defaults["longitude"]
        )


@lru_cache
def get_settings() -> LidlSettings:
    return LidlSettings()
