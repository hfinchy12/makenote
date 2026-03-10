# Releasing makenote

## Prerequisites

- Homebrew installed locally
- `hfinchy12/homebrew-tap` GitHub repo exists (create it at github.com/new with name `homebrew-tap` if not already done)
- All Phase 2 features verified working end-to-end

## Release Steps

1. Bump version in `pyproject.toml` (`version = "X.Y.Z"`)

2. Commit the version bump:
   ```bash
   git commit -am "chore: bump version to X.Y.Z"
   ```

3. Create and push the git tag:
   ```bash
   git tag vX.Y.Z
   git push origin main
   git push origin vX.Y.Z
   ```

4. Wait ~30 seconds for GitHub to make the tarball available, then compute the SHA256:
   ```bash
   curl -sL "https://github.com/hfinchy12/make-note/archive/refs/tags/vX.Y.Z.tar.gz" \
     | shasum -a 256 | awk '{ print $1 }'
   ```

5. Update `Formula/makenote.rb`:
   - Set `url` to the new tarball URL (replace `v0.1.0` with `vX.Y.Z`)
   - Set `sha256` to the hash computed in step 4 (replacing the PLACEHOLDER line)

6. Regenerate resource stanzas (resolves exact dep versions and real hashes):
   ```bash
   brew update-python-resources --print-only Formula/makenote.rb
   ```
   Paste the output into `Formula/makenote.rb`, replacing all resource blocks. Confirm all URLs are `.tar.gz` sdists, not `.whl` wheels.

   Note: This command requires the formula to be inside a tap. If running it locally, temporarily copy the formula into your local tap directory first:
   ```bash
   brew tap hfinchy12/tap
   cp Formula/makenote.rb $(brew --prefix)/Library/Taps/hfinchy12/homebrew-tap/Formula/makenote.rb
   brew update-python-resources --print-only hfinchy12/tap/makenote
   ```

7. Verify the formula locally:
   ```bash
   brew install --build-from-source Formula/makenote.rb
   brew test makenote
   ```
   Confirm `mn --version` outputs the correct version string.

8. Run the existing test suite:
   ```bash
   pytest tests/ -x -q
   ```

9. Copy the formula to the tap repo and publish:
   ```bash
   cp Formula/makenote.rb /path/to/homebrew-tap/Formula/makenote.rb
   cd /path/to/homebrew-tap
   git add Formula/makenote.rb
   git commit -m "makenote vX.Y.Z"
   git push origin main
   ```

10. Verify the user install path works:
    ```bash
    brew tap hfinchy12/tap
    brew install makenote
    mn --version
    ```

## Troubleshooting

- **"SHA256 mismatch"** — recompute hash (step 4); confirm the tag was pushed before computing
- **"ModuleNotFoundError" after brew install** — a transitive dep is missing from resources; rerun `brew update-python-resources` and ensure click, questionary, prompt-toolkit, and wcwidth are all declared
- **`brew update-python-resources` fails** — confirm the main `url` points to a real published tarball before running; the formula must also be inside a tap directory (see step 6 note)
- **Wrong Python version error** — formula uses `python@3.12`; run `brew install python@3.12` if missing
- **PLACEHOLDER remains in formula** — do not push to tap until all sha256 fields are replaced with real hashes

## Formula Location

- **Source of truth:** `Formula/makenote.rb` in this repo (make-note)
- **Published copy:** `Formula/makenote.rb` in `hfinchy12/homebrew-tap`
- Always update the source-of-truth file first, then copy to the tap repo
