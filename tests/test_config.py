import json
import pytest


@pytest.mark.xfail(strict=False, reason="not yet implemented")
def test_config_path():
    """CONFIG_PATH points to the expected location."""
    from makenote.config import CONFIG_PATH
    assert str(CONFIG_PATH).endswith(".config/makenote/config.json")


@pytest.mark.xfail(strict=False, reason="not yet implemented")
def test_config_dir_created(tmp_path, monkeypatch):
    """save_config creates parent directories if absent."""
    from makenote import config as cfg
    target = tmp_path / "sub" / "config.json"
    monkeypatch.setattr(cfg, "CONFIG_PATH", target)
    cfg.save_config({"repo": "a/b", "default_subject": "work", "subjects": ["work"]})
    assert target.exists()


@pytest.mark.xfail(strict=False, reason="not yet implemented")
def test_save_repo(tmp_path, monkeypatch):
    """save_config persists repo field."""
    from makenote import config as cfg
    target = tmp_path / "config.json"
    monkeypatch.setattr(cfg, "CONFIG_PATH", target)
    cfg.save_config({"repo": "owner/repo", "default_subject": "", "subjects": []})
    data = json.loads(target.read_text())
    assert data["repo"] == "owner/repo"


@pytest.mark.xfail(strict=False, reason="not yet implemented")
def test_save_default_subject(tmp_path, monkeypatch):
    """save_config persists default_subject field."""
    from makenote import config as cfg
    target = tmp_path / "config.json"
    monkeypatch.setattr(cfg, "CONFIG_PATH", target)
    cfg.save_config({"repo": "", "default_subject": "work", "subjects": ["work"]})
    data = json.loads(target.read_text())
    assert data["default_subject"] == "work"


@pytest.mark.xfail(strict=False, reason="not yet implemented")
def test_add_subject(tmp_path, monkeypatch):
    """save_config persists a newly added subject."""
    from makenote import config as cfg
    target = tmp_path / "config.json"
    monkeypatch.setattr(cfg, "CONFIG_PATH", target)
    cfg.save_config({"repo": "", "default_subject": "", "subjects": ["work", "personal"]})
    data = json.loads(target.read_text())
    assert "personal" in data["subjects"]


@pytest.mark.xfail(strict=False, reason="not yet implemented")
def test_remove_subject(tmp_path, monkeypatch):
    """save_config persists removal of a subject."""
    from makenote import config as cfg
    target = tmp_path / "config.json"
    monkeypatch.setattr(cfg, "CONFIG_PATH", target)
    cfg.save_config({"repo": "", "default_subject": "", "subjects": ["work"]})
    data = json.loads(target.read_text())
    assert "personal" not in data["subjects"]
