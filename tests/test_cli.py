import json
import pytest
from click.testing import CliRunner
from makenote.github import GhNotInstalledError, GhNotAuthError


@pytest.mark.xfail(strict=False, reason="not yet implemented")
def test_version():
    from makenote.cli import main
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == "mn 0.1.0"


@pytest.mark.xfail(strict=False, reason="not yet implemented")
def test_help():
    from makenote.cli import main
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "config" in result.output
    # Minimal output: no long descriptions
    assert len(result.output.splitlines()) < 20


@pytest.mark.xfail(strict=False, reason="not yet implemented")
def test_first_run_triggers_config(tmp_path, monkeypatch):
    """mn with no config file auto-triggers the config flow."""
    from makenote.cli import main
    monkeypatch.setattr("makenote.config.CONFIG_PATH", tmp_path / "config.json")
    called = []
    monkeypatch.setattr("makenote.config.run_config_flow", lambda: called.append(True))
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert called, "run_config_flow was not called on first run"


@pytest.mark.xfail(strict=False, reason="not yet implemented")
def test_config_cmd_no_double_trigger(tmp_path, monkeypatch):
    """mn config with no config does NOT auto-trigger setup AND then run config again."""
    from makenote.cli import main
    monkeypatch.setattr("makenote.config.CONFIG_PATH", tmp_path / "config.json")
    called = []
    monkeypatch.setattr("makenote.config.run_config_flow", lambda: called.append(True))
    runner = CliRunner()
    runner.invoke(main, ["config"])
    # run_config_flow called exactly once (from the config subcommand, not auto-trigger)
    assert len(called) == 1


@pytest.mark.xfail(strict=False, reason="not yet implemented")
def test_config_cmd_exists():
    """mn config subcommand is registered and reachable."""
    from makenote.cli import main
    runner = CliRunner()
    result = runner.invoke(main, ["config", "--help"])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(tmp_path, repo="owner/repo", default_subject="work", subjects=None):
    """Write a temp config.json and return its path."""
    if subjects is None:
        subjects = ["work", "personal"]
    config = {
        "repo": repo,
        "default_subject": default_subject,
        "subjects": subjects,
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    return config_path


class _MockAsk:
    """Helper to mock a questionary select/text call returning a fixed value."""
    def __init__(self, return_value):
        self._value = return_value

    def ask(self):
        return self._value


# ---------------------------------------------------------------------------
# New CLI tests — CORE-01 through CORE-04 and UX-02
# ---------------------------------------------------------------------------

def test_mn_interactive(tmp_path, monkeypatch):
    """mn with no args shows subject picker; selecting subject + note text logs the note."""
    from makenote.cli import main

    config_path = _make_config(tmp_path)
    monkeypatch.setattr("makenote.config.CONFIG_PATH", config_path)

    # Track write_note calls
    calls = []
    monkeypatch.setattr("makenote.cli._gh.write_note", lambda repo, subject, note: calls.append((repo, subject, note)))

    # questionary.select returns "work", questionary.text returns "my note"
    select_calls = iter(["work"])
    text_calls = iter(["my note"])

    monkeypatch.setattr("makenote.cli.questionary.select", lambda *a, **kw: _MockAsk(next(select_calls)))
    monkeypatch.setattr("makenote.cli.questionary.text", lambda *a, **kw: _MockAsk(next(text_calls)))

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, [])

    assert result.exit_code == 0
    assert "Note logged." in result.output
    assert len(calls) == 1
    assert calls[0] == ("owner/repo", "work", "my note")


def test_subject_picker_add_new(tmp_path, monkeypatch):
    """Selecting 'Add New' prompts for name, saves to config, uses it for the note."""
    from makenote.cli import main

    config_path = _make_config(tmp_path)
    monkeypatch.setattr("makenote.config.CONFIG_PATH", config_path)

    write_note_calls = []
    monkeypatch.setattr("makenote.cli._gh.write_note", lambda repo, subject, note: write_note_calls.append((repo, subject, note)))

    save_config_calls = []
    original_save = __import__("makenote.config", fromlist=["save_config"]).save_config

    def capturing_save(data):
        save_config_calls.append(data.copy())
        original_save(data)

    monkeypatch.setattr("makenote.config.CONFIG_PATH", config_path)
    monkeypatch.setattr("makenote.cli._cfg.save_config", capturing_save)

    select_iter = iter(["Add New"])
    text_iter = iter(["health", "ran 5k"])

    monkeypatch.setattr("makenote.cli.questionary.select", lambda *a, **kw: _MockAsk(next(select_iter)))
    monkeypatch.setattr("makenote.cli.questionary.text", lambda *a, **kw: _MockAsk(next(text_iter)))

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, [])

    assert result.exit_code == 0
    assert "Note logged." in result.output
    # save_config was called with "health" in subjects
    assert len(save_config_calls) == 1
    assert "health" in save_config_calls[0]["subjects"]
    # write_note called with the new subject
    assert len(write_note_calls) == 1
    assert write_note_calls[0][1] == "health"


def test_mn_no_subjects(tmp_path, monkeypatch):
    """mn with no subjects configured prints error and exits."""
    from makenote.cli import main

    config_path = _make_config(tmp_path, subjects=[])
    monkeypatch.setattr("makenote.config.CONFIG_PATH", config_path)

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, [])

    assert "Error: no subjects configured" in result.output


def test_mn_d_prompts(tmp_path, monkeypatch):
    """mn d with no inline text prompts for note text, logs with default subject."""
    from makenote.cli import main

    config_path = _make_config(tmp_path)
    monkeypatch.setattr("makenote.config.CONFIG_PATH", config_path)

    calls = []
    monkeypatch.setattr("makenote.cli._gh.write_note", lambda repo, subject, note: calls.append((repo, subject, note)))

    monkeypatch.setattr("makenote.cli.questionary.text", lambda *a, **kw: _MockAsk("my note"))

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, ["d"])

    assert result.exit_code == 0
    assert "Note logged." in result.output
    assert len(calls) == 1
    assert calls[0][1] == "work"  # default_subject


def test_mn_d_inline(tmp_path, monkeypatch):
    """mn d 'text' logs with zero interaction — no questionary calls."""
    from makenote.cli import main

    config_path = _make_config(tmp_path)
    monkeypatch.setattr("makenote.config.CONFIG_PATH", config_path)

    calls = []
    monkeypatch.setattr("makenote.cli._gh.write_note", lambda repo, subject, note: calls.append((repo, subject, note)))

    questionary_called = []
    monkeypatch.setattr("makenote.cli.questionary.text", lambda *a, **kw: questionary_called.append(True) or _MockAsk("should not be called"))

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, ["d", "fixed the login bug"])

    assert result.exit_code == 0
    assert "Note logged." in result.output
    assert calls[0][2] == "fixed the login bug"
    assert not questionary_called, "questionary.text should not be called for inline note"


def test_mn_list(tmp_path, monkeypatch):
    """mn list prints up to 20 recent notes in columnar format."""
    from makenote.cli import main

    config_path = _make_config(tmp_path)
    monkeypatch.setattr("makenote.config.CONFIG_PATH", config_path)

    sample_records = [
        {"date": "2026-03-08", "subject": "work", "note": "deployed new feature"},
        {"date": "2026-03-07", "subject": "personal", "note": "went for a run"},
    ]
    monkeypatch.setattr("makenote.cli._gh.read_notes", lambda repo, subjects: sample_records)

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, ["list"])

    assert result.exit_code == 0
    assert "2026-03-08" in result.output
    assert "work" in result.output
    assert "deployed new feature" in result.output
    assert "2026-03-07" in result.output
    assert "personal" in result.output
    assert "went for a run" in result.output


def test_mn_list_gh_not_installed(tmp_path, monkeypatch):
    """mn list with GhNotInstalledError prints locked message and exits 1."""
    from makenote.cli import main

    config_path = _make_config(tmp_path)
    monkeypatch.setattr("makenote.config.CONFIG_PATH", config_path)
    monkeypatch.setattr(
        "makenote.cli._gh.read_notes",
        lambda *a, **kw: (_ for _ in ()).throw(GhNotInstalledError("gh not found")),
    )

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, ["list"])

    assert result.exit_code == 1
    assert "Error: gh CLI not found" in result.output
    assert "https://cli.github.com" in result.output


def test_mn_list_gh_not_authenticated(tmp_path, monkeypatch):
    """mn list with GhNotAuthError prints locked message and exits 1."""
    from makenote.cli import main

    config_path = _make_config(tmp_path)
    monkeypatch.setattr("makenote.config.CONFIG_PATH", config_path)
    monkeypatch.setattr(
        "makenote.cli._gh.read_notes",
        lambda *a, **kw: (_ for _ in ()).throw(GhNotAuthError("not authenticated")),
    )

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, ["list"])

    assert result.exit_code == 1
    assert "Error: gh not authenticated" in result.output
    assert "gh auth login" in result.output


def test_mn_gh_not_installed(tmp_path, monkeypatch):
    """mn d with GhNotInstalledError prints correct locked message and exits 1."""
    from makenote.cli import main

    config_path = _make_config(tmp_path)
    monkeypatch.setattr("makenote.config.CONFIG_PATH", config_path)

    monkeypatch.setattr("makenote.cli._gh.write_note", lambda *a, **kw: (_ for _ in ()).throw(GhNotInstalledError("gh not found")))

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, ["d", "test"])

    assert result.exit_code == 1
    assert "Error: gh CLI not found" in result.output
    assert "https://cli.github.com" in result.output


def test_mn_gh_not_authenticated(tmp_path, monkeypatch):
    """mn d with GhNotAuthError prints correct locked message and exits 1."""
    from makenote.cli import main

    config_path = _make_config(tmp_path)
    monkeypatch.setattr("makenote.config.CONFIG_PATH", config_path)

    monkeypatch.setattr("makenote.cli._gh.write_note", lambda *a, **kw: (_ for _ in ()).throw(GhNotAuthError("not authenticated")))

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, ["d", "test"])

    assert result.exit_code == 1
    assert "Error: gh not authenticated" in result.output
    assert "gh auth login" in result.output
