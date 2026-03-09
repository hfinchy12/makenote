import pytest
from click.testing import CliRunner


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
