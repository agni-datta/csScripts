"""Tests for scripts.document.join_lines."""

import pytest

from scripts.document.join_lines import LineJoiner


@pytest.fixture()
def joiner() -> LineJoiner:
    return LineJoiner()


def test_joins_consecutive_text_lines(joiner: LineJoiner) -> None:
    content = "This is a long\nsentence that wraps.\n"
    result = joiner.process(content)
    assert "This is a long sentence that wraps." in result
    assert result.count("\n") == 1


def test_does_not_join_blank_line_separated_paragraphs(joiner: LineJoiner) -> None:
    content = "Paragraph one.\n\nParagraph two.\n"
    result = joiner.process(content)
    assert "Paragraph one." in result
    assert "Paragraph two." in result
    assert "\n\n" in result


def test_collapses_multiple_blank_lines(joiner: LineJoiner) -> None:
    content = "Line one.\n\n\n\nLine two.\n"
    result = joiner.process(content)
    assert result.count("\n\n") == 1
    assert "\n\n\n" not in result


def test_does_not_join_item_lines(joiner: LineJoiner) -> None:
    content = "Text before\n\\item first item\n\\item second item\n"
    result = joiner.process(content)
    assert "\\item first item" in result
    assert "\\item second item" in result


def test_preserves_comment_only_lines_separately(joiner: LineJoiner) -> None:
    content = "Some text.\n% a comment\nMore text.\n"
    result = joiner.process(content)
    assert "% a comment" in result
