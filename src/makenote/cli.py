from __future__ import annotations

import sys

import click
import questionary

import makenote.config as _cfg
import makenote.github as _gh


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="mn", message="%(prog)s %(version)s")
@click.pass_context
def main(ctx: click.Context) -> None:
    """mn — fast terminal note logging."""
    if not _cfg.config_exists() and ctx.invoked_subcommand != "config":
        click.echo("No config found. Running first-time setup.")
        _cfg.run_config_flow()
    elif ctx.invoked_subcommand is None:
        # Interactive note flow (mn with no subcommand)
        cfg = _cfg.load_config()
        subjects = cfg.get("subjects", [])
        if not subjects:
            click.echo("Error: no subjects configured. Run mn config to add subjects.")
            sys.exit(1)
        choices = ["Add New", questionary.Separator()] + subjects
        subject = questionary.select("Subject:", choices=choices).ask()
        if subject is None:
            sys.exit(0)
        if subject == "Add New":
            subject = questionary.text("New subject name:").ask()
            if subject is None:
                sys.exit(0)
            subject = subject.strip()
            cfg["subjects"].append(subject)
            _cfg.save_config(cfg)
        note_text = questionary.text("Note:").ask()
        if note_text is None:
            sys.exit(0)
        try:
            _gh.write_note(cfg["repo"], subject, note_text)
        except _gh.GhNotInstalledError:
            click.echo("Error: gh CLI not found. Install from https://cli.github.com")
            sys.exit(1)
        except _gh.GhNotAuthError:
            click.echo("Error: gh not authenticated. Run: gh auth login")
            sys.exit(1)
        except _gh.ShaConflictError:
            click.echo("Error: write conflict — file may have changed. Try again.")
            sys.exit(1)
        click.echo("Note logged.")


@main.command()
def config() -> None:
    """Edit configuration."""
    _cfg.run_config_flow()


@main.command(name="d")
@click.argument("note_text", required=False, default=None)
def default_note(note_text: str | None) -> None:
    """Log a note using the default subject."""
    cfg = _cfg.load_config()
    subject = cfg["default_subject"]
    if note_text is None:
        note_text = questionary.text("Note:").ask()
        if note_text is None:
            sys.exit(0)
    try:
        _gh.write_note(cfg["repo"], subject, note_text)
    except _gh.GhNotInstalledError:
        click.echo("Error: gh CLI not found. Install from https://cli.github.com")
        sys.exit(1)
    except _gh.GhNotAuthError:
        click.echo("Error: gh not authenticated. Run: gh auth login")
        sys.exit(1)
    except _gh.ShaConflictError:
        click.echo("Error: write conflict — file may have changed. Try again.")
        sys.exit(1)
    click.echo("Note logged.")


@main.command(name="list")
def list_notes() -> None:
    """Print recent notes across all subjects."""
    cfg = _cfg.load_config()
    try:
        records = _gh.read_notes(cfg["repo"], cfg.get("subjects", []))
    except _gh.GhNotInstalledError:
        click.echo("Error: gh CLI not found. Install from https://cli.github.com")
        sys.exit(1)
    except _gh.GhNotAuthError:
        click.echo("Error: gh not authenticated. Run: gh auth login")
        sys.exit(1)
    except _gh.ShaConflictError:
        click.echo("Error: write conflict — file may have changed. Try again.")
        sys.exit(1)
    if not records:
        click.echo("No notes found.")
        return
    for r in records:
        note_display = r["note"][:60] + "..." if len(r["note"]) > 60 else r["note"]
        click.echo(f"{r['date']}  {r['subject']:<15}  {note_display}")
