#!/usr/bin/env python3
"""Remove LaTeX ``%`` comments from ``.tex`` source files.

Strips everything from the first unescaped ``%`` character to the end of
each line.  Lines that consist entirely of a comment (no preceding code) are
dropped completely rather than left as blank lines.  Escaped percent signs
(``\\%``) and double-backslash sequences (``\\\\%``) are correctly handled
so that they are never mistakenly treated as comment markers.

Usage::

    python -m scripts.document.remove_comments paper.tex

    python -m scripts.document.remove_comments intro.tex chapter1.tex

Exit status is 0 on success, non-zero if any file could not be processed.

Example::

    $ python -m scripts.document.remove_comments paper.tex
    processed: paper.tex
"""

import argparse
from pathlib import Path
import re
import sys

_COMMENT_RE: re.Pattern[str] = re.compile(r"(?<!\\)(?:\\\\)*%")


class CommentRemover:
    """Strips LaTeX % comments from source files.

    Handles escaped percent signs (\\%) correctly and removes lines that
    are comment-only (no code before the %).
    """

    def process(self, content: str) -> str:
        """Remove LaTeX comments from content.

        Args:
            content: Full LaTeX file text.

        Returns:
            Content with comment text stripped, trailing newline preserved.
        """
        result: list[str] = []
        for line in content.splitlines():
            match = _COMMENT_RE.search(line)
            if match:
                code_part = line[: match.start()]
                if code_part.strip():
                    result.append(code_part.rstrip())
            else:
                result.append(line)
        return "\n".join(result) + "\n"


def main() -> None:
    """Entry point: remove comments from one or more LaTeX files."""
    parser = argparse.ArgumentParser(
        description="Remove LaTeX % comments from .tex files (in-place)."
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".tex file(s) to process.",
    )
    args = parser.parse_args()

    remover = CommentRemover()
    errors = 0

    for raw in args.files:
        path = Path(raw)
        if not path.is_file():
            print(f"error: {raw} is not a file", file=sys.stderr)
            errors += 1
            continue
        content = path.read_text(encoding="utf-8")
        path.write_text(remover.process(content), encoding="utf-8")
        print(f"processed: {path}")

    sys.exit(errors)


if __name__ == "__main__":
    main()
