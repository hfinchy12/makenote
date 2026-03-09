from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import questionary

CONFIG_PATH = Path.home() / ".config" / "makenote" / "config.json"


def config_exists() -> bool:
    return CONFIG_PATH.exists()


def load_config() -> dict:
    with CONFIG_PATH.open() as f:
        return json.load(f)


def save_config(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w") as f:
        json.dump(data, f, indent=2)
