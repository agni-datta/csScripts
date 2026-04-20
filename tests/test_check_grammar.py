"""Tests for scripts.document.check_grammar."""

from pathlib import Path

import pytest

from scripts.document.check_grammar import _RegexChecker
from scripts.document.check_grammar import GrammarChecker
from scripts.document.check_grammar import GrammarIssue


@pytest.fixture()
def regex_checker() -> GrammarChecker:
    """GrammarChecker forced onto the regex fallback backend (no Java required)."""
    checker = GrammarChecker.__new__(GrammarChecker)
    checker._disabled = set()
    checker._backend = _RegexChecker()
    return checker


@pytest.fixture()
def tex_file(tmp_path: Path) -> Path:
    return tmp_path / "sample.tex"


def test_detects_teh_typo(regex_checker: GrammarChecker, tex_file: Path) -> None:
    tex_file.write_text("This is teh end.\n", encoding="utf-8")
    hits = list(regex_checker.check_file(tex_file))
    assert any("teh" in issue.message.lower() for issue in hits)


def test_detects_recieve_typo(regex_checker: GrammarChecker, tex_file: Path) -> None:
    tex_file.write_text("We will recieve the data.\n", encoding="utf-8")
    hits = list(regex_checker.check_file(tex_file))
    assert any("recieve" in issue.message.lower() for issue in hits)


def test_skips_comment_lines(regex_checker: GrammarChecker, tex_file: Path) -> None:
    tex_file.write_text("% teh is a typo\n", encoding="utf-8")
    hits = list(regex_checker.check_file(tex_file))
    assert hits == []


def test_detects_eg_without_comma(
    regex_checker: GrammarChecker, tex_file: Path
) -> None:
    tex_file.write_text("e.g. for example\n", encoding="utf-8")
    hits = list(regex_checker.check_file(tex_file))
    assert any("e.g." in issue.message.lower() for issue in hits)


def test_clean_sentence_no_hits(regex_checker: GrammarChecker, tex_file: Path) -> None:
    tex_file.write_text("The results are shown in the table.\n", encoding="utf-8")
    hits = list(regex_checker.check_file(tex_file))
    assert hits == []


def test_grammar_issue_is_dataclass(
    regex_checker: GrammarChecker, tex_file: Path
) -> None:
    tex_file.write_text("This is teh end.\n", encoding="utf-8")
    hits = list(regex_checker.check_file(tex_file))
    assert hits
    issue = hits[0]
    assert isinstance(issue, GrammarIssue)
    assert isinstance(issue.file, Path)
    assert isinstance(issue.line, int)
    assert isinstance(issue.rule_id, str)
    assert isinstance(issue.message, str)
    assert isinstance(issue.suggestions, tuple)
    assert isinstance(issue.context, str)
