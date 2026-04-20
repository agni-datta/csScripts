"""Tests for scripts.document.remove_comments."""

import pytest

from scripts.document.remove_comments import CommentRemover


@pytest.fixture()
def remover() -> CommentRemover:
    return CommentRemover()


def test_removes_full_comment_line(remover: CommentRemover) -> None:
    content = "% This is a comment\nsome code\n"
    result = remover.process(content)
    assert "% This is a comment" not in result
    assert "some code" in result


def test_removes_inline_comment(remover: CommentRemover) -> None:
    content = r"some code % inline comment" + "\n"
    result = remover.process(content)
    assert "inline comment" not in result
    assert "some code" in result


def test_preserves_escaped_percent(remover: CommentRemover) -> None:
    content = r"100\% complete" + "\n"
    result = remover.process(content)
    assert r"100\%" in result


def test_trailing_newline_preserved(remover: CommentRemover) -> None:
    content = "code\n"
    result = remover.process(content)
    assert result.endswith("\n")


def test_empty_input(remover: CommentRemover) -> None:
    result = remover.process("")
    assert result == "\n"


def test_only_comments_gives_empty_body(remover: CommentRemover) -> None:
    content = "% comment one\n% comment two\n"
    result = remover.process(content)
    assert result.strip() == ""
