# Stack Research

**Domain:** Python CLI developer tool with interactive TUI, GitHub integration, dual distribution
**Researched:** 2026-03-08
**Confidence:** MEDIUM — external verification tools were unavailable; all version data is from training data (cutoff August 2025). Version numbers should be verified against PyPI before locking dependencies.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | >=3.11 | Runtime | 3.11+ offers meaningful performance gains and improved error messages; 3.10 is approaching end-of-life. 3.12 is the current stable release as of mid-2025. |
| Click | 8.1.x | CLI argument parsing, command dispatch, `mn`/`mn d`/`mn list`/`mn config` routing | Click is the de-facto standard for Python CLIs. Mature, stable, excellent help formatting, reliable subcommand handling. Typer wraps Click — using Click directly gives full control without a layer of abstraction over argument handling. |
| questionary | 2.0.x | Interactive arrow-key picker (subject selection), inline text prompts | questionary is the lightest correct library for this job: prompt_toolkit underneath, arrow-key `select`, inline `text` prompts. The project brief already names it. Alternatives (InquirerPy, prompt_toolkit directly) are heavier or more complex for this narrow use case. |
| pyproject.toml | — | Single-file build config, `[project.scripts]` entry points for `mn` command | PEP 517/518/660 standard. `console_scripts = ["mn = makenote.cli:main"]` wires the `mn` command on install. No `setup.py` needed. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| hatch / hatchling | 1.x (build backend) | Build backend for pyproject.toml | Use hatchling as the `[build-system]` backend. It is the modern default recommended by the Python Packaging Authority (PyPA) for new projects, simpler than setuptools for this use case. |
| rich | 13.x | Formatted terminal output for `mn list` | Use for the list display — coloured timestamps, bold subjects, truncated note previews. Do NOT use for interactive prompts (questionary handles those). |
| pytest | 8.x | Unit tests | pytest is the standard. Pair with `pytest-subprocess` to mock `gh` CLI calls without spawning real processes. |
| pytest-subprocess | 1.x | Mock `subprocess.run` / `subprocess.check_output` calls in tests | Essential for testing the `gh api` wrapper without hitting GitHub. Prevents flaky tests and credential requirements in CI. |
| tomllib (stdlib) | stdlib (3.11+) | Config file reading if config ever moves to TOML | Built into Python 3.11+. No extra dependency needed. For now, config is JSON so this is optional. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Dependency management, virtual env, `uv pip install -e .` for dev installs | uv is the 2025 standard for Python project tooling — dramatically faster than pip + venv. Use `uv sync` for reproducible envs. Not a runtime dependency; dev workflow only. |
| ruff | Linting + formatting | Replaces flake8 + black + isort in one tool. Default config is good for a project this size. `ruff check . --fix` and `ruff format .`. |
| pyinstaller / shiv | (Do NOT use — see below) | Listed here as explicit avoids |

---

## Installation

```bash
# Create project with uv
uv init makenote
cd makenote

# Add runtime dependencies
uv add click questionary rich

# Add dev dependencies
uv add --dev pytest pytest-subprocess ruff

# Install in editable mode (wires `mn` entry point locally)
uv pip install -e .
```

### pyproject.toml skeleton

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "makenote"
version = "0.1.0"
description = "Log developer notes to GitHub from the terminal"
requires-python = ">=3.11"
dependencies = [
  "click>=8.1",
  "questionary>=2.0",
  "rich>=13.0",
]

[project.scripts]
mn = "makenote.cli:main"

[dependency-groups]
dev = [
  "pytest>=8.0",
  "pytest-subprocess>=1.0",
  "ruff>=0.4",
]
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Click | Typer | Typer is better when you want automatic CLI generation from type annotations and you're building a larger API surface. For `mn` with 4 commands and bespoke argument handling, Click's explicit style is cleaner and avoids Typer's occasional type annotation friction. |
| Click | argparse (stdlib) | argparse for tools with zero runtime dependencies (e.g., scripts bundled with Python itself). For a distributed package, Click's DX is far superior. |
| questionary | InquirerPy | InquirerPy has more widget types but has had maintenance gaps. questionary is more actively maintained and its API surface exactly covers the `mn` use case (select + text). |
| questionary | prompt_toolkit directly | prompt_toolkit is what questionary wraps. Using it directly adds significant boilerplate for the same result. Only use raw prompt_toolkit if you need layout control beyond what questionary offers. |
| hatchling | setuptools | setuptools is still valid but requires more boilerplate. hatchling is the PyPA-recommended default for new projects as of 2023+. |
| hatchling | flit | flit is elegant but less flexible; no support for dynamic version discovery or custom build hooks. |
| uv (dev tool) | poetry | poetry is still widely used but uv is dramatically faster and is becoming the 2025 community standard for new projects. Both are fine. |
| rich | termcolor / colorama | rich provides much better output formatting for `mn list`. termcolor/colorama are appropriate for simple single-color output but not structured table/panel output. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| PyInstaller / shiv / nuitka | These bundle a full Python runtime into a binary. Adds 30-60MB to the distributable, breaks Homebrew's standard Python formula pattern, and the `gh` subprocess dependency means you need the host env anyway. | Standard pyproject.toml + Homebrew `python_shebang` formula |
| PyGitHub / requests against GitHub API directly | PROJECT.md explicitly excludes direct API token handling. `gh` CLI is the authentication layer by design. | `subprocess.run(["gh", "api", ...])` |
| Textual / Urwid / curses | Full TUI frameworks. `mn` only needs two interaction patterns: arrow-key select and inline text input. These frameworks are massive overkill and would require a rewrite if the TUI stays lightweight. | questionary |
| setuptools with setup.py | setup.py is the legacy path. It still works but has no advantages for a new project. New projects should use pyproject.toml exclusively. | hatchling + pyproject.toml |
| Conda / conda-build for distribution | Conda is a scientific Python ecosystem tool. Developer CLI tools target pip/Homebrew audiences. Conda packaging would add complexity with no benefit for this audience. | PyPI + Homebrew |
| pydantic (v1) | pydantic v1 is EOL. If you add pydantic for config validation, use v2. | pydantic>=2.0 (or just use stdlib dataclasses — config is simple enough) |

---

## Distribution: Homebrew Tap Pattern

Homebrew is the primary distribution target. The standard pattern for a Python CLI tool:

```ruby
# Formula/mn.rb in a personal tap (github.com/username/homebrew-tap)
class Mn < Formula
  include Language::Python::Virtualenv

  desc "Log developer notes to GitHub from the terminal"
  homepage "https://github.com/username/make-note"
  url "https://files.pythonhosted.org/packages/.../makenote-0.1.0.tar.gz"
  sha256 "..."
  license "MIT"

  depends_on "python@3.12"

  resource "click" do
    url "https://files.pythonhosted.org/packages/.../click-8.1.x.tar.gz"
    sha256 "..."
  end

  resource "questionary" do
    # ...
  end

  resource "rich" do
    # ...
  end

  def install
    virtualenv_install_with_resources
  end
end
```

Key constraint: Homebrew formulas using `virtualenv_install_with_resources` bundle all dependencies into the formula's own virtualenv. This means you must pin exact versions and provide SHA256 hashes for each dependency. The `brew audit` command validates this. This is more maintenance overhead than PyPI but is the correct Homebrew pattern for Python CLIs.

**Homebrew tap setup:**
1. Create `github.com/username/homebrew-tap`
2. Add formula at `Formula/mn.rb`
3. Users install with: `brew tap username/tap && brew install mn`

---

## Stack Patterns by Variant

**If adding shell completion (future):**
- Click has built-in shell completion generation (`click.shell_completion`)
- Call `mn --install-completion` to generate completion scripts
- Homebrew formula can wire this at install time

**If adding offline queue (out of scope v1, but future):**
- Use SQLite via `sqlite3` (stdlib) — no new dependency
- Do NOT add a queue library (overkill for a CLI)

**If config validation becomes complex:**
- Add `pydantic>=2.0` for config schema validation
- Currently config is simple enough that manual dict access + sensible defaults is fine

---

## Version Compatibility Notes

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| questionary>=2.0 | prompt_toolkit>=3.0 | questionary 2.x requires prompt_toolkit 3.x. Both are pure Python. No known conflicts with click or rich. |
| click>=8.1 | Python>=3.8 | Click 8.x is stable across Python 3.8–3.13. No compatibility concerns. |
| rich>=13.0 | Python>=3.8 | No known conflicts with click or questionary. |
| Python 3.12 / 3.13 | All above | Python 3.13 is the current release as of late 2024. All recommended libraries support it. |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Click as CLI framework | HIGH | Stable, dominant choice for 5+ years, no credible challenger for this use case |
| questionary for TUI | HIGH | Explicitly named in PROJECT.md, correct fit, actively maintained |
| hatchling as build backend | MEDIUM | PyPA recommendation is confirmed from training; verify current guidance at packaging.python.org |
| uv as dev tool | MEDIUM | Rapidly became standard in 2024; verify it's still recommended at docs.astral.sh/uv |
| questionary version (2.0.x) | LOW | Specific version from training data — verify at pypi.org/project/questionary before pinning |
| click version (8.1.x) | LOW | Verify at pypi.org/project/click — Click 8.2 may have shipped |
| rich version (13.x) | LOW | Verify at pypi.org/project/rich — rich releases frequently |
| Homebrew formula pattern | MEDIUM | Pattern is well-established; verify against current `brew` formula guidelines if Homebrew Python support changes |

---

## Sources

- Training data (cutoff August 2025) — Click, questionary, rich, hatchling, uv ecosystem state
- PROJECT.md — questionary and gh CLI constraints confirmed from project brief
- Python Packaging Authority guidance (pypa.io) — pyproject.toml and hatchling recommendation
- NOTE: All version numbers require verification at pypi.org before being used in pyproject.toml

---
*Stack research for: MakeNote (`mn`) Python CLI developer tool*
*Researched: 2026-03-08*
