"""Tests for scripts.document.check_spelling."""

from collections import Counter
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from scripts.document.check_spelling import SpellingChecker


@pytest.fixture()
def checker() -> SpellingChecker:
    return SpellingChecker(force_backend="aspell")


@pytest.fixture()
def tex_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.tex"
    p.write_text("Hello world\n", encoding="utf-8")
    return p


def test_returns_counter(checker: SpellingChecker, tex_file: Path) -> None:
    with patch("scripts.document.check_spelling.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="mispelled\nmispelled\ntypo\n")
        result = checker.check_file(tex_file)
    assert isinstance(result, Counter)
    assert result["mispelled"] == 2
    assert result["typo"] == 1


def test_empty_output_returns_empty_counter(
    checker: SpellingChecker, tex_file: Path
) -> None:
    with patch("scripts.document.check_spelling.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="")
        result = checker.check_file(tex_file)
    assert len(result) == 0


def test_aspell_called_with_tex_mode(checker: SpellingChecker, tex_file: Path) -> None:
    with patch("scripts.document.check_spelling.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="")
        checker.check_file(tex_file)
    call_args = mock_run.call_args
    cmd = call_args[0][0]
    assert "--mode=tex" in cmd
    assert "list" in cmd
