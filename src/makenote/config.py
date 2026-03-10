from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import questionary

from makenote.github import GhError, list_subjects

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


def _offer_import_subjects(data: dict) -> None:
    """Offer to import subjects found in the remote repo that aren't local yet."""
    try:
        remote_subjects = list_subjects(data["repo"])
    except GhError as e:
        click.echo(f"Warning: could not fetch remote subjects: {e}")
        return

    new_subjects = [s for s in remote_subjects if s not in data["subjects"]]
    if not new_subjects:
        return

    subject_list = ", ".join(new_subjects)
    answer = questionary.select(
        f"Found {len(new_subjects)} subject(s) in remote repo: {subject_list}. Import all?",
        choices=["Yes", "No"],
    ).ask()
    if answer is None:
        return
    confirmed = answer == "Yes"

    if not confirmed:
        return

    data["subjects"].extend(new_subjects)
    click.echo(f"Imported {len(new_subjects)} subject(s).")


def run_config_flow(existing: dict | None = None) -> None:
    """Interactive config editor. Loops until user selects Save and exit."""
    data = existing.copy() if existing else {"repo": "", "default_subject": "", "subjects": []}

    # Pre-load existing config if it exists and no data passed in
    if existing is None and config_exists():
        data = load_config()

    while True:
        action = questionary.select(
            "Configure makenote:",
            choices=[
                "Set GitHub repo",
                "Set default subject",
                questionary.Separator(),
                "Add subject",
                "Remove subject",
                questionary.Separator(),
                "Save and exit",
            ],
        ).ask()

        if action is None:  # Ctrl-C: exit cleanly, no traceback
            sys.exit(0)

        if action == "Set GitHub repo":
            repo = questionary.text("GitHub repo (owner/repo):").ask()
            if repo is None:
                sys.exit(0)
            data["repo"] = repo.strip()
            _offer_import_subjects(data)

        elif action == "Set default subject":
            if not data["subjects"]:
                click.echo("Error: add at least one subject first.")
                continue
            subject = questionary.select(
                "Default subject:", choices=data["subjects"]
            ).ask()
            if subject is None:
                sys.exit(0)
            data["default_subject"] = subject

        elif action == "Add subject":
            name = questionary.text("New subject name:").ask()
            if name is None:
                sys.exit(0)
            name = name.strip()
            if name and name not in data["subjects"]:
                data["subjects"].append(name)

        elif action == "Remove subject":
            if not data["subjects"]:
                click.echo("Error: no subjects to remove.")
                continue
            to_remove = questionary.select(
                "Remove which subject?", choices=data["subjects"]
            ).ask()
            if to_remove is None:
                sys.exit(0)
            data["subjects"].remove(to_remove)

        elif action == "Save and exit":
            save_config(data)
            break
