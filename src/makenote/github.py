"""
GitHub I/O module for makenote.

Provides write_note() and read_notes() as the single public interface for
all GitHub API interactions. Encapsulates gh CLI subprocess calls, base64
encoding/decoding, and error classification. cli.py stays clean.
"""
from __future__ import annotations

import base64
import datetime
import json
import shutil
import subprocess

# Module-level constant — keeps path prefix configurable for future phases.
NOTES_ROOT = "notes"


# ---------------------------------------------------------------------------
# Error hierarchy
# ---------------------------------------------------------------------------

class GhError(Exception):
    """Base class for all gh-related errors."""


class GhNotInstalledError(GhError):
    """Raised when the gh CLI binary is not found on PATH."""


class GhNotAuthError(GhError):
    """Raised when gh returns an authentication failure."""


class ShaConflictError(GhError):
    """Raised when a PUT request fails with a 422 SHA conflict."""


class GhApiError(GhError):
    """Raised for non-zero gh exit codes that are not auth or conflict errors."""


# ---------------------------------------------------------------------------
# Private helper
# ---------------------------------------------------------------------------

def _run_gh(*args: str) -> subprocess.CompletedProcess:
    """
    Run a gh subcommand.

    Raises GhNotInstalledError if gh is not on PATH.
    Raises GhNotAuthError on authentication failures.
    Raises GhApiError on other non-zero exit codes.
    """
    if not shutil.which("gh"):
        raise GhNotInstalledError("gh CLI not found. Install from https://cli.github.com")

    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        stderr = result.stderr.lower()
        if "not logged in" in stderr or "auth" in stderr or "authentication" in stderr:
            raise GhNotAuthError("gh not authenticated. Run: gh auth login")
        raise GhApiError(result.stderr.strip())

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def write_note(repo: str, subject: str, note_text: str) -> None:
    """
    Append a note record to the subject's JSONL file in the GitHub repo.

    Performs read-modify-write:
    1. GET the current file to obtain its SHA (required for updating).
    2. Append a new JSONL record.
    3. PUT the updated content back.

    If the file does not yet exist (GET returns non-zero), creates it without
    including a sha field in the PUT request.

    Args:
        repo: GitHub repo in "owner/repo" format.
        subject: Subject name (used for path and record field).
        note_text: Text of the note to log.

    Raises:
        GhNotInstalledError: gh CLI binary not on PATH.
        GhNotAuthError: gh not authenticated.
        ShaConflictError: PUT fails with 422 (stale SHA).
        GhApiError: Other gh API failure.
    """
    # Check for gh before doing anything (consistent error handling)
    if not shutil.which("gh"):
        raise GhNotInstalledError("gh CLI not found. Install from https://cli.github.com")

    path = f"{NOTES_ROOT}/{subject}/notes.jsonl"
    endpoint = f"repos/{repo}/contents/{path}"

    # Step 1: GET current file (404 is normal for new files — not an error)
    get_result = subprocess.run(
        ["gh", "api", endpoint],
        capture_output=True,
        text=True,
    )

    # Step 2: Build the new JSONL record
    new_record = json.dumps({
        "date": datetime.date.today().isoformat(),
        "subject": subject,
        "note": note_text,
    })

    if get_result.returncode == 0:
        # File exists — decode existing content, append new record, capture sha
        file_data = json.loads(get_result.stdout)
        existing_sha: str | None = file_data["sha"]
        existing_content = base64.b64decode(file_data["content"]).decode("utf-8")
        new_content = existing_content.rstrip("\n") + "\n" + new_record + "\n"
    else:
        # Check if the GET failure is auth-related (not a simple 404)
        stderr = get_result.stderr.lower()
        if get_result.returncode != 0 and (
            "not logged in" in stderr or ("auth" in stderr and "404" not in stderr and "not found" not in stderr)
        ):
            raise GhNotAuthError("gh not authenticated. Run: gh auth login")
        # Treat as "file does not exist yet" — create it
        existing_sha = None
        new_content = new_record + "\n"

    # Step 3: Base64-encode the new content for the PUT payload
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
            raise ShaConflictError("write conflict — file may have changed. Try again.")
        raise GhApiError(stderr.strip())


def read_notes(repo: str, subjects: list[str]) -> list[dict]:
    """
    Fetch and return recent notes across all given subjects.

    For each subject, GETs its notes.jsonl file from GitHub, decodes the
    base64 content, and parses each JSONL line. Missing files (404) are
    silently skipped. Returns records sorted by date descending, max 20.

    Args:
        repo: GitHub repo in "owner/repo" format.
        subjects: List of subject names to fetch notes for.

    Returns:
        List of note dicts (with date, subject, note keys), newest first,
        at most 20 records total.
    """
    records: list[dict] = []

    for subject in subjects:
        path = f"{NOTES_ROOT}/{subject}/notes.jsonl"
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{path}"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # Subject file not yet created or other error — skip silently
            continue

        file_data = json.loads(result.stdout)
        content = base64.b64decode(file_data["content"]).decode("utf-8")

        for line in content.splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    # Skip malformed lines
                    pass

    return sorted(records, key=lambda r: r.get("date", ""), reverse=True)[:20]
