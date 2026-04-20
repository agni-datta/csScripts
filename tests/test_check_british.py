"""Tests for scripts.document.check_british."""

from pathlib import Path

import pytest

from scripts.document.check_british import BritishSpellingChecker


@pytest.fixture()
def checker() -> BritishSpellingChecker:
    return BritishSpellingChecker()


@pytest.fixture()
def tex_file(tmp_path: Path) -> Path:
    return tmp_path / "sample.tex"


def test_detects_british_colour(
    checker: BritishSpellingChecker, tex_file: Path
) -> None:
    tex_file.write_text("The colour of the sky is blue.\n", encoding="utf-8")
    hits = list(checker.check_file(tex_file))
    words = [w for _, w in hits]
    assert "colour" in words


def test_ignores_false_positive_our(
    checker: BritishSpellingChecker, tex_file: Path
) -> None:
    tex_file.write_text("Your course is important.\n", encoding="utf-8")
    hits = list(checker.check_file(tex_file))
    words = [w.lower() for _, w in hits]
    assert "your" not in words
    assert "course" not in words


def test_detects_ise_suffix(checker: BritishSpellingChecker, tex_file: Path) -> None:
    tex_file.write_text("We should organise the data.\n", encoding="utf-8")
    hits = list(checker.check_file(tex_file))
    words = [w.lower() for _, w in hits]
    assert "organise" in words


def test_clean_file_returns_nothing(
    checker: BritishSpellingChecker, tex_file: Path
) -> None:
    tex_file.write_text("The data are organized correctly.\n", encoding="utf-8")
    hits = list(checker.check_file(tex_file))
    assert hits == []


def test_line_numbers_reported(checker: BritishSpellingChecker, tex_file: Path) -> None:
    tex_file.write_text("first line\ncolour here\nthird line\n", encoding="utf-8")
    hits = list(checker.check_file(tex_file))
    linenos = [ln for ln, _ in hits]
    assert 2 in linenos
