"""Tests for scripts.document.remove_blank_lines."""

import pytest

from scripts.document.remove_blank_lines import BlankLineCollapser


@pytest.fixture()
def collapser() -> BlankLineCollapser:
    return BlankLineCollapser()


def test_collapses_multiple_blanks(collapser: BlankLineCollapser) -> None:
    content = "a\n\n\n\nb\n"
    result = collapser.process(content)
    assert "\n\n\n" not in result
    assert "a" in result
    assert "b" in result


def test_keeps_single_blank_line(collapser: BlankLineCollapser) -> None:
    content = "a\n\nb\n"
    result = collapser.process(content)
    assert "\n\n" in result


def test_strips_leading_blank_lines(collapser: BlankLineCollapser) -> None:
    content = "\n\ntext here\n"
    result = collapser.process(content)
    assert result.startswith("text")


def test_strips_trailing_blank_lines(collapser: BlankLineCollapser) -> None:
    content = "text here\n\n\n"
    result = collapser.process(content)
    assert result.endswith("text here\n")


def test_trailing_newline_always_present(collapser: BlankLineCollapser) -> None:
    content = "just text"
    result = collapser.process(content)
    assert result.endswith("\n")


def test_empty_content(collapser: BlankLineCollapser) -> None:
    result = collapser.process("")
    assert result == "\n"
