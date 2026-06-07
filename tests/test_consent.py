"""The first-run consent gate: the user must accept the no-warranty, no-liability terms."""

from __future__ import annotations

from pathlib import Path

import pytest

from climon import consent


def test_first_run_shows_three_warnings_and_requires_agreement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert not consent.has_accepted()
    shown: list[str] = []
    accepted = consent.require_acceptance(read=lambda _prompt: "agree", write=shown.append)
    assert accepted
    assert consent.has_accepted()  # remembered for next time
    text = "\n".join(shown)
    assert "WARNING 1 of 3" in text
    assert "WARNING 2 of 3" in text
    assert "WARNING 3 of 3" in text
    assert "no liability" in text.lower()
    assert "at your own risk" in text.lower()


def test_declining_aborts_and_is_not_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    accepted = consent.require_acceptance(read=lambda _prompt: "no thanks", write=lambda _t: None)
    assert not accepted
    assert not consent.has_accepted()


def test_no_input_aborts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    def _eof(_prompt: str) -> str:
        raise EOFError

    assert not consent.require_acceptance(read=_eof, write=lambda _t: None)


def test_acceptance_is_not_asked_again(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    consent.record_acceptance()
    asked: list[str] = []

    def _record(prompt: str) -> str:
        asked.append(prompt)
        return "anything"

    assert consent.require_acceptance(read=_record, write=lambda _t: None)
    assert asked == []  # already accepted, so never prompted


def test_new_terms_version_asks_again(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    consent.record_acceptance()
    assert consent.has_accepted()
    monkeypatch.setattr(consent, "ACCEPTANCE_VERSION", "2")
    assert not consent.has_accepted()  # the old marker no longer matches
