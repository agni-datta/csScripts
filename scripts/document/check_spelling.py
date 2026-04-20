#!/usr/bin/env python3
"""Check LaTeX source files for spelling errors.

Two complementary backends are supported and tried in order:

1. **aspell** (preferred when installed) – runs the system ``aspell`` spell
   checker in TeX mode, which understands LaTeX commands and skips macro
   names.  Results are grouped by word and sorted by frequency.

2. **pyspellchecker** (automatic fallback) – a pure-Python spell checker
   that requires no external binary.  It strips LaTeX commands with a simple
   regex before analysing plain text.

Usage::

    # Check a single file
    cs-check-spelling paper.tex

    # Check all .tex files under a directory
    cs-check-spelling src/

    # Force pyspellchecker even when aspell is available
    cs-check-spelling --backend pyspellchecker paper.tex

Exit status is 0 when no misspelled words are found, 1 otherwise.

Dependencies:
    aspell (system package, optional)  – ``brew install aspell`` / ``sudo apt install aspell``
    pyspellchecker >= 0.7 (optional)   – ``pip install pyspellchecker``

Example::

    $ cs-check-spelling thesis/
    thesis/chapter1.tex:
      recieve: 3
      teh: 1
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Iterator

try:
    from spellchecker import SpellChecker as _SpellChecker

    _PYSPELLCHECKER_AVAILABLE = True
except ImportError:
    _PYSPELLCHECKER_AVAILABLE = False

_LATEX_CMD_RE: re.Pattern[str] = re.compile(
    r"\\[a-zA-Z]+\*?\s*(?:\[[^\]]*\])*(?:\{[^}]*\})*"
)
_COMMENT_RE: re.Pattern[str] = re.compile(r"(?<!\\)%.*$", re.MULTILINE)


class _AspellBackend:
    """Spell-check a LaTeX file using the ``aspell`` CLI tool.

    Runs ``aspell --mode=tex list`` on the file content so that LaTeX macros
    are automatically ignored by aspell's TeX mode.

    Raises:
        RuntimeError: If ``aspell`` is not found on ``$PATH``.
    """

    def check_file(self, path: Path) -> Counter[str]:
        """Return a frequency counter of misspelled words in *path*.

        Args:
            path: Path to the LaTeX source file.

        Returns:
            :class:`collections.Counter` mapping each misspelled word to the
            number of times it appears.

        Raises:
            RuntimeError: If the ``aspell`` binary is not installed.
            OSError: If *path* cannot be read.
        """
        content = path.read_text(encoding="utf-8", errors="replace")
        result = subprocess.run(
            ["aspell", "--mode=tex", "list"],
            input=content,
            capture_output=True,
            text=True,
            check=False,
        )
        return Counter(w for w in result.stdout.splitlines() if w)


class _PySpellCheckerBackend:
    """Spell-check a LaTeX file using ``pyspellchecker`` (pure Python).

    LaTeX comments and command sequences are stripped from the source before
    analysis.  This backend requires no external binary.

    Attributes:
        _checker: Underlying :class:`spellchecker.SpellChecker` instance.

    Raises:
        RuntimeError: If ``pyspellchecker`` is not installed.
    """

    def __init__(self) -> None:
        if not _PYSPELLCHECKER_AVAILABLE:
            raise RuntimeError(
                "pyspellchecker is not installed.  "
                "Install it with: pip install pyspellchecker"
            )
        self._checker = _SpellChecker(language="en")

    def check_file(self, path: Path) -> Counter[str]:
        """Return a frequency counter of misspelled words in *path*.

        Args:
            path: Path to the LaTeX source file.

        Returns:
            :class:`collections.Counter` mapping each misspelled word to the
            number of times it appears.

        Raises:
            OSError: If *path* cannot be read.
        """
        content = path.read_text(encoding="utf-8", errors="replace")
        content = _COMMENT_RE.sub("", content)
        content = _LATEX_CMD_RE.sub(" ", content)
        tokens = re.findall(r"[a-zA-Z]+", content)
        misspelled = self._checker.unknown(tokens)
        return Counter(t for t in tokens if t.lower() in misspelled)


class SpellingChecker:
    """High-level spell checker for LaTeX files.

    Selects the ``aspell`` backend when available (and not overridden), or
    falls back to ``pyspellchecker``.  If neither is available, raises
    :class:`RuntimeError`.

    Attributes:
        _backend: Active backend (``_AspellBackend`` or ``_PySpellCheckerBackend``).
        backend_name: Human-readable name of the selected backend.

    Example::

        checker = SpellingChecker()
        counts = checker.check_file(Path("paper.tex"))
        for word, n in counts.most_common():
            print(f"  {word}: {n}")
    """

    def __init__(self, force_backend: str | None = None) -> None:
        """Initialise the checker, selecting the appropriate backend.

        Args:
            force_backend: One of ``"aspell"`` or ``"pyspellchecker"``.  When
                ``None`` (default) the best available backend is chosen
                automatically.

        Raises:
            ValueError: If *force_backend* is not a recognised name.
            RuntimeError: If the requested or only available backend is missing.
        """
        if force_backend == "aspell":
            self._backend: _AspellBackend | _PySpellCheckerBackend = _AspellBackend()
            self.backend_name = "aspell"
        elif force_backend == "pyspellchecker":
            self._backend = _PySpellCheckerBackend()
            self.backend_name = "pyspellchecker"
        elif force_backend is not None:
            raise ValueError(f"Unknown backend: {force_backend!r}")
        elif shutil.which("aspell"):
            self._backend = _AspellBackend()
            self.backend_name = "aspell"
        elif _PYSPELLCHECKER_AVAILABLE:
            self._backend = _PySpellCheckerBackend()
            self.backend_name = "pyspellchecker"
        else:
            raise RuntimeError(
                "No spell-checking backend found.\n"
                "Install aspell:          brew install aspell  |  sudo apt install aspell\n"
                "Or install pyspellchecker: pip install pyspellchecker"
            )

    def check_file(self, path: Path) -> Counter[str]:
        """Spell-check a single LaTeX file.

        Args:
            path: Path to the ``.tex`` file to check.

        Returns:
            :class:`collections.Counter` mapping misspelled words to their
            frequency in the file.

        Raises:
            OSError: If *path* cannot be read.
        """
        return self._backend.check_file(path)


def _iter_tex_files(paths: list[str]) -> Iterator[Path]:
    """Expand CLI paths into individual ``.tex`` file paths.

    Directories are recursed with :func:`pathlib.Path.rglob`; plain files
    are yielded directly.  Unrecognised paths emit a warning and are skipped.

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
    """Parse command-line arguments and run the spell check.

    Reports are grouped by file.  Within each file, misspelled words are
    listed from most to least frequent.  Exits with code 1 when any issues
    are found.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Check LaTeX files for spelling errors.\n\n"
            "Uses aspell (if installed) or pyspellchecker as a fallback."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="+",
        metavar="PATH",
        help="One or more .tex files or directories to check.",
    )
    parser.add_argument(
        "--backend",
        choices=["aspell", "pyspellchecker"],
        default=None,
        help="Force a specific spell-checking backend.",
    )
    args = parser.parse_args()

    try:
        checker = SpellingChecker(force_backend=args.backend)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)

    print(f"Using backend: {checker.backend_name}", file=sys.stderr)
    found_any = False

    for tex_file in _iter_tex_files(args.paths):
        counts = checker.check_file(tex_file)
        if counts:
            found_any = True
            print(f"\n{tex_file}:")
            for word, count in counts.most_common():
                print(f"  {word}: {count}")

    sys.exit(1 if found_any else 0)


if __name__ == "__main__":
    main()
