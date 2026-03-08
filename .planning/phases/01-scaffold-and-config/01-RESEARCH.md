# Phase 1: Scaffold and Config - Research

**Researched:** 2026-03-08
**Domain:** Python CLI packaging (pyproject.toml + click) and interactive prompts (questionary)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- `mn --help` → minimal output: just commands and flags, no examples or descriptions
- `mn --version` → `mn 0.1.0` format (name + version, no comma, no "version" word)
- All output is plain text — no ANSI colors, no styled output
- Errors use: `Error: <message>` — plain prefix, direct, no emoji or decoration
- `questionary` is the chosen library for interactive prompts (arrow-key selection)
- Config at `~/.config/makenote/config.json`
- Python CLI via `pyproject.toml` `console_scripts` entry point (`mn`)
- Phase 2 will import config reading logic from this phase (design for import)
- `gh` CLI is a hard dependency; must be installed and authenticated by the user (not validated in this phase)

### Claude's Discretion
- Config flow UX (step-by-step vs menu) — Claude decides
- Subject management UI within `mn config` (inline list vs add/remove prompts) — Claude decides
- First-run experience messaging — Claude decides
- Python package structure (flat vs `src/` layout) — Claude decides
- pyproject.toml contents (Python version, dependencies, metadata) — Claude decides

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UX-01 | `mn --help` and `mn --version` work correctly | click 8.3.x `@click.version_option(message="%(prog)s %(version)s")` + `@click.group` auto-generates --help |
| CONF-01 | First run with no config auto-triggers setup flow before proceeding | click `@click.group(invoke_without_command=True)` + `@click.pass_context` + config existence check in group callback |
| CONF-02 | Config stored at `~/.config/makenote/config.json` | `pathlib.Path.home() / ".config" / "makenote" / "config.json"` + `mkdir(parents=True, exist_ok=True)` |
| CONF-03 | User can set/change the target GitHub repo | `questionary.text()` prompt in config flow |
| CONF-04 | User can set/change the default subject | `questionary.select()` or `questionary.text()` prompt in config flow |
| CONF-05 | User can add a new subject | `questionary.text()` prompt; append to subjects list in config |
| CONF-06 | User can remove an existing subject | `questionary.select()` of current subjects; remove selected from list |
| CORE-05 | User can run `mn config` to interactively edit repo, default subject, and subject list | click subcommand `config` registered on the group |
</phase_requirements>

---

## Summary

This phase builds a greenfield Python CLI tool from scratch. The two primary concerns are (1) correct Python packaging so `pip install -e .` installs `mn` as an executable, and (2) a working interactive config flow using `questionary`.

The standard stack is clear and locked: `click` 8.3.x for CLI structure (group + subcommands, `--help`, `--version`) and `questionary` 2.1.1 for interactive prompts. The package should use a `src/` layout for correctness (avoids import-from-working-directory bugs) and `setuptools` as the build backend (widest compatibility, well-understood). Config is plain JSON stored at `~/.config/makenote/config.json`, created with `pathlib` — no external config library needed at this scale.

The trickiest requirement is CONF-01: "first-run auto-triggers setup." The correct pattern in click is to intercept in the group callback using `invoke_without_command=True` and `@click.pass_context`, then check for config existence before allowing any subcommand to run. This needs careful design so `mn config` itself is still accessible when no config exists (it IS the setup path).

**Primary recommendation:** Use `click` group with `invoke_without_command=True`, check config at group-callback level (before subcommand runs), redirect to `run_config_flow()` when config is absent (except when the user is already running `mn config`), store config as plain JSON via `json` stdlib. Keep all prompt logic in `makenote/config.py`, importable by Phase 2.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| click | 8.3.x | CLI structure, --help, --version, subcommands, group | Most widely adopted Python CLI framework (38.7% of CLI projects in 2025); decorator-based, composable |
| questionary | 2.1.1 | Interactive arrow-key prompts (select, text, confirm) | Locked decision; based on prompt-toolkit; active maintenance (released Aug 2025) |
| setuptools | latest | Build backend for pyproject.toml | Widest compatibility, standard for new packages; auto-discovers src layout |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json (stdlib) | — | Read/write config.json | Always — no external dep needed for simple flat JSON |
| pathlib (stdlib) | — | Config directory creation, path manipulation | Always — `Path.home() / ".config" / "makenote"` |
| importlib.metadata (stdlib) | — | Auto-detect version in click.version_option | When `version` is not hard-coded in decorator |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| click | argparse (stdlib) | argparse has no decorator API, more boilerplate for subcommands; click generates cleaner --help |
| click | typer | typer wraps click but adds type-hint complexity; overkill for this scale |
| questionary | InquirerPy | InquirerPy is a rewrite of PyInquirer, similar API but questionary is locked decision |
| setuptools | hatchling | hatchling is modern but less familiar; setuptools is fine for this project |
| src/ layout | flat layout | flat layout risks importing from working directory during tests; src/ layout is current PyPA recommendation |

**Installation:**
```bash
pip install click questionary
```

---

## Architecture Patterns

### Recommended Project Structure
```
make-note/
├── src/
│   └── makenote/
│       ├── __init__.py       # package marker, version = "0.1.0"
│       ├── cli.py            # click group + subcommand wiring, entry point function
│       ├── config.py         # config read/write logic + run_config_flow() function
│       └── constants.py      # CONFIG_PATH, APP_NAME
├── tests/
│   ├── __init__.py
│   ├── test_cli.py           # CliRunner tests for --help, --version, first-run
│   └── test_config.py        # unit tests for config read/write/validate
├── pyproject.toml
└── README.md (optional)
```

### Pattern 1: pyproject.toml with console_scripts
**What:** Declares the `mn` executable that pip installs into PATH.
**When to use:** All Python CLI tools distributed via pip.
**Example:**
```toml
# Source: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "makenote"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "click>=8.1",
    "questionary>=2.0",
]

[project.scripts]
mn = "makenote.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
```

### Pattern 2: click Group with First-Run Interception
**What:** Group callback runs before any subcommand. If config is missing and user is not explicitly running `mn config`, trigger the setup flow automatically.
**When to use:** Any CLI that requires initial configuration before use.
**Example:**
```python
# Source: https://click.palletsprojects.com/en/stable/commands-and-groups/
import click
from makenote.config import config_exists, run_config_flow

@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="mn", message="%(prog)s %(version)s")
@click.pass_context
def main(ctx):
    # First-run detection: if no config and not running 'mn config', auto-setup
    if not config_exists() and ctx.invoked_subcommand != "config":
        click.echo("No config found. Running first-time setup.")
        run_config_flow()
    # If invoked with no subcommand and config exists, show help
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

@main.command()
def config():
    """Edit configuration."""
    run_config_flow()
```

### Pattern 3: questionary select with Choice and Separator
**What:** Arrow-key list for subject selection and subject management. Use `Separator` to visually group options like "--- Actions ---" above "Add subject" / "Remove subject".
**When to use:** Any prompt where user picks from a list.
**Example:**
```python
# Source: https://questionary.readthedocs.io/en/stable/pages/types.html
import questionary
from questionary import Separator

action = questionary.select(
    "What would you like to configure?",
    choices=[
        "Set GitHub repo",
        "Set default subject",
        Separator(),
        "Add subject",
        "Remove subject",
        Separator(),
        "Done",
    ]
).ask()  # returns None on Ctrl-C
```

### Pattern 4: Config Read/Write
**What:** Load JSON from `~/.config/makenote/config.json`, return typed dict. Create parent directories on first write.
**When to use:** All config access — keep in `config.py` so Phase 2 can import it.
**Example:**
```python
# Source: pathlib stdlib + json stdlib
from pathlib import Path
import json

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
```

### Anti-Patterns to Avoid
- **Running config flow inside every subcommand:** Config check belongs in the group callback, not repeated in each command.
- **Hard-coding `~/.config` as a string:** Use `Path.home()` — avoids issues on Windows and non-standard home dirs.
- **Using `questionary.unsafe_ask()`:** Prefer `.ask()` which returns `None` on Ctrl-C. Check for `None` and exit gracefully.
- **Storing config path in multiple places:** Define `CONFIG_PATH` once in `constants.py` or at the top of `config.py`, import everywhere.
- **Printing with `print()`:** Use `click.echo()` for all CLI output — it handles encoding edge cases and is testable via CliRunner.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Arrow-key selection prompts | Custom readline/curses prompt | `questionary.select()` | Terminal compatibility, platform-specific edge cases |
| --help generation | Manual help string formatting | `click` (automatic from docstrings + decorators) | Click generates consistent --help from group/command structure |
| --version flag | Manual `sys.argv` parsing | `@click.version_option()` | Correct exit code, standard format |
| Config directory creation | Manual `os.makedirs` with try/except | `Path.mkdir(parents=True, exist_ok=True)` | Cleaner, idiomatic Python 3 |
| CLI test harness | subprocess calls in tests | `click.testing.CliRunner` | Isolated, no subprocess overhead, captures stdout |

**Key insight:** The combination of click + questionary handles 100% of the UX requirements in this phase. Any custom terminal manipulation is a trap.

---

## Common Pitfalls

### Pitfall 1: questionary.ask() Returns None on Ctrl-C
**What goes wrong:** User presses Ctrl-C during a prompt; code tries to use the return value as a string and crashes with `AttributeError` or `TypeError`.
**Why it happens:** `.ask()` (safe mode) catches `KeyboardInterrupt` and returns `None`. Code that doesn't check for `None` proceeds with invalid data.
**How to avoid:** Always check `if result is None: sys.exit(0)` immediately after each `.ask()` call. Or use a helper wrapper.
**Warning signs:** Any prompt return value used directly without a `None` check.

### Pitfall 2: Importing from Working Directory (flat layout)
**What goes wrong:** `import makenote` in tests resolves to the local `makenote/` directory instead of the installed package. Tests pass locally but fail on CI or after install.
**Why it happens:** Python adds the current directory to `sys.path`. Flat layout makes the package importable from cwd.
**How to avoid:** Use `src/` layout. With `src/makenote/`, the package is only importable after `pip install -e .`.
**Warning signs:** Tests pass without `pip install -e .`; behavior differs between test run and installed version.

### Pitfall 3: mn config Blocked by First-Run Check
**What goes wrong:** First-run detection blocks ALL commands including `mn config` itself, making it impossible to set up configuration.
**Why it happens:** Naive implementation: `if not config_exists(): run_config_flow()` at group level intercepts `mn config` too.
**How to avoid:** Check `ctx.invoked_subcommand != "config"` before auto-triggering setup. When `mn config` is explicitly called, skip the auto-trigger and let the config subcommand handle the flow directly.
**Warning signs:** `mn config` triggers the setup flow twice (auto + explicit).

### Pitfall 4: Click Help Output Too Verbose
**What goes wrong:** User constraint requires minimal `--help`. Click by default includes the command docstring as the help text for each command.
**Why it happens:** Click uses function docstrings as help text automatically.
**How to avoid:** Use empty docstrings or very short one-liners. Do not include examples or long descriptions in docstrings. The `mn --help` output should list only commands and flags.
**Warning signs:** Docstrings longer than one line appearing in help output.

### Pitfall 5: Version String Mismatch
**What goes wrong:** `mn --version` outputs `mn, version 0.1.0` (Click default format) instead of `mn 0.1.0` (user requirement).
**Why it happens:** Click's default message template is `"%(prog)s, version %(version)s"`.
**How to avoid:** Always pass `message="%(prog)s %(version)s"` explicitly to `@click.version_option()`.
**Warning signs:** Comma or the word "version" appearing in `mn --version` output.

---

## Code Examples

### Minimal pyproject.toml for this project
```toml
# Source: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "makenote"
version = "0.1.0"
requires-python = ">=3.10"
description = "Fast terminal note logging to GitHub"
dependencies = [
    "click>=8.1",
    "questionary>=2.0",
]

[project.scripts]
mn = "makenote.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### click --version with correct format
```python
# Source: https://click.palletsprojects.com/en/stable/api/#click.version_option
@click.version_option(version="0.1.0", prog_name="mn", message="%(prog)s %(version)s")
```

### Config flow skeleton (run_config_flow)
```python
# questionary API: https://questionary.readthedocs.io/en/stable/pages/types.html
import questionary
import sys

def run_config_flow(existing: dict | None = None) -> None:
    """Interactive config editor. Loops until user selects Done."""
    data = existing.copy() if existing else {"repo": "", "default_subject": "", "subjects": []}

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
            ]
        ).ask()

        if action is None:  # Ctrl-C
            sys.exit(0)

        if action == "Set GitHub repo":
            repo = questionary.text("GitHub repo (owner/repo):").ask()
            if repo is None:
                sys.exit(0)
            data["repo"] = repo.strip()

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
```

### Click CliRunner test pattern
```python
# Source: https://click.palletsprojects.com/en/stable/testing/
from click.testing import CliRunner
from makenote.cli import main

def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == "mn 0.1.0"

def test_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "config" in result.output
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `setup.py` + `setup.cfg` | `pyproject.toml` only | PEP 517/518 (2018), now standard | Single config file; `pip install -e .` works without setup.py |
| `argparse` for subcommands | `click` with `@click.group()` | click has been dominant since ~2015 | Decorator-based, auto --help, composable |
| `os.path` for paths | `pathlib.Path` | Python 3.4+, idiomatic since ~3.6 | Cleaner, cross-platform, chainable |
| `PyInquirer` for prompts | `questionary` | questionary ~2019; PyInquirer unmaintained | `questionary` actively maintained (2.1.1 Aug 2025) |

**Deprecated/outdated:**
- `setup.py`: Do not create. pyproject.toml handles everything.
- `ConfigParser` / `.ini` config: Project chose JSON. Do not use.
- `PyInquirer`: Unmaintained. `questionary` is the successor.

---

## Open Questions

1. **Version string source of truth**
   - What we know: Version "0.1.0" must appear in both `pyproject.toml` and the `--version` output.
   - What's unclear: Should `cli.py` hard-code `"0.1.0"` or read it dynamically via `importlib.metadata.version("makenote")`? Dynamic approach requires the package to be installed; hard-coded is simpler for development.
   - Recommendation: Hard-code `"0.1.0"` in `pyproject.toml` and pass it directly to `@click.version_option(version="0.1.0")` for Phase 1. Avoid dynamic lookup to keep the dev loop simple.

2. **Config flow entry point: menu-loop vs wizard**
   - What we know: Claude has discretion on UX. Step-by-step wizard runs prompts in sequence. Menu-loop lets user jump to any field.
   - What's unclear: What's better for first-run (all fields empty)?
   - Recommendation: Menu-loop is the right choice. It serves both first-run (user sets fields they need) and re-run (user changes only one thing). Wizard approach forces re-entering fields the user doesn't want to change.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (latest) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` — see Wave 0 |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UX-01 | `mn --version` prints `mn 0.1.0` | unit | `pytest tests/test_cli.py::test_version -x` | Wave 0 |
| UX-01 | `mn --help` exits 0 and lists `config` command | unit | `pytest tests/test_cli.py::test_help -x` | Wave 0 |
| CONF-01 | `mn` with no config triggers setup flow | unit (mock) | `pytest tests/test_cli.py::test_first_run_triggers_config -x` | Wave 0 |
| CONF-01 | `mn config` when no config does NOT double-trigger | unit (mock) | `pytest tests/test_cli.py::test_config_cmd_no_double_trigger -x` | Wave 0 |
| CONF-02 | Config written to correct path | unit | `pytest tests/test_config.py::test_config_path -x` | Wave 0 |
| CONF-02 | Config directory created if absent | unit (tmp_path) | `pytest tests/test_config.py::test_config_dir_created -x` | Wave 0 |
| CONF-03 | Repo field saved after prompt | unit (mock questionary) | `pytest tests/test_config.py::test_save_repo -x` | Wave 0 |
| CONF-04 | Default subject saved after prompt | unit (mock questionary) | `pytest tests/test_config.py::test_save_default_subject -x` | Wave 0 |
| CONF-05 | Subject added to list and persisted | unit (mock questionary) | `pytest tests/test_config.py::test_add_subject -x` | Wave 0 |
| CONF-06 | Subject removed from list and persisted | unit (mock questionary) | `pytest tests/test_config.py::test_remove_subject -x` | Wave 0 |
| CORE-05 | `mn config` subcommand is reachable | unit | `pytest tests/test_cli.py::test_config_cmd_exists -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/__init__.py` — package marker
- [ ] `tests/test_cli.py` — covers UX-01, CONF-01, CORE-05
- [ ] `tests/test_config.py` — covers CONF-02 through CONF-06
- [ ] `pyproject.toml` `[tool.pytest.ini_options]` block — testpaths config
- [ ] Framework install: `pip install pytest` (plus `pip install -e .` for package under test)

---

## Sources

### Primary (HIGH confidence)
- [questionary 2.1.1 PyPI](https://pypi.org/project/questionary/) — version, Python support range
- [questionary types docs](https://questionary.readthedocs.io/en/stable/pages/types.html) — select/text/confirm API, Choice, Separator
- [questionary advanced docs](https://questionary.readthedocs.io/en/stable/pages/advanced.html) — .ask() vs .unsafe_ask(), KeyboardInterrupt handling
- [click 8.3.x docs](https://click.palletsprojects.com/en/stable/) — group, version_option, pass_context
- [click API reference](https://click.palletsprojects.com/en/stable/api/#click.version_option) — version_option message parameter
- [click testing docs](https://click.palletsprojects.com/en/stable/testing/) — CliRunner pattern
- [Python Packaging Guide - pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) — required fields, console_scripts, build backend
- [src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) — PyPA recommendation

### Secondary (MEDIUM confidence)
- [click commands-and-groups](https://click.palletsprojects.com/en/stable/commands-and-groups/) — invoke_without_command, invoked_subcommand pattern — verified against official click docs
- WebSearch: click 2025 market share (38.7%) — sourced from multiple 2025 blog posts, consistent across sources

### Tertiary (LOW confidence)
- None — all critical claims verified against official documentation.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — questionary and click are locked or verified against PyPI/official docs; versions confirmed current
- Architecture: HIGH — click group pattern is official documented API; config path pattern is stdlib
- Pitfalls: HIGH — Ctrl-C/None pitfall and version message pitfall verified against official click/questionary docs; import pitfall verified against PyPA guide

**Research date:** 2026-03-08
**Valid until:** 2026-06-08 (stable ecosystem; click and questionary are not fast-moving)
