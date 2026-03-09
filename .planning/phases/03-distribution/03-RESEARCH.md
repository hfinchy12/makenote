# Phase 3: Distribution - Research

**Researched:** 2026-03-09
**Domain:** Homebrew personal tap, Python formula authoring
**Confidence:** HIGH

## Summary

This phase delivers a Homebrew personal tap so users can run `brew install hunterfinch/tap/makenote` on a clean macOS machine. The work is well-understood: Homebrew's `virtualenv_install_with_resources` pattern is the canonical approach for Python CLI tools, it is stable and well-documented, and the tap structure is a simple GitHub repo convention.

The main technical work is: (1) writing `Formula/makenote.rb` using the virtualenv pattern with explicit resource declarations for `click` and `questionary` (and their transitive dependencies), (2) generating correct SHA256 hashes for all resource URLs, and (3) writing `RELEASING.md` with the manual checklist. There is no novel problem-solving; every step maps to an established Homebrew convention.

One key blocker to watch: resource declarations require `sdist` tarballs from PyPI for every dependency (including transitive ones: `prompt-toolkit`, `wcwidth`). Use `brew update-python-resources` on the formula file to auto-generate or verify these stanzas — `homebrew-pypi-poet` is deprecated as of 2024 in favor of this built-in command.

**Primary recommendation:** Write the formula using `virtualenv_install_with_resources`, generate all resource stanzas with `brew update-python-resources --print-only ./Formula/makenote.rb`, and validate locally with `brew install --build-from-source ./Formula/makenote.rb` before pushing to the tap repo.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Tap repo structure**
- Dedicated `homebrew-tap` GitHub repo: `hunterfinch/homebrew-tap`
- Install command for users: `brew tap hunterfinch/tap` then `brew install makenote`
- Formula lives at `Formula/makenote.rb` in the make-note repo (source of truth) — copied to tap repo on each release
- User will create the `homebrew-tap` GitHub repo manually; this phase only writes the formula file

**Python formula approach**
- Use `virtualenv_install_with_resources` pattern — installs Homebrew Python and bundles `click` and `questionary` into an isolated venv; works on a completely clean machine
- Source URL: GitHub release tarball (`https://github.com/hunterfinch/make-note/archive/refs/tags/v0.1.0.tar.gz`)
- SHA256: placeholder in formula during development, with a clear comment explaining how to compute the real hash before publishing

**Release & publish workflow**
- Manual checklist process: bump version in `pyproject.toml` → create git tag → compute SHA256 of tarball → update `Formula/makenote.rb` → push formula to `homebrew-tap` repo
- Include `RELEASING.md` in the make-note repo root with step-by-step release instructions
- This phase delivers the formula and tap setup only; tagging v0.1.0 and first publish are deferred until Phase 2 is fully working

**Formula test block**
- `brew test makenote` verifies `mn --version` only — fast, no side effects, confirms binary is installed and wired correctly
- Plan includes a local verification task: `brew install --build-from-source ./Formula/makenote.rb` to confirm the formula works before pushing to the tap

### Claude's Discretion
- Exact `virtualenv_install_with_resources` resource declarations for click and questionary versions
- Formula `desc`, `homepage`, and metadata fields
- Structure of RELEASING.md (headings, detail level)

### Deferred Ideas (OUT OF SCOPE)
- PyPI distribution (`pip install makenote`) — DIST-03, explicitly v2 requirement
- GitHub Actions to auto-update the formula on new tags — manual workflow is sufficient for v1
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DIST-01 | Tool installable via Homebrew personal tap | Formula file + tap structure covered in Standard Stack and Architecture Patterns sections |
| DIST-02 | Homebrew formula declares `gh` as a dependency | `depends_on "gh"` syntax covered in Standard Stack and Code Examples sections |
</phase_requirements>

---

## Standard Stack

### Core
| Library / Tool | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| Homebrew Ruby formula DSL | N/A (built into Homebrew) | Describes package metadata, dependencies, install steps | The only mechanism for Homebrew tap packages |
| `Language::Python::Virtualenv` | built into Homebrew | Creates isolated venv in `libexec`; links bin to PATH | Official Homebrew pattern for Python apps since Python@3.12 requirement |
| `brew update-python-resources` | built into Homebrew | Generates/updates resource stanzas from PyPI | Replaced deprecated `homebrew-pypi-poet`; official tooling |

### Python Dependencies (resources to declare)
| Package | Min Version | Source |
|---------|-------------|--------|
| click | >=8.1 | `pyproject.toml` |
| questionary | >=2.0 | `pyproject.toml` |
| prompt-toolkit | >=3.0 (transitive dep of questionary) | Must be declared as resource |
| wcwidth | transitive dep of prompt-toolkit | Must be declared as resource |

> All resource URLs must point to PyPI `sdist` tarballs (`.tar.gz`), not wheels. Use `brew update-python-resources` to resolve exact versions and SHA256 hashes automatically.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `brew update-python-resources` | `homebrew-pypi-poet` | homebrew-pypi-poet is deprecated (Issue #74, 2024); built-in tooling is preferred |
| Manual tap | homebrew-core submission | homebrew-core requires audits, CI, maintainer review — overkill for a personal tool |
| GitHub release tarball | PyPI sdist as source URL | GitHub tarball is correct when PyPI is not the canonical distribution |

**Installation (for local testing):**
```bash
# Test the formula locally before pushing to tap
brew install --build-from-source ./Formula/makenote.rb

# Or verbose mode for debugging
HOMEBREW_NO_INSTALL_FROM_API=1 brew install --build-from-source --verbose --debug ./Formula/makenote.rb

# Generate/verify resource stanzas
brew update-python-resources --print-only ./Formula/makenote.rb
```

## Architecture Patterns

### Recommended Project Structure (new files this phase)
```
make-note/
├── Formula/
│   └── makenote.rb        # Source-of-truth formula; copied to tap on release
├── RELEASING.md           # Step-by-step release checklist
└── pyproject.toml         # Already exists; version bumped at release time

homebrew-tap/              # Separate GitHub repo: hunterfinch/homebrew-tap
└── Formula/
    └── makenote.rb        # Copy of Formula/makenote.rb from make-note repo
```

### Pattern 1: Homebrew Python Virtualenv Formula
**What:** A Ruby formula class that creates an isolated Python venv in `libexec`, installs all declared resources (dependencies) into the venv, then installs the package itself and links its entry-point scripts to `bin/`.

**When to use:** Any Python application distributed via Homebrew. Required since Homebrew Python@3.12 to prevent contamination of system `site-packages`.

**Example:**
```ruby
# Source: https://docs.brew.sh/Python-for-Formula-Authors
class Makenote < Formula
  include Language::Python::Virtualenv

  desc "Fast terminal note logging to GitHub"
  homepage "https://github.com/hunterfinch/make-note"
  url "https://github.com/hunterfinch/make-note/archive/refs/tags/v0.1.0.tar.gz"
  # PLACEHOLDER — compute with: curl -sL <url> | shasum -a 256
  sha256 "PLACEHOLDER_SHA256"
  license "MIT"

  depends_on "python@3.12"
  depends_on "gh"

  # Resource stanzas generated by: brew update-python-resources --print-only ./Formula/makenote.rb
  # Replace the stanzas below with the output of that command before publishing.
  resource "click" do
    url "https://files.pythonhosted.org/packages/.../click-8.1.x.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "questionary" do
    url "https://files.pythonhosted.org/packages/.../questionary-2.x.tar.gz"
    sha256 "PLACEHOLDER"
  end

  # prompt-toolkit and wcwidth are transitive deps; also required as resources
  resource "prompt-toolkit" do
    url "https://files.pythonhosted.org/packages/.../prompt_toolkit-3.x.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "wcwidth" do
    url "https://files.pythonhosted.org/packages/.../wcwidth-0.x.tar.gz"
    sha256 "PLACEHOLDER"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    system bin/"mn", "--version"
  end
end
```

### Pattern 2: Tap Repository Convention
**What:** A GitHub repo named `homebrew-tap` (with the `homebrew-` prefix) under the user's account, containing a `Formula/` subdirectory with `.rb` formula files.

**When to use:** Every personal Homebrew tap.

**User installation flow:**
```bash
# Two-step (explicit tap first)
brew tap hunterfinch/tap
brew install makenote

# One-step (shorthand, no prior tap needed)
brew install hunterfinch/tap/makenote
```

> Homebrew resolves `hunterfinch/tap` to `github.com/hunterfinch/homebrew-tap` automatically.

### Pattern 3: SHA256 Computation for Release
**What:** Every release requires computing the SHA256 of the source tarball and each resource tarball.

**For the main package tarball:**
```bash
# Source: common Homebrew release practice
curl -sL "https://github.com/hunterfinch/make-note/archive/refs/tags/v0.1.0.tar.gz" \
  | shasum -a 256 | awk '{ print $1 }'
```

**For resource stanzas:** run `brew update-python-resources` on the formula after updating the main `url`/`sha256` fields — it resolves and updates all resource SHA256s automatically.

### Anti-Patterns to Avoid
- **Using `depends_on "python3"` (alias):** Triggers audit error; must use `depends_on "python@3.12"` (specific minor version).
- **Omitting transitive dependencies:** `questionary` depends on `prompt-toolkit`, which depends on `wcwidth`. All must be declared as explicit resources — Homebrew does NOT resolve transitive deps automatically.
- **Using wheel URLs in resources:** Resources must point to `sdist` tarballs (`.tar.gz`), not `.whl` files.
- **Skipping local `--build-from-source` test:** Pushing to the tap without local validation risks a broken formula for all users.
- **Putting formula directly in repo root:** Supported but disorganized; `Formula/` subdirectory is the correct convention.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dependency SHA256 lookup | Manual PyPI browsing for each dep | `brew update-python-resources --print-only ./Formula/makenote.rb` | Automated, accurate, handles transitive deps |
| Python isolation | Custom install scripts | `virtualenv_install_with_resources` | Official pattern; handles venv, linking, and pip install correctly |
| Tap creation scaffolding | Manual directory setup | `brew tap-new username/tap` | Creates correct structure with CI templates |

**Key insight:** Homebrew provides purpose-built tooling for every step of Python formula creation. Manual approaches are error-prone and unnecessary.

## Common Pitfalls

### Pitfall 1: Missing Transitive Resource Declarations
**What goes wrong:** Formula installs successfully locally (where deps may already be present) but fails on a clean machine with `ModuleNotFoundError`.
**Why it happens:** `virtualenv_install_with_resources` only installs what is explicitly declared. Homebrew does not resolve `install_requires` automatically.
**How to avoid:** Always run `brew update-python-resources --print-only` to enumerate ALL transitive deps, not just direct ones.
**Warning signs:** Formula passes local `--build-from-source` but fails on CI or a clean VM.

### Pitfall 2: Wrong Python Version in `depends_on`
**What goes wrong:** `brew audit` flags the formula; alternatively, the formula silently uses the wrong Python.
**Why it happens:** `depends_on "python3"` or `depends_on "python"` are aliases, not valid formula dependencies.
**How to avoid:** Use `depends_on "python@3.12"` (or the current Homebrew stable Python minor version at time of writing).
**Warning signs:** `brew audit --new-formula Formula/makenote.rb` reports a dependency error.

### Pitfall 3: SHA256 Placeholder Left in Published Formula
**What goes wrong:** `brew install` fails with a SHA256 mismatch error for every user.
**Why it happens:** The formula file ships with a placeholder SHA256 that was never replaced before pushing to the tap.
**How to avoid:** RELEASING.md must include an explicit step: "compute SHA256 → update formula → verify locally → then push."
**Warning signs:** The word `PLACEHOLDER` remaining in any `sha256` field of the formula.

### Pitfall 4: PyPI sdist Not Available for a Dependency
**What goes wrong:** `brew update-python-resources` fails to find a source tarball for a dependency.
**Why it happens:** Some packages only publish wheels on PyPI.
**How to avoid:** `click` and `questionary` both have sdists; this is low risk for the known deps. Verify with `pip download --no-binary :all: click questionary` in a test venv.
**Warning signs:** `brew update-python-resources` reports "no sdist" for a package.

### Pitfall 5: `gh` Version Mismatch After Install
**What goes wrong:** `mn` commands fail because `gh` is present but outdated (authentication or API changes).
**Why it happens:** `depends_on "gh"` ensures `gh` is installed but does not enforce a minimum version.
**How to avoid:** This is acceptable for v1; the formula satisfies DIST-02. Document minimum `gh` version in README if known.
**Warning signs:** `gh api` calls return unexpected errors after Homebrew install.

## Code Examples

Verified patterns from official sources:

### Complete Minimal Formula Structure
```ruby
# Source: https://docs.brew.sh/Python-for-Formula-Authors
class Makenote < Formula
  include Language::Python::Virtualenv

  desc "Fast terminal note logging to GitHub"
  homepage "https://github.com/hunterfinch/make-note"
  url "https://github.com/hunterfinch/make-note/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "PLACEHOLDER_COMPUTE_WITH_CURL_SHASUM"
  license "MIT"

  depends_on "python@3.12"
  depends_on "gh"

  # Generated by: brew update-python-resources --print-only ./Formula/makenote.rb
  resource "click" do
    url "..."
    sha256 "..."
  end

  # ... additional resources ...

  def install
    virtualenv_install_with_resources
  end

  test do
    system bin/"mn", "--version"
  end
end
```

### Generating Resource Stanzas
```bash
# Source: https://docs.brew.sh/Python-for-Formula-Authors (brew update-python-resources section)

# Step 1: Write formula with correct url/sha256 for main package, placeholder resources
# Step 2: Run to auto-generate all resource stanzas
brew update-python-resources --print-only Formula/makenote.rb

# Step 3: Paste output into formula, replacing placeholder resource blocks
# Step 4: Validate locally
brew install --build-from-source Formula/makenote.rb
brew test makenote
```

### Computing Tarball SHA256 at Release Time
```bash
# Source: Homebrew Formula Cookbook / common release practice
curl -sL "https://github.com/hunterfinch/make-note/archive/refs/tags/v0.1.0.tar.gz" \
  | shasum -a 256 | awk '{ print $1 }'
```

### User Tap & Install Commands
```bash
# Source: https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap
brew tap hunterfinch/tap
brew install makenote

# Or one-liner:
brew install hunterfinch/tap/makenote
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `homebrew-pypi-poet` (third-party) | `brew update-python-resources` (built-in) | ~2021–2023 (poet deprecated 2024) | Use built-in; poet still works but is unmaintained |
| `depends_on "python3"` | `depends_on "python@3.12"` (specific version) | Several years ago | Alias form triggers brew audit failure |
| Formulae without venv | `virtualenv_install_with_resources` required for Python@3.12+ | Python@3.12 era | Mandatory isolation; older pattern no longer accepted |

**Deprecated/outdated:**
- `homebrew-pypi-poet`: Deprecated (Issue #74). Still installable but unmaintained; replaced by `brew update-python-resources`.
- `venv.pip_install_and_link buildpath` (verbose form): Still works but `virtualenv_install_with_resources` is the idiomatic one-liner.

## Open Questions

1. **Exact resource SHA256 values for click 8.x, questionary 2.x, prompt-toolkit 3.x, wcwidth**
   - What we know: These packages have sdists on PyPI; exact versions and hashes must be resolved at formula-writing time
   - What's unclear: Minor version pins (e.g., `click 8.1.8` vs `8.1.7`) — depends on PyPI state when `brew update-python-resources` runs
   - Recommendation: Do not hardcode; use `brew update-python-resources --print-only` as the authoritative source during the write-formula task

2. **Current Homebrew stable Python minor version**
   - What we know: `python@3.12` and `python@3.13` are both available in Homebrew as of early 2026; `python@3.12` is widely used in formulas
   - What's unclear: Which is the "current" version Homebrew prefers for new formulas
   - Recommendation: Use `python@3.12` as the conservative, well-supported choice; update to `python@3.13` if `brew audit` recommends it

3. **`brew test` block: `--version` vs functional test**
   - What we know: Homebrew documentation says `--version` is a "bad test" but acceptable if no better option exists; the context decision locks `mn --version` as the test
   - What's unclear: Nothing — this is locked by the user's decision and acceptable per Homebrew's own guidance
   - Recommendation: Implement as decided (`system bin/"mn", "--version"`); this is sufficient for a personal tap

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing, configured in `pyproject.toml`) |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DIST-01 | `brew install hunterfinch/tap/makenote` succeeds; `mn --version` runs | manual/smoke | `brew install --build-from-source Formula/makenote.rb && brew test makenote` | ❌ Wave 0 (formula file) |
| DIST-02 | Formula declares `gh` as dependency; `gh` installed automatically | manual/inspection | `grep 'depends_on "gh"' Formula/makenote.rb` | ❌ Wave 0 (formula file) |

> DIST-01 and DIST-02 are verified through formula content inspection and a local `--build-from-source` smoke test, not via pytest unit tests. No pytest tests are needed for this phase.

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q` (existing suite, confirms no regressions)
- **Per wave merge:** `pytest tests/` + `grep 'depends_on "gh"' Formula/makenote.rb`
- **Phase gate:** Formula file present and correct + local `brew install --build-from-source` passes before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `Formula/makenote.rb` — covers DIST-01 and DIST-02 (the primary deliverable of this phase)
- [ ] `RELEASING.md` — release documentation

*(No pytest gaps — existing test infrastructure covers regressions; distribution requirements are verified via formula inspection and brew tooling, not pytest.)*

## Sources

### Primary (HIGH confidence)
- `https://docs.brew.sh/Python-for-Formula-Authors` — virtualenv_install_with_resources pattern, resource declarations, install method, `brew update-python-resources` usage
- `https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap` — tap repo structure, `brew tap-new`, user install commands
- `https://docs.brew.sh/Formula-Cookbook` — `depends_on` syntax, test block guidance

### Secondary (MEDIUM confidence)
- `https://til.simonwillison.net/homebrew/packaging-python-cli-for-homebrew` — real-world Python CLI formula template verified against official docs
- `https://safjan.com/publishing-python-cli-tool-to-homebrew/` — step-by-step guide consistent with official docs
- `https://github.com/tdsmith/homebrew-pypi-poet/issues/74` — deprecation of homebrew-pypi-poet confirmed; `brew update-python-resources` recommended as replacement

### Tertiary (LOW confidence)
- WebSearch results on Python version specifics (`python@3.12` vs `python@3.13`) — exact "preferred" version for new formulas needs confirmation via `brew audit` at task time

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — virtualenv_install_with_resources is documented on official Homebrew docs; tap structure verified via official docs
- Architecture: HIGH — formula structure and tap conventions verified with official sources
- Pitfalls: HIGH for transitive deps and SHA256 issues (documented in official sources); MEDIUM for Python version pin (current preferred version may shift)
- Resource SHA256 values: LOW — must be computed at task execution time; not resolvable during research

**Research date:** 2026-03-09
**Valid until:** 2026-09-09 (stable domain; Homebrew Python formula conventions change slowly)
