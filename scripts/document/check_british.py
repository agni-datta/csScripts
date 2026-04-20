#!/usr/bin/env python3
"""Check LaTeX source files for British English spelling variants.

Uses the ``pyspellchecker`` English (American) dictionary to detect words that
are valid British spellings but absent from the American English word list
(e.g. *colour*, *organise*, *realise*, *centre*).  Unlike a purely
regex-based approach this avoids maintaining a hard-coded false-positive
list: if ``pyspellchecker`` knows a word as correct American English it is
silently passed through.

Usage::

    # Check a single file
    cs-check-british paper.tex

    # Check every .tex file beneath a directory
    cs-check-british src/

    # Mix files and directories
    cs-check-british intro.tex src/ appendix.tex

Exit status is 0 when no issues are found, 1 otherwise.

Dependencies:
    pyspellchecker >= 0.7  (``pip install pyspellchecker``)

Example::

    $ cs-check-british thesis/
    thesis/chapter1.tex:42: honour
    thesis/chapter2.tex:17: organise
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from typing import Iterator

try:
    from spellchecker import SpellChecker as _SpellChecker

    _SPELLCHECKER_AVAILABLE = True
except ImportError:
    _SPELLCHECKER_AVAILABLE = False

_BRITISH_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\b\w+our\b",  # colour, honour, behaviour …
        r"\b\w+ise\b",  # organise, realise, normalise …
        r"\b\w+isation\b",  # organisation, realisation …
        r"\b\w+yse\b",  # analyse, catalyse …
        r"\b\w+ogue\b",  # catalogue, dialogue …
        r"\b\w+re\b",  # centre, theatre, litre …
        r"\b\w+ence\b",  # offence, defence, licence …
    )
)

_STATIC_ALLOWLIST: frozenset[str] = frozenset(
    {
        "our",
        "your",
        "four",
        "hour",
        "tour",
        "course",
        "source",
        "resource",
        "because",
        "house",
        "mouse",
        "use",
        "cause",
        "clause",
        "pause",
        "praise",
        "rise",
        "wise",
        "more",
        "core",
        "store",
        "before",
        "here",
        "there",
        "where",
        "were",
        "are",
        "figure",
        "picture",
        "nature",
        "future",
        "measure",
        "pressure",
        "treasure",
        "pleasure",
        "secure",
        "ensure",
        "require",
        "fire",
        "hire",
        "wire",
        "tire",
        "prepare",
        "compare",
        "share",
        "care",
        "dare",
        "square",
        "software",
        "hardware",
        "firmware",
        "middleware",
        "malware",
        "league",
        "unique",
        "antique",
        "technique",
        "critique",
        "defence",
        "licence",
        "offence",
        "presence",
        "audience",
        "patience",
        "sentence",
        "science",
        "sequence",
        "silence",
        "violence",
        "experience",
        "conference",
        "difference",
        "reference",
        "preference",
        "inference",
        "evidence",
        "residence",
        "prevalence",
        "consequence",
        "intelligence",
    }
)


class _AmericanDictionary:
    """Wrapper around pyspellchecker's American English word frequency list.

    Falls back to :data:`_STATIC_ALLOWLIST` when ``pyspellchecker`` is not
    installed, logging a one-time warning.

    Attributes:
        _checker: Underlying :class:`spellchecker.SpellChecker` instance, or
            ``None`` when the package is unavailable.
    """

    def __init__(self) -> None:
        if _SPELLCHECKER_AVAILABLE:
            self._checker: object | None = _SpellChecker(language="en")
        else:
            self._checker = None
            print(
                "warning: pyspellchecker not installed – "
                "falling back to static allowlist (less accurate).\n"
                "  Install with: pip install pyspellchecker",
                file=sys.stderr,
            )

    def is_american_english(self, word: str) -> bool:
        """Return ``True`` if *word* is a known American English word.

        Args:
            word: A single lower-cased token.

        Returns:
            ``True`` when the word is in the American English dictionary or
            in the static fallback allowlist.
        """
        if self._checker is not None:
            return word not in self._checker.unknown([word])
        return word in _STATIC_ALLOWLIST


class BritishSpellingChecker:
    """Detect British English spelling variants in LaTeX source files.

    The checker scans each line of a ``.tex`` file for tokens matching
    characteristic British spelling suffixes, then cross-references each
    candidate against an American English dictionary.  Words present in the
    American dictionary are considered legitimate and are silently skipped.

    Attributes:
        _dictionary: American English dictionary used to filter false positives.

    Example::

        checker = BritishSpellingChecker()
        for lineno, word in checker.check_file(Path("paper.tex")):
            print(f"line {lineno}: {word}")
    """

    def __init__(self) -> None:
        self._dictionary = _AmericanDictionary()

    def check_file(self, path: Path) -> Iterator[tuple[int, str]]:
        """Scan a file and yield ``(line_number, word)`` for British spellings.

        Lines that are LaTeX comments (stripped content starts with ``%``) are
        skipped entirely so that comment-only explanations do not generate
        false positives.

        Args:
            path: Path to the ``.tex`` file to inspect.

        Yields:
            A ``(lineno, word)`` tuple where *lineno* is 1-based and *word*
            is the matched token as it appears in the source.

        Raises:
            OSError: If *path* cannot be read.
        """
        content = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(content.splitlines(), start=1):
            if line.lstrip().startswith("%"):
                continue
            for pattern in _BRITISH_PATTERNS:
                for match in pattern.finditer(line):
                    word = match.group(0)
                    if not self._dictionary.is_american_english(word.lower()):
                        yield lineno, word


def _iter_tex_files(paths: list[str]) -> Iterator[Path]:
    """Expand CLI paths into individual ``.tex`` file paths.

    Directories are recursed with :func:`pathlib.Path.rglob`; plain files
    are yielded directly.  Paths that are neither an existing file nor a
    directory produce a warning on ``stderr`` and are skipped.

    Args:
        paths: Raw path strings from the command line.

    Yields:
        Resolved :class:`~pathlib.Path` objects for each ``.tex`` file found.
    """
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            yield from sorted(p.rglob("*.tex"))
        elif p.is_file() and p.suffix == ".tex":
            yield p
        else:
            print(
                f"warning: skipping {raw!r} (not a .tex file or directory)",
                file=sys.stderr,
            )


def main() -> None:
    """Parse command-line arguments and run the British spelling check.

    Prints results in ``file:line: word`` format (compatible with most
    editor *quickfix* lists).  Exits with code 1 when any issues are found.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Detect British English spelling variants in LaTeX source files.\n\n"
            "Uses the American English dictionary from pyspellchecker so that "
            "words already valid in American English are never flagged."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="+",
        metavar="PATH",
        help="One or more .tex files or directories to check.",
    )
    args = parser.parse_args()

    checker = BritishSpellingChecker()
    found_any = False

    for tex_file in _iter_tex_files(args.paths):
        for lineno, word in checker.check_file(tex_file):
            print(f"{tex_file}:{lineno}: {word}")
            found_any = True

    sys.exit(1 if found_any else 0)


if __name__ == "__main__":
    main()
