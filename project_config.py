from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


CONFIG_PATH = Path(__file__).resolve().with_name("config.toml")
LOCAL_CONFIG_PATH = CONFIG_PATH.with_name("config.local.toml")
REQUIRED_SECTIONS = {
    "paths",
    "images",
    "collage",
    "compression",
    "report",
    "pdf",
    "pipeline",
}


def read_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as config_file:
            return tomllib.load(config_file)
    except tomllib.TOMLDecodeError as exc:
        raise SystemExit(f"Invalid TOML in {path}: {exc}") from exc


def merge_config(
    defaults: dict[str, Any], overrides: dict[str, Any]
) -> dict[str, Any]:
    merged = defaults.copy()

    for key, override_value in overrides.items():
        default_value = merged.get(key)
        if isinstance(default_value, dict) and isinstance(override_value, dict):
            merged[key] = merge_config(default_value, override_value)
        else:
            merged[key] = override_value

    return merged


def load_config(
    path: Path = CONFIG_PATH,
    local_path: Path = LOCAL_CONFIG_PATH,
) -> dict[str, Any]:
    try:
        config = read_toml(path)
    except FileNotFoundError as exc:
        raise SystemExit(f"Configuration file not found: {path}") from exc

    if local_path.exists():
        config = merge_config(config, read_toml(local_path))

    missing_sections = sorted(REQUIRED_SECTIONS - config.keys())
    if missing_sections:
        missing = ", ".join(missing_sections)
        raise SystemExit(f"Missing config.toml sections: {missing}")

    return config


CONFIG = load_config()
