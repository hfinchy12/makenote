# Phase 2: Core Note-Taking - Research

**Researched:** 2026-03-08
**Domain:** GitHub Contents API via `gh` CLI, Click subcommands, JSONL append, Python subprocess
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Note input uses `questionary.text("Note:")` — consistent with existing config flow pattern
- After successful push: print `Note logged.` — brief confirmation, plain text
- When no subjects configured: print `Error: no subjects configured. Run mn config to add subjects.` and exit
- "Add New" in the subject picker persists the new subject to `config.json` permanently (not session-only)
- All GitHub failures: error-and-exit, no retry — consistent with no-offline-queue decision
- `gh` not installed: `Error: gh CLI not found. Install from https://cli.github.com`
- `gh` not authenticated: `Error: gh not authenticated. Run: gh auth login`
- SHA conflict (stale write): `Error: write conflict — file may have changed. Try again.`
- All errors follow the established `Error: <message>` format from Phase 1

### Claude's Discretion

- `mn list` display format (fields shown, ordering, truncation)
- Exact `gh api` endpoint and payload structure
- Module structure for `github.py`

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| GH-01 | Notes written via `gh api` — read current SHA → append record → update file | GET + PUT Contents API workflow documented below |
| GH-02 | Notes stored as JSONL with `date`, `subject`, `note` fields per record | JSONL append pattern documented; `datetime.date.today()` for date |
| GH-03 | One `notes.jsonl` per subject folder, under configurable `target_path` in the repo | Path construction pattern documented below |
| GH-04 | Clear error message when `gh` not installed or not authenticated | `FileNotFoundError` vs non-zero returncode detection documented |
| CORE-01 | `mn` — arrow-key subject picker → inline note input → push to GitHub | questionary.select + text flow with "Add New" option |
| CORE-02 | `mn d` — skip subject picker, prompt for note text using default subject | Click argument with nargs=-1 or separate command |
| CORE-03 | `mn d "note content"` — zero interaction | Click argument receives note text directly |
| CORE-04 | `mn list` — recent notes across all subjects printed to terminal | Read + base64-decode JSONL from each subject via gh api |
| UX-02 | Subject picker uses arrow-key selection with "Add New" option | `questionary.select()` with "Add New" as first/last choice |
| UX-03 | Each note record includes a `date` field (YYYY-MM-DD) | `datetime.date.today().isoformat()` |
</phase_requirements>

---

## Summary

Phase 2 builds on the Phase 1 scaffold (Click group, questionary, config load/save) to implement the full note-logging and note-reading user flows. The central technical challenge is the GitHub write workflow: read the current file to get its SHA, decode the base64 content to append a new JSONL record, re-encode, and PUT back. This read-modify-write pattern is well-documented and must be implemented exactly — the SHA is mandatory for updates and must match the current blob to avoid a 422 conflict.

All GitHub I/O is done by shelling out to `gh api` via Python's `subprocess.run`. The two detection cases (binary not found vs. authenticated failure) map to distinct Python exception types and `gh` exit codes. The `mn note` subcommand is the core flow; the `mn d` / `mn d "text"` variants differ only in whether they skip the subject picker and whether they accept an inline argument. `mn list` reads JSONL from GitHub for every configured subject and prints a simple timestamped list.

**Primary recommendation:** Implement `github.py` as a single module with three public functions — `write_note(repo, subject, note_text)`, `read_notes(repo, subjects)`, and a private `_run_gh(*args)` helper that handles the binary-not-found and auth-failure detection uniformly.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `click` | >=8.1 (already in project) | CLI subcommands and argument parsing | Already established; `@main.command()` pattern in place |
| `questionary` | >=2.0 (already in project) | Arrow-key pickers and text prompts | Already established; `None`-check pattern in place |
| `subprocess` (stdlib) | Python 3.9+ | Shell out to `gh api` | No additional dependency; matches project's "no credential handling" principle |
| `json` (stdlib) | Python 3.9+ | Parse `gh api` JSON responses and JSONL records | Already used in config.py |
| `base64` (stdlib) | Python 3.9+ | Encode content for GitHub PUT; decode content from GitHub GET | Required by GitHub Contents API |
| `datetime` (stdlib) | Python 3.9+ | Produce YYYY-MM-DD date field per record | `datetime.date.today().isoformat()` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `shutil.which` (stdlib) | Python 3.9+ | Detect whether `gh` binary is on PATH | Use in `_run_gh()` before subprocess call to produce clean error message |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `subprocess` shelling to `gh` | `PyGithub` or `httpx` + token | Requires credential management; project explicitly chose `gh` to avoid this |
| `shutil.which` check | Catch `FileNotFoundError` | Both work; `which` check gives slightly cleaner error path but catching exception is equally valid |

**No new installation required** — all dependencies are stdlib or already in `pyproject.toml`.

---

## Architecture Patterns

### Recommended Project Structure

```
src/makenote/
├── __init__.py
├── cli.py          # Click group + all subcommands (mn, mn note, mn d, mn list)
├── config.py       # Existing — load_config, save_config, run_config_flow
├── constants.py    # Existing — CONFIG_PATH
└── github.py       # NEW — write_note(), read_notes(), _run_gh() helper

tests/
├── __init__.py
├── test_cli.py     # Existing + new command tests
├── test_config.py  # Existing
└── test_github.py  # NEW — github.py unit tests with monkeypatched subprocess
```

### Pattern 1: Click Subcommand with Optional Inline Argument

`mn` invokes the interactive flow. `mn d` and `mn d "text"` are implemented as a single subcommand `note` with an optional argument. The default subject shortcut `d` is handled by wiring the `note` command to also be reachable as `d` or by providing a dedicated `d` alias command.

The cleanest approach for `mn d "text"`:

```python
# Source: Click docs — https://click.palletsprojects.com/en/8.x/arguments/#variadic-arguments
@main.command()
@click.argument("subject")
@click.argument("note_text", required=False, default=None)
def note(subject: str, note_text: str | None) -> None:
    """Log a note to the given subject."""
    ...
```

However, because `mn d "text"` uses the default subject (`d` is the subject shorthand), the simpler design is:

```python
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
    _gh.write_note(cfg["repo"], subject, note_text)
    click.echo("Note logged.")
```

And `mn` (bare invocation with subject picker) is the existing `invoke_without_command` branch in `main()`.

**When to use:** `note_text` is `None` → prompt; not `None` → zero-interaction path.

### Pattern 2: GitHub Read-Modify-Write (GH-01)

The GitHub Contents API requires a read before every write (to get the current SHA). File content is base64-encoded in both directions.

```python
import base64
import json
import subprocess
import datetime

# Source: https://www.zufallsheld.de/2023/12/11/til-how-to-create-github-files-via-api
#         https://docs.github.com/en/rest/repos/contents

def _run_gh(*args: str) -> subprocess.CompletedProcess:
    """Run gh api subcommand. Raises GhNotInstalledError or GhNotAuthError on failure."""
    import shutil
    if not shutil.which("gh"):
        raise GhNotInstalledError()
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.lower()
        if "not logged in" in stderr or "auth" in stderr or "authentication" in stderr:
            raise GhNotAuthError()
        raise GhApiError(result.stderr.strip())
    return result


def write_note(repo: str, subject: str, note_text: str) -> None:
    path = f"notes/{subject}/notes.jsonl"
    endpoint = f"repos/{repo}/contents/{path}"

    # Step 1: GET current file (may not exist yet)
    get_result = subprocess.run(
        ["gh", "api", endpoint],
        capture_output=True,
        text=True,
    )

    new_record = json.dumps({
        "date": datetime.date.today().isoformat(),
        "subject": subject,
        "note": note_text,
    })

    if get_result.returncode == 0:
        # File exists — decode existing content, append, re-encode
        file_data = json.loads(get_result.stdout)
        existing_sha = file_data["sha"]
        existing_content = base64.b64decode(file_data["content"]).decode("utf-8")
        new_content = existing_content.rstrip("\n") + "\n" + new_record + "\n"
    else:
        # File does not exist — create it
        existing_sha = None
        new_content = new_record + "\n"

    encoded = base64.b64encode(new_content.encode("utf-8")).decode("ascii")

    put_args = [
        "gh", "api", "--method", "PUT", endpoint,
        "-F", f"message=note: add entry to {subject}",
        "-F", f"content={encoded}",
    ]
    if existing_sha:
        put_args += ["-F", f"sha={existing_sha}"]

    put_result = subprocess.run(put_args, capture_output=True, text=True)
    if put_result.returncode != 0:
        stderr = put_result.stderr
        if "422" in stderr or "conflict" in stderr.lower():
            raise ShaConflictError()
        raise GhApiError(stderr.strip())
```

### Pattern 3: mn list Display Format

Fetch JSONL from each subject folder, decode, parse, sort by date descending, print the most recent 20 records.

```python
def read_notes(repo: str, subjects: list[str]) -> list[dict]:
    records = []
    for subject in subjects:
        path = f"notes/{subject}/notes.jsonl"
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{path}"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            continue  # Subject file not yet created — skip silently
        file_data = json.loads(result.stdout)
        content = base64.b64decode(file_data["content"]).decode("utf-8")
        for line in content.splitlines():
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return sorted(records, key=lambda r: r["date"], reverse=True)[:20]
```

Display format (Claude's discretion — recommended):
```
2026-03-08  work      fixed the login bug
2026-03-07  personal  read chapter 3
```
Left-aligned columns: date (10 chars), subject (padded to longest subject name), note (truncated at 60 chars with ellipsis if longer).

### Pattern 4: Error Class Hierarchy in github.py

```python
class GhError(Exception):
    pass

class GhNotInstalledError(GhError):
    pass

class GhNotAuthError(GhError):
    pass

class ShaConflictError(GhError):
    pass

class GhApiError(GhError):
    pass
```

Callers in `cli.py` catch these and print the locked error messages.

### Anti-Patterns to Avoid

- **Importing `github.py` functions directly in cli.py:** Use `import makenote.github as _gh` (module-level) so tests can monkeypatch `_gh.write_note` without re-importing.
- **Stripping newlines from base64 content without decoding first:** GitHub may return content with embedded `\n` in the base64 string (line-wrapped). Use `base64.b64decode(content)` directly — the stdlib handles whitespace correctly.
- **Assuming file exists on first note:** Always treat a 404 GET response as "create new file" not an error.
- **Hardcoding `notes/` path prefix:** The REQUIREMENTS.md mentions a configurable `target_path`. Keep the path prefix as a constant or config field from the start — Phase 3 may expose it.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Base64 encode/decode | Custom encoding loop | `base64.b64encode` / `b64decode` (stdlib) | Handles padding, line-wrapping edge cases automatically |
| GitHub auth | Token storage, OAuth flow | `gh auth login` (user's responsibility, per requirements) | Out of scope by explicit project decision |
| Arrow-key TUI | curses-based picker | `questionary.select()` | Already in project; tested pattern |
| JSON serialization | String formatting | `json.dumps` / `json.loads` | Handles escaping; JSONL is just one record per line |

**Key insight:** The `gh api` CLI handles all OAuth token management, token refresh, and HTTP retry. The Python code only needs to call `subprocess.run` and parse stdout — no HTTP library needed.

---

## Common Pitfalls

### Pitfall 1: SHA Conflict on Concurrent Writes

**What goes wrong:** Two `mn` invocations run within seconds of each other. Both GET the same SHA, both try to PUT. The second PUT fails with HTTP 422 Unprocessable Entity because the SHA no longer matches.

**Why it happens:** GitHub's Contents API uses optimistic concurrency — the SHA you PUT must match the current blob SHA.

**How to avoid:** Detect 422 in the PUT response and surface the locked error message: `Error: write conflict — file may have changed. Try again.`

**Warning signs:** `returncode != 0` on PUT with `422` in stderr.

### Pitfall 2: base64 Content Has Embedded Newlines

**What goes wrong:** GitHub returns base64 content with `\n` every 60 characters for readability. Passing this directly to `base64.b64decode` without stripping newlines used to fail in some implementations.

**How to avoid:** Python's `base64.b64decode` accepts bytes with whitespace — pass the raw string value directly. Do NOT strip newlines manually before decoding; just call `base64.b64decode(file_data["content"])`.

**Confidence:** HIGH — stdlib behavior is well-documented.

### Pitfall 3: gh Not on PATH in Some Environments

**What goes wrong:** On macOS when `mn` is launched from a GUI context (e.g., IDE terminal without full shell), `gh` may not be in the subprocess PATH even if installed.

**How to avoid:** Use `shutil.which("gh")` to check before the subprocess call. This gives a clear error rather than `FileNotFoundError` propagating as a traceback.

**Warning signs:** `FileNotFoundError` raised by `subprocess.run(["gh", ...])`.

### Pitfall 4: questionary.select() "Add New" Placement

**What goes wrong:** Placing "Add New" at the bottom of a long subject list means users must scroll past all subjects to find it.

**How to avoid:** Place "Add New" as the first choice in the picker, separated from existing subjects with a `questionary.Separator()`.

### Pitfall 5: mn Command Routing Ambiguity

**What goes wrong:** `mn` is already a Click group with `invoke_without_command=True`. Adding the interactive note-logging flow into the existing `elif ctx.invoked_subcommand is None` branch means the bare `mn` invocation now logs a note instead of showing help.

**How to avoid:** Replace the current `click.echo(ctx.get_help())` branch with the subject picker + note input flow. The `mn --help` flag still works via Click's built-in flag handling regardless.

### Pitfall 6: Missing `target_path` in Config

**What goes wrong:** Notes stored at `notes/{subject}/notes.jsonl` hardcoded in Phase 2. Requirements mention a "configurable `target_path`" (GH-03) but the config schema from Phase 1 does not have this field.

**How to avoid:** Use a module-level constant `NOTES_ROOT = "notes"` in `github.py` for now, or add `target_path` to the config schema. Either approach is acceptable; the constant is simpler and can be made configurable in a later wave. Do NOT silently read a missing key from config — pick one approach and be consistent.

---

## Code Examples

### GET file and extract SHA + content

```python
# Source: https://www.zufallsheld.de/2023/12/11/til-how-to-create-github-files-via-api
result = subprocess.run(
    ["gh", "api", "repos/owner/repo/contents/notes/work/notes.jsonl"],
    capture_output=True,
    text=True,
)
if result.returncode == 0:
    data = json.loads(result.stdout)
    sha = data["sha"]
    content = base64.b64decode(data["content"]).decode("utf-8")
# returncode != 0 with 404 in stderr → file does not exist yet
```

### PUT to create or update a file

```python
# Source: https://www.zufallsheld.de/2023/12/11/til-how-to-create-github-files-via-api
encoded = base64.b64encode(new_content.encode("utf-8")).decode("ascii")

args = [
    "gh", "api", "--method", "PUT",
    "repos/owner/repo/contents/notes/work/notes.jsonl",
    "-F", "message=note: add entry to work",
    "-F", f"content={encoded}",
]
# Only include sha when updating (not creating)
if existing_sha:
    args += ["-F", f"sha={existing_sha}"]

result = subprocess.run(args, capture_output=True, text=True)
```

### Detect gh not installed vs not authenticated

```python
# Source: Python stdlib docs + community patterns
import shutil

def _check_gh_available() -> None:
    if not shutil.which("gh"):
        click.echo("Error: gh CLI not found. Install from https://cli.github.com")
        sys.exit(1)

# After subprocess call:
if result.returncode != 0:
    stderr = result.stderr.lower()
    if "not logged in" in stderr or "authentication" in stderr:
        click.echo("Error: gh not authenticated. Run: gh auth login")
        sys.exit(1)
```

### JSONL record format (GH-02, UX-03)

```python
import datetime, json
record = json.dumps({
    "date": datetime.date.today().isoformat(),  # "2026-03-08"
    "subject": "work",
    "note": "fixed the login bug",
})
# Append to file content: existing_content.rstrip("\n") + "\n" + record + "\n"
```

### mn list output format

```python
# Recommended display format
for r in records:  # sorted newest-first, max 20
    note_display = r["note"][:60] + "..." if len(r["note"]) > 60 else r["note"]
    print(f"{r['date']}  {r['subject']:<15}  {note_display}")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct GitHub API with personal access token | `gh api` CLI (handles auth) | `gh` CLI v1.0 (2020) | No credential storage needed in app |
| `subprocess.check_output` | `subprocess.run(capture_output=True)` | Python 3.7 | Cleaner; `capture_output=True` replaces `stdout=PIPE, stderr=PIPE` |

**No deprecated approaches apply to this phase.**

---

## Open Questions

1. **`target_path` in config schema**
   - What we know: GH-03 says "under configurable `target_path`" — but Phase 1 config schema has `repo`, `default_subject`, `subjects` only
   - What's unclear: Should Phase 2 add `target_path` to the config schema, or hardcode `notes/` for now?
   - Recommendation: Use module constant `NOTES_ROOT = "notes"` in `github.py` for Phase 2. Document that Phase 3 or a later wave can promote it to a config field. This keeps Phase 2 scope clean.

2. **`mn` bare invocation with config present**
   - What we know: Current `cli.py` shows help when invoked with no subcommand and config exists
   - What's unclear: The phase goal says `mn` should show the subject picker — but this changes the existing behavior of showing help
   - Recommendation: Replace the `click.echo(ctx.get_help())` branch with the subject picker flow. `mn --help` continues to work via Click's `--help` flag processing which runs before `invoke_without_command`.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (no version pinned; current install) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_github.py tests/test_cli.py -x -q` |
| Full suite command | `pytest -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GH-01 | write_note reads SHA, appends JSONL, PUTs to GitHub | unit (monkeypatch subprocess) | `pytest tests/test_github.py::test_write_note_update -x` | Wave 0 |
| GH-01 | write_note creates file when it does not exist | unit (monkeypatch subprocess) | `pytest tests/test_github.py::test_write_note_create -x` | Wave 0 |
| GH-02 | Written record has date, subject, note fields | unit | `pytest tests/test_github.py::test_record_format -x` | Wave 0 |
| GH-03 | Path constructed as notes/{subject}/notes.jsonl | unit | `pytest tests/test_github.py::test_path_construction -x` | Wave 0 |
| GH-04 | gh not installed → clean error, exit 1 | unit (monkeypatch shutil.which) | `pytest tests/test_github.py::test_gh_not_installed -x` | Wave 0 |
| GH-04 | gh not authenticated → clean error, exit 1 | unit (monkeypatch subprocess returncode) | `pytest tests/test_github.py::test_gh_not_authenticated -x` | Wave 0 |
| CORE-01 | `mn` with config shows subject picker and logs note | integration (CliRunner + monkeypatch) | `pytest tests/test_cli.py::test_mn_interactive -x` | Wave 0 |
| CORE-02 | `mn d` prompts for note text using default subject | integration (CliRunner + monkeypatch) | `pytest tests/test_cli.py::test_mn_d_prompts -x` | Wave 0 |
| CORE-03 | `mn d "text"` logs note with zero interaction | integration (CliRunner) | `pytest tests/test_cli.py::test_mn_d_inline -x` | Wave 0 |
| CORE-04 | `mn list` prints recent notes from all subjects | integration (CliRunner + monkeypatch) | `pytest tests/test_cli.py::test_mn_list -x` | Wave 0 |
| UX-02 | Subject picker includes "Add New" option | unit (questionary mock) | `pytest tests/test_cli.py::test_subject_picker_add_new -x` | Wave 0 |
| UX-03 | Each record has date field in YYYY-MM-DD format | unit | `pytest tests/test_github.py::test_date_field_format -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_github.py tests/test_cli.py -x -q`
- **Per wave merge:** `pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_github.py` — covers GH-01, GH-02, GH-03, GH-04, UX-03
- [ ] `src/makenote/github.py` — module stub with error classes and function signatures

*(test_cli.py and test_config.py already exist; new test functions for CORE-01 through CORE-04 and UX-02 are added to the existing file)*

---

## Sources

### Primary (HIGH confidence)
- https://www.zufallsheld.de/2023/12/11/til-how-to-create-github-files-via-api — exact `gh api` GET and PUT commands with SHA workflow, verified against official API behavior
- https://cli.github.com/manual/gh_api — `gh api` flags: `--method`, `-F`, `-f`, `-q`, `--input`, exit code behavior
- Python stdlib docs (subprocess, base64, datetime, shutil) — all stdlib; behavior is stable

### Secondary (MEDIUM confidence)
- https://docs.github.com/en/rest/repos/contents — GET/PUT Contents endpoint reference (page rendered without full content, but cross-verified with the practical examples above)
- WebSearch results confirming `FileNotFoundError` is the Python exception when subprocess cannot find `gh` binary

### Tertiary (LOW confidence)
- Community pattern for detecting `gh` auth failure from stderr text ("not logged in", "authentication") — common pattern in community scripts but not officially specified in `gh` docs

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all stdlib + already-installed deps; no new libraries needed
- GitHub API payload: HIGH — verified against working `gh api` examples from official-adjacent source
- Architecture patterns: HIGH — derived directly from existing Phase 1 code conventions
- Auth error detection from stderr: MEDIUM — community pattern, not official specification
- Pitfalls: HIGH — derived from GitHub API docs and known Python subprocess behavior

**Research date:** 2026-03-08
**Valid until:** 2026-09-08 (stable domain — `gh` CLI API and Python stdlib)
