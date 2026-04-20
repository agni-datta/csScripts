#!/usr/bin/env python3
"""Collapse multiple consecutive blank lines to a single blank line.

LaTeX source files (and plain text files in general) occasionally accumulate
several consecutive blank lines through editing.  This tool normalises them:
every run of two or more blank lines is replaced by exactly one blank line,
and leading or trailing blank lines are removed entirely.

Usage::

    python -m scripts.document.remove_blank_lines paper.tex

    python -m scripts.document.remove_blank_lines intro.tex chapter1.tex

Exit status is 0 on success, non-zero if any file could not be processed.

Example::

    $ python -m scripts.document.remove_blank_lines paper.tex
    processed: paper.tex
"""

import argparse
from pathlib import Path
import sys


class BlankLineCollapser:
    """Collapses runs of blank lines to exactly one blank line.

    Also strips leading and trailing blank lines from the file.
    """

    def process(self, content: str) -> str:
        """Collapse consecutive blank lines in content.

        Args:
            content: Full file text.

        Returns:
            Cleaned text with at most one consecutive blank line,
            trailing newline preserved.
        """
        lines = content.splitlines()
        result: list[str] = []
        last_blank = False

        for line in lines:
            blank = not line.strip()
            if blank:
                if not last_blank:
                    result.append("")
                last_blank = True
            else:
                result.append(line)
                last_blank = False

        while result and not result[0]:
            result.pop(0)
        while result and not result[-1]:
            result.pop()

        return "\n".join(result) + "\n"


def main() -> None:
    """Entry point: remove excess blank lines from one or more files."""
    parser = argparse.ArgumentParser(
        description="Collapse multiple blank lines to a single blank line."
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="File(s) to process (in-place).",
    )
    args = parser.parse_args()

    collapser = BlankLineCollapser()
    errors = 0

    for raw in args.files:
        path = Path(raw)
        if not path.is_file():
            print(f"error: {raw} is not a file", file=sys.stderr)
            errors += 1
            continue
        content = path.read_text(encoding="utf-8")
        path.write_text(collapser.process(content), encoding="utf-8")
        print(f"processed: {path}")

    sys.exit(errors)


if __name__ == "__main__":
    main()
