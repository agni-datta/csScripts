#!/usr/bin/env python3
"""Join consecutive wrapped text lines in LaTeX source files.

Many LaTeX authors hard-wrap prose at 80 columns for readability in editors
that lack soft-wrapping.  This tool re-joins those wrapped lines so that
each logical sentence or paragraph sits on a single line, which makes
``git diff`` output easier to read and simplifies subsequent text processing.

The joiner is LaTeX-aware: it preserves blank lines (paragraph breaks),
comment-only lines, structural commands (``\\begin``, ``\\end``, ``\\item``,
etc.), and escape sequences such as ``\\\\`` (forced line break).

Usage::

    join-lines paper.tex

    join-lines intro.tex methods.tex discussion.tex

Exit status is 0 on success, non-zero if any file could not be processed.

Example::

    $ join-lines chapter.tex
    processed: chapter.tex
"""

import argparse
from pathlib import Path
import sys

_TEXTUAL_COMMANDS: frozenset[str] = frozenset(
    {
        r"\item",
        r"\textit",
        r"\textbf",
        r"\cref",
        r"\cite",
        r"\ref",
        r"\label",
    }
)


class LineJoiner:
    """Joins consecutive text lines in a LaTeX document.

    Collapses wrapped paragraph text into single lines while preserving
    LaTeX structure, blank lines, and non-prose content.
    """

    def _is_text_line(self, line: str) -> bool:
        """Return True if the line contains joinable prose content.

        Args:
            line: A single line of LaTeX source.

        Returns:
            True if the line should participate in joining.
        """
        stripped = line.strip()
        if not stripped or stripped.startswith("%"):
            return False
        if stripped.startswith("\\"):
            return any(stripped.startswith(cmd) for cmd in _TEXTUAL_COMMANDS)
        return stripped not in {"}", "]", "{", "["}

    def _should_join(self, prev: str, nxt: str) -> bool:
        """Return True if two adjacent lines should be joined.

        Args:
            prev: The previous line.
            nxt: The next line.

        Returns:
            True if the lines should be concatenated.
        """
        if not self._is_text_line(prev) or not self._is_text_line(nxt):
            return False
        prev_s = prev.strip()
        nxt_s = nxt.strip()
        if nxt_s.startswith(r"\item"):
            return False
        if prev_s.endswith("\\\\") or prev_s.endswith("%"):
            return False
        return True

    def _join_block(self, block: list[str]) -> str:
        """Merge a block of lines into one line.

        Args:
            block: List of consecutive lines forming one logical line.

        Returns:
            A single joined line with trailing newline.
        """
        if len(block) == 1:
            return block[0]
        parts = [block[0].rstrip()] + [ln.strip() for ln in block[1:]]
        return " ".join(parts) + "\n"

    def process(self, content: str) -> str:
        """Join lines and collapse consecutive blank lines.

        Args:
            content: Full file content as a string.

        Returns:
            Processed content with lines joined and blanks collapsed.
        """
        lines = content.splitlines(keepends=True)
        joined: list[str] = []
        block: list[str] = []

        for line in lines:
            if not block:
                block = [line]
            elif self._should_join(block[-1], line):
                block.append(line)
            else:
                joined.append(self._join_block(block))
                block = [line]
        if block:
            joined.append(self._join_block(block))

        result: list[str] = []
        prev_blank = False
        for line in joined:
            is_blank = not line.strip()
            if is_blank and prev_blank:
                continue
            result.append(line)
            prev_blank = is_blank

        return "".join(result)


def main() -> None:
    """Entry point: join lines in one or more LaTeX files."""
    parser = argparse.ArgumentParser(
        description="Join wrapped text lines in LaTeX files."
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".tex file(s) to process (in-place).",
    )
    args = parser.parse_args()

    joiner = LineJoiner()
    errors = 0

    for raw in args.files:
        path = Path(raw)
        if not path.is_file():
            print(f"error: {raw} is not a file", file=sys.stderr)
            errors += 1
            continue
        content = path.read_text(encoding="utf-8")
        path.write_text(joiner.process(content), encoding="utf-8")
        print(f"processed: {path}")

    sys.exit(errors)


if __name__ == "__main__":
    main()
