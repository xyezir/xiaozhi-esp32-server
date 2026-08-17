from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


class SettingsError(ValueError):
    """Raised when runtime configuration is unsafe or incomplete."""


def _read_secret(name: str, file_name: str) -> str:
    value = os.environ.get(name, "").strip()
    value_file = os.environ.get(file_name, "").strip()
    if value and value_file:
        raise SettingsError(f"configure only one of {name} and {file_name}")
    if value_file:
        try:
            value = Path(value_file).read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise SettingsError(f"{file_name} cannot be read") from exc
    return value


def _bounded_float(name: str, default: float, minimum: float, maximum: float) -> float:
    raw = os.environ.get(name, str(default)).strip()
    try:
        parsed = float(raw)
    except ValueError as exc:
        raise SettingsError(f"{name} must be a number") from exc
    if not math.isfinite(parsed) or not minimum <= parsed <= maximum:
        raise SettingsError(f"{name} must be between {minimum} and {maximum}")
    return parsed


def _bounded_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.environ.get(name, str(default)).strip()
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise SettingsError(f"{name} must be an integer") from exc
    if not minimum <= parsed <= maximum:
        raise SettingsError(f"{name} must be between {minimum} and {maximum}")
    return parsed


def _validate_base_url(value: str, *, allow_insecure_http: bool) -> str:
    normalized = value.strip().rstrip("/")
    parsed = urlsplit(normalized)
    allowed_schemes = {"https"}
    if allow_insecure_http:
        allowed_schemes.add("http")
    if parsed.scheme not in allowed_schemes:
        raise SettingsError("CYJDATA_API_BASE_URL must use https")
    if not parsed.hostname or parsed.username or parsed.password:
        raise SettingsError("CYJDATA_API_BASE_URL must contain a host and no userinfo")
    if parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
        raise SettingsError(
            "CYJDATA_API_BASE_URL must be an origin without path or query"
        )
    return normalized


@dataclass(frozen=True)
class Settings:
    api_base_url: str
    api_key: str
    auth_token: str
    timeout_seconds: float = 2.8
    connect_timeout_seconds: float = 0.8
    cache_ttl_seconds: float = 30.0
    cache_max_entries: int = 128

    @classmethod
    def from_env(cls) -> Settings:
        allow_insecure = os.environ.get(
            "RETRIEVAL_ALLOW_INSECURE_HTTP", ""
        ).strip().lower() in {"1", "true", "yes"}
        base_url = _validate_base_url(
            os.environ.get("CYJDATA_API_BASE_URL", "https://data-admin.petsengine.cn"),
            allow_insecure_http=allow_insecure,
        )
        api_key = _read_secret("CYJDATA_API_KEY", "CYJDATA_API_KEY_FILE")
        if len(api_key) < 16 or api_key.lower() in {
            "change-me",
            "your-api-key",
            "placeholder",
        }:
            raise SettingsError("CYJDATA_API_KEY is missing or invalid")
        auth_token = _read_secret("RETRIEVAL_AUTH_TOKEN", "RETRIEVAL_AUTH_TOKEN_FILE")
        if len(auth_token) < 32 or auth_token.lower() in {
            "change-me",
            "your-auth-token",
            "placeholder",
        }:
            raise SettingsError("RETRIEVAL_AUTH_TOKEN is missing or invalid")
        return cls(
            api_base_url=base_url,
            api_key=api_key,
            auth_token=auth_token,
            timeout_seconds=_bounded_float("RETRIEVAL_TIMEOUT_SECONDS", 2.8, 0.5, 10.0),
            connect_timeout_seconds=_bounded_float(
                "RETRIEVAL_CONNECT_TIMEOUT_SECONDS", 0.8, 0.1, 5.0
            ),
            cache_ttl_seconds=_bounded_float(
                "RETRIEVAL_CACHE_TTL_SECONDS", 30.0, 0.0, 300.0
            ),
            cache_max_entries=_bounded_int("RETRIEVAL_CACHE_MAX_ENTRIES", 128, 0, 2048),
        )
