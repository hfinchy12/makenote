from __future__ import annotations

import datetime
import sys

import click
import questionary

import makenote.config as _cfg
import makenote.github as _gh


def _parse_date(value: str) -> str:
    """Parse and validate a date string. Returns ISO date string or raises click.BadParameter."""
    if value == "yesterday":
        return (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    try:
        parsed = datetime.date.fromisoformat(value)
    except ValueError:
        raise click.BadParameter(f"invalid date '{value}'. Use YYYY-MM-DD or 'yesterday'.")
    if parsed > datetime.date.today():
        raise click.BadParameter(f"date '{value}' cannot be in the future.")
    return parsed.isoformat()


@click.group(invoke_without_command=True)
@click.version_option(package_name="makenote", prog_name="mn", message="%(prog)s %(version)s")
@click.option("--date", "-D", default=None, help="Date for the note (YYYY-MM-DD or 'yesterday'). Defaults to today.")
@click.pass_context
def main(ctx: click.Context, date: str | None) -> None:
    """mn — fast terminal note logging."""
    if not _cfg.config_exists() and ctx.invoked_subcommand != "config":
        click.echo("No config found. Running first-time setup.")
        _cfg.run_config_flow()
    elif ctx.invoked_subcommand is None:
        # Interactive note flow (mn with no subcommand)
        note_date = _parse_date(date) if date is not None else None
        cfg = _cfg.load_config()
        subjects = cfg.get("subjects", [])
        if not subjects:
            click.echo("Error: no subjects configured. Run mn config to add subjects.")
            sys.exit(1)
        choices = subjects + [questionary.Separator(), "Add New"]
        subject = questionary.select("Subject:", choices=choices).ask()
        if subject is None:
            sys.exit(0)
        if subject == "Add New":
            while True:
                subject = questionary.text("New subject name (letters, digits, hyphens, underscores only):").ask()
                if subject is None:
                    sys.exit(0)
                subject = subject.strip()
                try:
                    _gh._validate_subject(subject)
                    break
                except ValueError as e:
                    click.echo(f"Error: {e}")
            cfg["subjects"].append(subject)
            _cfg.save_config(cfg)
        note_text = questionary.text("Note:").ask()
        if note_text is None:
            sys.exit(0)
        try:
            _gh.write_note(cfg["repo"], subject, note_text, date=note_date)
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
@click.option("--date", "-D", default=None, help="Date for the note (YYYY-MM-DD or 'yesterday'). Defaults to today.")
def default_note(note_text: str | None, date: str | None) -> None:
    """Log a note using the default subject."""
    note_date = _parse_date(date) if date is not None else None
    cfg = _cfg.load_config()
    subject = cfg.get("default_subject", "")
    if not subject:
        click.echo("Error: no default subject set. Run mn config to set one.")
        sys.exit(1)
    if note_text is None:
        note_text = questionary.text("Note:").ask()
        if note_text is None:
            sys.exit(0)
    try:
        _gh.write_note(cfg["repo"], subject, note_text, date=note_date)
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


@main.command(name="cal")
def calendar_view() -> None:
    """Interactively browse the past 7 days and log a note for any date."""
    cfg = _cfg.load_config()
    subjects = cfg.get("subjects", [])
    if not subjects:
        click.echo("Error: no subjects configured. Run mn config to add subjects.")
        sys.exit(1)

    subject = questionary.select("Subject:", choices=subjects).ask()
    if subject is None:
        sys.exit(0)

    today = datetime.date.today()
    dates = [(today - datetime.timedelta(days=i)).isoformat() for i in range(7)]
    since = dates[-1]

    try:
        records = _gh.read_notes(cfg["repo"], [subject], since=since)
    except _gh.GhNotInstalledError:
        click.echo("Error: gh CLI not found. Install from https://cli.github.com")
        sys.exit(1)
    except _gh.GhNotAuthError:
        click.echo("Error: gh not authenticated. Run: gh auth login")
        sys.exit(1)

    by_date: dict[str, list[dict]] = {}
    for r in records:
        by_date.setdefault(r["date"], []).append(r)

    choices = []
    for d in dates:
        day_notes = by_date.get(d, [])
        if not day_notes:
            label = f"{d}  (no notes)"
        else:
            first = day_notes[0]["note"]
            preview = first[:50] + "..." if len(first) > 50 else first
            extra = f" (+{len(day_notes) - 1} more)" if len(day_notes) > 1 else ""
            label = f"{d}  {preview}{extra}"
        choices.append(questionary.Choice(title=label, value=d))

    selected_date = questionary.select("Select a date:", choices=choices).ask()
    if selected_date is None:
        sys.exit(0)

    note_text = questionary.text("Note:").ask()
    if note_text is None:
        sys.exit(0)

    try:
        _gh.write_note(cfg["repo"], subject, note_text, date=selected_date)
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
@click.option("--subject", "-s", default=None, help="Filter notes to a single subject.")
def list_notes(subject: str | None) -> None:
    """Print recent notes across all subjects."""
    cfg = _cfg.load_config()
    subjects = cfg.get("subjects", [])
    if subject is not None:
        if subject not in subjects:
            click.echo(f"Error: unknown subject '{subject}'. Run mn config to manage subjects.")
            sys.exit(1)
        subjects = [subject]
    try:
        records = _gh.read_notes(cfg["repo"], subjects)
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
