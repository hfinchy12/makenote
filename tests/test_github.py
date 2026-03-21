"""
Unit tests for makenote.github module.

All subprocess.run calls are monkeypatched — no real network calls.
Tests cover GH-01 (update + create), GH-02, GH-03, GH-04, UX-03, and SHA conflict.
"""
from __future__ import annotations

import base64
import json
import re
from types import SimpleNamespace

import pytest

from makenote.github import (
    GhNotAuthError,
    GhNotInstalledError,
    ShaConflictError,
    write_note,
    read_notes,
    _validate_subject,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(returncode: int = 0, stdout: str = "", stderr: str = "") -> SimpleNamespace:
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def _encoded(text: str) -> str:
    """Return base64-encoded text as an ASCII string (simulates GitHub response)."""
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


EXISTING_SHA = "abc123deadbeef"
EXISTING_CONTENT = json.dumps({"date": "2026-01-01", "subject": "work", "note": "old note"}) + "\n"


def _get_success_result() -> SimpleNamespace:
    """Simulate a successful GET response with existing file content."""
    payload = json.dumps({"sha": EXISTING_SHA, "content": _encoded(EXISTING_CONTENT)})
    return _make_result(returncode=0, stdout=payload)


def _get_not_found_result() -> SimpleNamespace:
    """Simulate a 404 GET response (file does not exist yet)."""
    return _make_result(returncode=1, stderr="HTTP 404: Not Found")


def _put_success_result() -> SimpleNamespace:
    return _make_result(returncode=0, stdout="{}")


# ---------------------------------------------------------------------------
# GH-01: write_note update path (file already exists)
# ---------------------------------------------------------------------------

def test_write_note_update(monkeypatch):
    """write_note with existing file: GET returns sha+content; PUT includes sha field."""
    calls = []

    def fake_run(args, capture_output=False, text=False):
        calls.append(args)
        # First call is GET, second is PUT
        if len(calls) == 1:
            return _get_success_result()
        return _put_success_result()

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/local/bin/gh")

    write_note("owner/repo", "work", "new note text")

    # There should be exactly two subprocess calls: GET and PUT
    assert len(calls) == 2, f"Expected 2 calls, got {len(calls)}"

    put_args = calls[1]
    put_str = " ".join(str(a) for a in put_args)

    # PUT must include --method PUT
    assert "--method" in put_args
    assert "PUT" in put_args

    # PUT must include sha= field
    sha_args = [a for a in put_args if isinstance(a, str) and a.startswith("sha=")]
    assert sha_args, "PUT call must include a sha= field for updates"
    assert EXISTING_SHA in sha_args[0]

    # The content field must decode to include both the old content and the new record
    content_args = [a for a in put_args if isinstance(a, str) and a.startswith("content=")]
    assert content_args, "PUT call must include a content= field"
    encoded_content = content_args[0][len("content="):]
    decoded = base64.b64decode(encoded_content).decode("utf-8")
    assert "old note" in decoded
    assert "new note text" in decoded


# ---------------------------------------------------------------------------
# GH-01: write_note create path (file does not exist yet)
# ---------------------------------------------------------------------------

def test_write_note_create(monkeypatch):
    """write_note with new file: GET returns non-zero; PUT does NOT include sha field."""
    calls = []

    def fake_run(args, capture_output=False, text=False):
        calls.append(args)
        if len(calls) == 1:
            return _get_not_found_result()
        return _put_success_result()

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/local/bin/gh")

    write_note("owner/repo", "personal", "first note ever")

    assert len(calls) == 2, f"Expected 2 calls, got {len(calls)}"

    put_args = calls[1]

    # PUT must NOT include sha= field for new files
    sha_args = [a for a in put_args if isinstance(a, str) and a.startswith("sha=")]
    assert not sha_args, "PUT call must NOT include sha= when creating a new file"


# ---------------------------------------------------------------------------
# GH-02: Record format has date, subject, note keys
# ---------------------------------------------------------------------------

def test_record_format(monkeypatch):
    """The JSONL record written to GitHub has date, subject, and note fields."""
    captured_put_args = []

    def fake_run(args, capture_output=False, text=False):
        if len(captured_put_args) == 0:
            return _get_not_found_result()
        captured_put_args.append(args)
        return _put_success_result()

    # Use a list to track call count
    call_count = [0]

    def fake_run2(args, capture_output=False, text=False):
        call_count[0] += 1
        if call_count[0] == 1:
            return _get_not_found_result()
        captured_put_args.append(args)
        return _put_success_result()

    monkeypatch.setattr("subprocess.run", fake_run2)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/local/bin/gh")

    write_note("owner/repo", "work", "some note content")

    assert captured_put_args, "PUT call was not made"
    put_args = captured_put_args[0]

    content_args = [a for a in put_args if isinstance(a, str) and a.startswith("content=")]
    assert content_args, "content= field missing from PUT"
    encoded_content = content_args[0][len("content="):]
    decoded = base64.b64decode(encoded_content).decode("utf-8")

    # Parse the last non-empty line as JSON
    lines = [l for l in decoded.splitlines() if l.strip()]
    assert lines, "No JSONL lines in written content"
    record = json.loads(lines[-1])

    assert "date" in record, "Record missing 'date' key"
    assert "subject" in record, "Record missing 'subject' key"
    assert "note" in record, "Record missing 'note' key"
    assert record["subject"] == "work"
    assert record["note"] == "some note content"


# ---------------------------------------------------------------------------
# GH-03: Path construction uses notes/{subject}/notes.jsonl
# ---------------------------------------------------------------------------

def test_path_construction(monkeypatch):
    """The GET and PUT endpoints include 'notes/{subject}/notes.jsonl'."""
    calls = []

    def fake_run(args, capture_output=False, text=False):
        calls.append(args)
        if len(calls) == 1:
            return _get_not_found_result()
        return _put_success_result()

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/local/bin/gh")

    write_note("owner/repo", "mysubject", "hello")

    for call_args in calls:
        call_str = " ".join(str(a) for a in call_args)
        assert "notes/mysubject/notes.jsonl" in call_str, (
            f"Expected 'notes/mysubject/notes.jsonl' in call args: {call_str}"
        )


# ---------------------------------------------------------------------------
# GH-04: gh not installed → GhNotInstalledError
# ---------------------------------------------------------------------------

def test_gh_not_installed(monkeypatch):
    """When gh is not on PATH, write_note raises GhNotInstalledError."""
    monkeypatch.setattr("shutil.which", lambda name: None)

    with pytest.raises(GhNotInstalledError):
        write_note("owner/repo", "work", "note text")


# ---------------------------------------------------------------------------
# GH-04: gh not authenticated → GhNotAuthError
# ---------------------------------------------------------------------------

def test_gh_not_authenticated(monkeypatch):
    """When gh returns non-zero with auth-related stderr, write_note raises GhNotAuthError."""
    call_count = [0]

    def fake_run(args, capture_output=False, text=False):
        call_count[0] += 1
        if call_count[0] == 1:
            # GET fails with auth error
            return _make_result(returncode=1, stderr="not logged in to any GitHub hosts")
        return _put_success_result()

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/local/bin/gh")

    with pytest.raises(GhNotAuthError):
        write_note("owner/repo", "work", "note text")


# ---------------------------------------------------------------------------
# UX-03: date field matches YYYY-MM-DD format
# ---------------------------------------------------------------------------

def test_date_field_format(monkeypatch):
    """The date field in the written JSONL record matches the YYYY-MM-DD pattern."""
    captured_put_args = []
    call_count = [0]

    def fake_run(args, capture_output=False, text=False):
        call_count[0] += 1
        if call_count[0] == 1:
            return _get_not_found_result()
        captured_put_args.append(args)
        return _put_success_result()

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/local/bin/gh")

    write_note("owner/repo", "work", "note with date")

    assert captured_put_args, "PUT call was not made"
    put_args = captured_put_args[0]

    content_args = [a for a in put_args if isinstance(a, str) and a.startswith("content=")]
    encoded_content = content_args[0][len("content="):]
    decoded = base64.b64decode(encoded_content).decode("utf-8")

    lines = [l for l in decoded.splitlines() if l.strip()]
    record = json.loads(lines[-1])

    date_value = record["date"]
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", date_value), (
        f"Date '{date_value}' does not match YYYY-MM-DD pattern"
    )


# ---------------------------------------------------------------------------
# SHA conflict: PUT returns 422 → ShaConflictError
# ---------------------------------------------------------------------------

def test_sha_conflict(monkeypatch):
    """When PUT returns non-zero with 422 in stderr, write_note raises ShaConflictError."""
    call_count = [0]

    def fake_run(args, capture_output=False, text=False):
        call_count[0] += 1
        if call_count[0] == 1:
            return _get_success_result()
        # PUT fails with 422 conflict
        return _make_result(returncode=1, stderr="HTTP 422: Unprocessable Entity - sha does not match")

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/local/bin/gh")

    with pytest.raises(ShaConflictError):
        write_note("owner/repo", "work", "note text")


# ---------------------------------------------------------------------------
# GH-04: read_notes() — gh not installed → GhNotInstalledError
# ---------------------------------------------------------------------------

def test_read_notes_gh_not_installed(monkeypatch):
    """read_notes() raises GhNotInstalledError when gh is not on PATH."""
    monkeypatch.setattr("shutil.which", lambda name: None)

    with pytest.raises(GhNotInstalledError):
        read_notes("owner/repo", ["work"])


# ---------------------------------------------------------------------------
# GH-04: read_notes() — gh not authenticated → GhNotAuthError
# ---------------------------------------------------------------------------

def test_read_notes_gh_not_authenticated(monkeypatch):
    """read_notes() raises GhNotAuthError when gh returns auth-related stderr."""

    def fake_run(args, capture_output=False, text=False):
        return _make_result(returncode=1, stderr="not logged in to any GitHub hosts")

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/local/bin/gh")

    with pytest.raises(GhNotAuthError):
        read_notes("owner/repo", ["work"])


# ---------------------------------------------------------------------------
# GH-04: read_notes() — 404 silently skipped (existing behavior preserved)
# ---------------------------------------------------------------------------

def test_read_notes_404_skipped(monkeypatch):
    """read_notes() silently skips subjects with 404 file-not-found errors."""

    def fake_run(args, capture_output=False, text=False):
        return _make_result(returncode=1, stderr="HTTP 404: Not Found")

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/local/bin/gh")

    result = read_notes("owner/repo", ["work", "personal"])
    assert result == [], f"Expected empty list for 404, got {result}"


# ---------------------------------------------------------------------------
# Security: subject validation (path traversal prevention)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("subject", [
    "work",
    "my-notes",
    "notes_2024",
    "ABC",
    "a1-b2_c3",
])
def test_validate_subject_valid(subject):
    """Valid subject names pass validation without raising."""
    _validate_subject(subject)  # should not raise


@pytest.mark.parametrize("subject", [
    "work/../admin",
    "../../etc/passwd",
    "notes/evil",
    "sub ject",
    "subject!",
    "",
    ".",
    "..",
])
def test_validate_subject_invalid(subject):
    """Invalid subject names raise ValueError."""
    with pytest.raises(ValueError, match="Invalid subject name"):
        _validate_subject(subject)


def test_write_note_rejects_traversal_subject(monkeypatch):
    """write_note raises ValueError before making any API calls for invalid subjects."""
    calls = []

    def fake_run(args, capture_output=False, text=False):
        calls.append(args)
        return _put_success_result()

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/local/bin/gh")

    with pytest.raises(ValueError, match="Invalid subject name"):
        write_note("owner/repo", "work/../admin", "note text")

    assert calls == [], "No subprocess calls should be made for invalid subjects"


def test_read_notes_rejects_traversal_subject(monkeypatch):
    """read_notes raises ValueError before making any API calls for invalid subjects."""
    calls = []

    def fake_run(args, capture_output=False, text=False):
        calls.append(args)
        return _make_result(returncode=0, stdout="{}")

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/local/bin/gh")

    with pytest.raises(ValueError, match="Invalid subject name"):
        read_notes("owner/repo", ["../../etc/passwd", "valid"])

    assert calls == [], "No subprocess calls should be made for invalid subjects"
