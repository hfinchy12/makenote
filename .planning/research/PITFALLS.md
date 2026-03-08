# Pitfalls Research

**Domain:** Python CLI developer tool — gh subprocess, JSONL file writes, Homebrew tap distribution
**Researched:** 2026-03-08
**Confidence:** MEDIUM (web search unavailable; findings based on direct domain knowledge of gh CLI, Python packaging, and Homebrew tap patterns — flagged where verification is recommended)

---

## Critical Pitfalls

### Pitfall 1: gh api Requires SHA for File Updates — Missing It Causes Silent No-Op or 422

**What goes wrong:**
When updating an existing file via `gh api` (GitHub Contents API), the request body must include the existing file's `sha` field. Without the `sha`, GitHub returns HTTP 422 Unprocessable Entity. Many implementations fetch the file to read content but fail to also capture and pass back the `sha` when writing. The update call appears structurally correct but fails at runtime only when the file already exists.

**Why it happens:**
The first write (creating a new `notes.jsonl`) works fine — file creation does not require a `sha`. The bug is invisible on a clean setup and only surfaces on the second note logged to a subject. Developers often prototype against a fresh repo, ship, then discover the bug in real use.

**How to avoid:**
In `github.py`, the fetch-and-update flow must be a single function that:
1. Calls `gh api repos/{owner}/{repo}/contents/{path}` to GET the file
2. Captures BOTH `content` (base64 decoded) AND `sha` from the response
3. Appends the new JSONL record
4. Re-encodes as base64 and passes `sha` in the PUT request body

Treat GET + PUT as an atomic pair in one function, never split across call sites.

**Warning signs:**
- First note per subject succeeds, second note fails with a non-zero exit code from subprocess
- `gh api` stderr contains "422" or "sha" in the error message
- Manual testing against a new repo always passes

**Phase to address:**
Phase implementing GitHub write operations (`github.py`). Add an integration test that writes two notes to the same subject and verifies both are present.

---

### Pitfall 2: gh api Returns Base64-Encoded Content — Decoded Incorrectly Corrupts JSONL

**What goes wrong:**
The GitHub Contents API returns file content as base64. If the base64 string contains embedded newlines (GitHub adds them every 60 characters for readability), naive `base64.b64decode(content)` works, but `base64.b64decode(content.strip())` or string-split approaches can silently drop characters. The JSONL file appears to write but earlier records are corrupted or truncated.

**Why it happens:**
GitHub's base64 includes line breaks (`\n` every ~76 chars). Python's `base64.b64decode` handles this only when `validate=False` (the default). The trap is treating the content field as a clean base64 string — it is not. Any transformation that removes "whitespace only" before decoding will corrupt multi-line base64.

**How to avoid:**
Always decode with `base64.b64decode(content)` where `content` is the raw string from the API response — do not `.strip()`, `.replace('\n', '')`, or otherwise transform it before decoding. After decoding, immediately verify the result is valid UTF-8 before appending.

**Warning signs:**
- Decoded file content is shorter than expected
- `json.loads()` on individual JSONL lines raises `JSONDecodeError`
- Only manifests when `notes.jsonl` has grown beyond ~60 characters (GitHub starts adding line breaks)

**Phase to address:**
Phase implementing GitHub read/write (`github.py`). Unit test with a fixture that simulates a GitHub API response containing a multi-line base64 block.

---

### Pitfall 3: gh Subprocess Error Handling — Exit Code Only, Missing Stderr

**What goes wrong:**
`subprocess.run(['gh', 'api', ...])` returns a non-zero exit code on failure, but the error detail is in stderr. If stderr is not captured and surfaced, the user sees only "failed" with no actionable message. Common failures — not authenticated, repo not found, network unavailable, rate limited — all produce different stderr messages that developers need to see to diagnose problems.

**Why it happens:**
Python subprocess calls default to inheriting the parent process's stderr (it appears in the terminal), which works during development. In production, if output is captured (`capture_output=True` or `stderr=PIPE`), stderr disappears unless explicitly re-raised.

**How to avoid:**
Standardize all `gh api` calls with a wrapper in `github.py`:
- Use `subprocess.run(..., capture_output=True, text=True)`
- On non-zero `returncode`, raise a custom exception that includes `result.stderr.strip()`
- Let the top-level command handler in `main.py` catch this and print a user-friendly message that includes the original stderr detail

Never silently swallow `result.stderr`.

**Warning signs:**
- The tool says "Error logging note" but gives no reason
- Authentication failures are indistinguishable from network failures in user output
- `returncode` is checked but `stderr` is never read

**Phase to address:**
Phase implementing subprocess wrapper (`github.py`). Define a `GhCommandError` exception class early and use it everywhere from the start.

---

### Pitfall 4: gh Not Installed or Not Authenticated — No Graceful Check at Startup

**What goes wrong:**
If `gh` is not in PATH or not authenticated, every command fails with a confusing Python traceback (`FileNotFoundError`) or a raw `gh` error message. The tool has no preflight check, so users with fresh setups face cryptic errors instead of actionable guidance.

**Why it happens:**
Developers build and test with `gh` already installed and authenticated. The failure path is never exercised locally. It only surfaces when a new user installs via Homebrew, has `gh` installed but hasn't run `gh auth login`, or is using a machine where `gh` is not in PATH.

**How to avoid:**
At startup (before any command executes), run a preflight check:
1. `shutil.which('gh')` — if None, print "gh CLI not found. Install with: brew install gh" and exit
2. `subprocess.run(['gh', 'auth', 'status'], capture_output=True)` — if non-zero, print "gh not authenticated. Run: gh auth login" and exit

Both checks should run before config is read or any interactive flow starts.

**Warning signs:**
- Test suite never tests the "gh not present" path
- `main.py` calls into `github.py` functions before any auth check
- Homebrew formula declares `gh` as a dependency but the tool doesn't verify auth state

**Phase to address:**
Phase implementing `main.py` command routing. Preflight check must be the first thing every subcommand runs, or extracted into a shared `checks.py` called at CLI entry.

---

### Pitfall 5: First-Run Config Not Detected Globally — Individual Commands Fail Instead of Guiding Setup

**What goes wrong:**
`mn d "note"` is called on a fresh install with no `~/.config/makenote/config.json`. The command fails with a `KeyError` or `FileNotFoundError` deep in config loading rather than immediately redirecting the user to `mn config`. The user has no idea what went wrong.

**Why it happens:**
Developers run `mn config` first during development, so config always exists. The missing-config path is never tested. Each command file independently tries to read config without gating on existence.

**How to avoid:**
Config loading must be centralized in `config.py`. The loading function checks for config existence and returns a typed sentinel (or raises a `ConfigNotFoundError`). The `main.py` entry point catches `ConfigNotFoundError` and responds: "No configuration found. Run `mn config` to set up." before exiting cleanly. Never let `KeyError` or `FileNotFoundError` bubble to the user.

**Warning signs:**
- Individual command files call `config.load()` independently without a try/except
- No test exists for `mn d "note"` with a missing config file
- Error message mentions a file path or Python traceback rather than instructing the user

**Phase to address:**
Phase implementing config layer (`config.py`). The config-not-found guard should be in place before any command is wired up.

---

### Pitfall 6: JSONL File Partial Write — Appended Line Not Terminated With Newline

**What goes wrong:**
JSONL format requires each record to be on its own line terminated by `\n`. If the append logic produces a file where the last line is missing a trailing newline, the next append joins two records on one line. Both become unparseable by any JSONL reader. This accumulates silently — the tool "works" but `mn list` starts showing parse errors or skipping records.

**Why it happens:**
The append logic is often written as: `existing_content + new_json_record`. If `existing_content` does not end with `\n` (possible for a newly created file or after a partial write), the new record is appended directly to the last byte of the previous record.

**How to avoid:**
The append function must always ensure:
1. If `existing_content` is non-empty and does not end with `\n`, add one before appending
2. Every new record is written as `json.dumps(record) + '\n'`
3. After constructing the new content, validate that every line parses with `json.loads` before encoding and sending to GitHub

Defensive: `new_content = existing_content.rstrip('\n') + '\n' + new_line + '\n'` if `existing_content` else `new_line + '\n'`

**Warning signs:**
- `mn list` shows fewer records than expected
- A JSONL file in the GitHub repo has two JSON objects on one line when viewed raw
- `json.loads(line)` occasionally raises `JSONDecodeError` in the list command

**Phase to address:**
Phase implementing JSONL append logic (`github.py` or dedicated `notes.py`). Validate round-trip: write one record, write another, read back and confirm both lines parse.

---

### Pitfall 7: questionary Crashes or Hangs When stdin Is Not a TTY

**What goes wrong:**
`questionary` renders interactive prompts assuming stdin is a terminal. When `mn` is run in a non-interactive context — CI pipeline, subprocess from another script, redirected input — `questionary` either crashes with an `AttributeError`, hangs waiting for input, or produces garbled output. Even testing with `pytest` can trigger this if tests call the interactive flow directly.

**Why it happens:**
`questionary` (and its underlying `prompt_toolkit` dependency) reads terminal metadata from stdin. In a non-TTY context, that metadata is absent. The `mn d "note"` zero-interaction path avoids this, but `mn` and `mn d` (no note arg) both use `questionary`.

**How to avoid:**
Before calling any `questionary` function, guard with `sys.stdin.isatty()`. If stdin is not a TTY, either fall back to a non-interactive path or exit with a helpful error: "Interactive mode requires a terminal. Use `mn d \"your note\"` for non-interactive logging."

In tests, never call the `questionary` layer directly. Test the flow logic and GitHub write logic separately using mocks or fixtures that bypass the prompt.

**Warning signs:**
- Running `mn` inside a `pytest` test hangs indefinitely
- CI that runs integration tests fails with cryptic `prompt_toolkit` errors
- The tool is piped into another command and hangs

**Phase to address:**
Phase implementing the interactive flow (`flow.py`). Add the `isatty()` guard before the subject picker and note input prompt.

---

### Pitfall 8: pyproject.toml console_scripts Entry Point Points to Wrong Target

**What goes wrong:**
The `console_scripts` entry point in `pyproject.toml` silently installs a broken `mn` command. If the module path or function name is wrong, `mn` either raises `ImportError` at runtime or does nothing. The install step (`pip install -e .`) succeeds regardless because Python doesn't validate the import path at install time.

**Why it happens:**
`mn = "makenote.main:main"` — if `main.py` has no `main()` function (e.g., it uses `if __name__ == '__main__':` instead), the installed command fails at runtime. Or if the package directory is named `make_note` but `pyproject.toml` references `makenote`, the import fails. The mismatch is never caught by the build step.

**How to avoid:**
- Always define an explicit `def main():` function in `main.py` — never rely on `__main__` block alone for the entry point
- After `pip install -e .`, immediately run `mn --help` (or a smoke test) as part of the development setup to verify the entry point resolves
- CI should include a step that installs the package and runs the entry point command

**Warning signs:**
- `mn` is not found in PATH after `pip install -e .` (wrong package name in entry points)
- `mn` raises `ImportError` or `ModuleNotFoundError` at invocation
- No post-install smoke test in the project setup instructions

**Phase to address:**
Phase setting up `pyproject.toml` and project scaffold. The very first thing wired should be: `pyproject.toml` entry point → `main.py:main()` → `print("mn works")` — verified end-to-end before any real logic is added.

---

### Pitfall 9: Homebrew Formula SHA256 Mismatch After Re-Pushing a Tag

**What goes wrong:**
The Homebrew formula contains a hardcoded `sha256` of the release tarball. If a git tag is deleted and re-pushed (even to fix a typo in a release), GitHub regenerates a different tarball, making the SHA256 invalid. Any `brew install` attempt fails with "SHA256 mismatch" for all users until the formula is updated. This is a recoverable but highly disruptive mistake.

**Why it happens:**
Developers re-push tags during the release process to fix mistakes ("the tag was on the wrong commit"). Git tags are mutable by default. The formula is updated once and assumed stable.

**How to avoid:**
- Treat git tags as immutable: never delete and re-push a release tag
- Use GitHub Releases (not just tags) — the tarball URL is more stable
- Compute SHA256 from the tarball only after the tag is final: `curl -L <tarball_url> | shasum -a 256`
- Add a release checklist that includes: tag → release → SHA256 → formula update → verify `brew install` in a clean environment

**Warning signs:**
- You've deleted and re-pushed a tag at any point
- The formula was updated without re-downloading the tarball to verify the hash
- No test of `brew install` after a formula update

**Phase to address:**
Phase setting up Homebrew tap and release workflow. Document the release checklist explicitly and make SHA recomputation a mandatory step.

---

### Pitfall 10: Homebrew virtualenv_install_with_resources Requires All Python Dependencies Declared as Resources

**What goes wrong:**
Homebrew's `virtualenv_install_with_resources` does not use `pip` from the internet at install time. All Python dependencies must be declared as `resource` blocks in the formula with their own URL and SHA256. If `questionary` or `prompt_toolkit` is not listed, the install succeeds but `mn` fails at runtime with `ModuleNotFoundError`.

**Why it happens:**
During development, `pip install -e .` pulls dependencies from PyPI automatically. The Homebrew formula is written to mirror this but the resource blocks are easy to miss or to get version-mismatched. When `questionary` depends on `prompt_toolkit`, both must be declared as resources.

**How to avoid:**
Use `poet` (the Homebrew formula dependency generator) to generate resource blocks from your `pyproject.toml`:
```bash
pip install homebrew-pypi-poet
poet makenote
```
This outputs correct `resource` blocks with SHA256 for all transitive dependencies. Regenerate this every time a dependency is added or bumped.

**Warning signs:**
- The formula `def install` block has `virtualenv_install_with_resources` but only 0–1 `resource` blocks
- `mn` fails with `ModuleNotFoundError: No module named 'questionary'` after Homebrew install
- You never tested `brew install` from the formula in a clean environment (no pre-existing Python packages)

**Phase to address:**
Phase setting up the Homebrew formula. Run `poet` output and include all resources before publishing the tap.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode `python3.11` in Homebrew formula | Avoids version selection logic | Breaks when macOS ships with 3.13+ and Homebrew updates; user gets version conflicts | Never — use `python@3.12` or the latest stable and test forward |
| Put all logic in `main.py` | Faster prototyping | Untestable; GitHub calls, config reads, and interactive flow tangled together | MVP only, must refactor before Homebrew distribution |
| Catch bare `Exception` in subprocess calls | Prevents crashes | Swallows meaningful errors; makes debugging impossible | Never — always catch `subprocess.CalledProcessError` and `FileNotFoundError` separately |
| Read entire config on every command invocation | Simple | Fine for this scale | Always acceptable — config is tiny, disk reads are fast |
| No validation of config JSON after user edits externally | Simpler code | Config corruption causes cryptic crashes | Acceptable for MVP if `config.py` loads with try/except and guides user to re-run `mn config` |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `gh api` PUT file | Omitting `sha` in the PUT body | Always include `sha` from the GET response; without it, any file update 422s |
| `gh api` GET file | Not decoding base64 before appending | `base64.b64decode(response['content'])` — the `content` field is always base64 |
| `gh api` path encoding | Using spaces in `subject` names as folder names without URL encoding | Either enforce no-space subject names in `mn config`, or URL-encode path components before passing to `gh api` |
| `gh auth status` preflight | Checking only exit code without checking stderr | Exit 0 from `gh auth status` means authenticated; exit 1 means not authenticated — always check both |
| `questionary` on Windows | Assuming ANSI terminal codes work everywhere | Arrow-key pickers may fail on Windows cmd.exe; acceptable to mark Windows as unsupported for v1 |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Fetching entire JSONL file on every write | Slow for large note files | Acceptable for personal use (files stay small — hundreds of lines) | Never a real problem at personal scale; only a concern if the file exceeds ~1MB, which would take years of daily use |
| Fetching entire JSONL on `mn list` | Slow startup if file is large | Fetch and truncate server-side is not possible via GitHub Contents API; accept the tradeoff or cap file size | At ~500KB+ file size; negligible for years of daily use |
| Calling `gh auth status` on every command | 200–400ms startup latency | Cache auth check result in memory for the process lifetime; or skip if speed is a priority | Immediately noticeable if preflight adds >500ms — consider making it only run on first use or on explicit `mn check` |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Logging sensitive data in note content | User notes are in a (possibly public) GitHub repo | Document clearly that the target repo should be private; warn in first-run setup if repo visibility is unknown |
| Storing GitHub tokens in config | Token exposure if config file is readable by other processes | Do not store tokens — this is precisely why `gh` CLI is used; `gh` manages tokens in its own secure storage |
| Subject names with shell metacharacters | Shell injection if subject names are interpolated into subprocess commands | Always pass `gh api` arguments as list items in `subprocess.run`, never as a shell string; `shell=False` (the default) |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No confirmation after successful note log | User doesn't know if it worked | Always print a one-line success message: `Note logged. [subject] — "note preview..."` |
| `mn list` fetches from GitHub every time with no indication | Appears to hang on slow connections | Print "Fetching notes..." before the `gh api` call, or add a spinner |
| Config setup asks too many questions upfront | First-run friction defeats the tool's purpose | Ask only: repo and default subject; subjects list is just [default subject] initially; everything else is addable later |
| Silent success on `mn d "note"` (no output) | Power-user path feels broken | Always output the logged note as confirmation, even in zero-interaction mode |
| `mn config` overwrites subjects list when editing repo | Loses configured subjects | Load existing config, mutate only the changed field, and write back — never start from a blank config on edit |

---

## "Looks Done But Isn't" Checklist

- [ ] **gh api file update:** Verify that the second note written to the same subject persists (SHA bug only manifests on the second write, not the first)
- [ ] **JSONL integrity:** Open the `notes.jsonl` file raw in GitHub and verify each line is a single valid JSON object after 3+ writes
- [ ] **Homebrew install:** Install from the formula in a clean environment (no pre-existing Python packages in a fresh Docker container or VM) and run `mn --help`
- [ ] **First-run experience:** Delete `~/.config/makenote/config.json`, run `mn d "test"`, and verify the error message guides setup rather than showing a Python traceback
- [ ] **console_scripts entry point:** Run `which mn` after `pip install -e .` in a fresh virtualenv to confirm the command is on PATH and invokes the correct function
- [ ] **Non-TTY guard:** Run `echo "" | mn` and verify it exits cleanly with a message rather than hanging
- [ ] **Ctrl-C during questionary:** Press Ctrl-C mid-prompt and verify the tool exits cleanly without a traceback (`KeyboardInterrupt` must be caught at the top level)

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| SHA mismatch in Homebrew formula | LOW | Recompute SHA256 from the tarball URL, update formula, push to tap repo — users re-run `brew upgrade` |
| JSONL corruption (two records on one line) | MEDIUM | Manually edit the raw `notes.jsonl` file in GitHub's web editor to separate the fused lines; add a validation step in the code to prevent recurrence |
| config.json corrupted or missing after bad edit | LOW | Delete `~/.config/makenote/config.json` and re-run `mn config` — no data loss (notes are in GitHub) |
| `gh api` SHA mismatch error after concurrent writes from two machines | LOW-MEDIUM | The second write fails; retry logic is out of scope for v1; user must re-run the command |
| Homebrew formula missing resource blocks | MEDIUM | Re-run `poet`, add missing resources, push formula update — existing users must `brew reinstall makenote` |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| gh api SHA required for updates | GitHub write implementation (`github.py`) | Integration test: write two notes to same subject, verify both present |
| Base64 multi-line decode corruption | GitHub write implementation (`github.py`) | Unit test with multi-line base64 fixture simulating real GitHub response |
| gh subprocess stderr not captured | GitHub write implementation (`github.py`) | Test that auth failure produces readable error message, not raw traceback |
| gh not installed / not authenticated | `main.py` command routing (first phase with runnable CLI) | Test `mn d "x"` with `gh` absent from PATH — expect clean error, not traceback |
| First-run config not detected | Config layer (`config.py`) | Test all subcommands with missing config — all must route to setup guidance |
| JSONL partial write / missing newline | JSONL append logic | Round-trip test: write 3 records, read back, assert all 3 lines parse as JSON |
| questionary non-TTY crash | Interactive flow (`flow.py`) | Test that non-TTY stdin produces clean exit message |
| console_scripts wrong target | pyproject.toml scaffold (first phase) | Smoke test: install in fresh virtualenv, run `mn --help`, verify no ImportError |
| Homebrew SHA256 mismatch | Homebrew tap and release workflow phase | Verify `brew install` in clean environment after every formula change |
| Homebrew missing resource blocks | Homebrew tap phase | Run `poet` to generate resources; test clean install before publishing tap |

---

## Sources

- Domain knowledge: `gh` CLI GitHub Contents API behavior (SHA requirement, base64 encoding) — MEDIUM confidence; recommend verifying against `gh api --help` and GitHub REST API docs for file update endpoint
- Python packaging: `pyproject.toml` `console_scripts` behavior — HIGH confidence; well-documented in Python Packaging Authority docs
- Homebrew Python formula patterns: `virtualenv_install_with_resources` and `poet` tool — MEDIUM confidence; Homebrew Python documentation at https://docs.brew.sh/Python-for-Formula-Authors
- `questionary` / `prompt_toolkit` TTY behavior — MEDIUM confidence; observable behavior from prompt_toolkit source and known pattern in CLI tool development
- JSONL format specification: https://jsonlines.org — HIGH confidence; trivially verifiable

---
*Pitfalls research for: Python CLI developer note-logging tool (mn / MakeNote)*
*Researched: 2026-03-08*
