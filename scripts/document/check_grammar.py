#!/usr/bin/env python3
"""Check LaTeX source files for grammar errors using LanguageTool.

This script strips LaTeX markup from each file with ``pylatexenc`` and then
passes the resulting plain text to a local ``LanguageTool`` server (via the
``language_tool_python`` package) for grammar analysis.  Using an NLP-backed
grammar engine avoids the fragility of hand-rolled regular expressions and
covers a far wider range of issues (article agreement, punctuation, style,
redundancy, and more).

Usage::

    # Check a single file
    cs-check-grammar paper.tex

    # Check every .tex file beneath a directory
    cs-check-grammar src/

    # Pass extra LanguageTool rule IDs to disable (comma-separated)
    cs-check-grammar --disable WHITESPACE_RULE,EN_QUOTES paper.tex

Exit status is 0 when no issues are found, 1 otherwise.

Dependencies:
    language_tool_python >= 2.7  (``pip install language-tool-python``)
    pylatexenc >= 2.10           (``pip install pylatexenc``)
    Java 8+ runtime (required by the local LanguageTool server)

Example::

    $ cs-check-grammar thesis/chapter1.tex
    thesis/chapter1.tex – [EN_A_VS_AN] offset 34 | Use "an" instead of "a".
        Suggestions: an
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Iterator, Sequence

try:
    import language_tool_python as _ltp

    _LTP_AVAILABLE = True
except ImportError:
    _LTP_AVAILABLE = False

try:
    from pylatexenc.latex2text import LatexNodes2Text as _LatexNodes2Text

    _PYLATEXENC_AVAILABLE = True
except ImportError:
    _PYLATEXENC_AVAILABLE = False

import re

_FALLBACK_RULES: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(pattern, re.IGNORECASE), description)
    for pattern, description in (
        (r"\b(a)\s+[aeiou]\w+", "possible a/an error"),
        (r"\b(an)\s+[^aeiou\s]\w+", "possible an/a error"),
        (r"\bit\'s\b\s+(?:own|value|state|purpose|size|length)", "it's vs its"),
        (r"\btheir\s+(?:is|are|was|were)\b", "their vs there"),
        (r"\bto\s+(?:much|many)\b", "to vs too"),
        (r"\bcan\s+not\b", "can not → cannot"),
        (r"\be\.g\.\s+[^,]", "e.g. without comma"),
        (r"\bi\.e\.\s+[^,]", "i.e. without comma"),
        (r"\bloose\b", "loose vs lose (check context)"),
        (r"\bteh\b", "teh → the"),
        (r"\brecieve\b", "recieve → receive"),
        (r"\bseperate\b", "seperate → separate"),
        (r"\boccured\b", "occured → occurred"),
        (r"\buntill\b", "untill → until"),
    )
)


@dataclass(frozen=True)
class GrammarIssue:
    """A single grammar issue found in a source file.

    Attributes:
        file: Path to the source file.
        line: 1-based line number where the issue starts (approximate when
            using the LanguageTool backend because stripping LaTeX markup
            shifts offsets).
        rule_id: Short identifier for the triggered grammar rule.
        message: Human-readable description of the problem.
        suggestions: Replacement suggestions offered by the checker.
        context: Snippet of text surrounding the issue.
    """

    file: Path
    line: int
    rule_id: str
    message: str
    suggestions: tuple[str, ...]
    context: str


def _strip_latex(content: str) -> str:
    """Convert LaTeX markup to plain text.

    Uses ``pylatexenc`` when available for accurate macro expansion.  Falls
    back to stripping backslash commands with a simple regex when the package
    is absent.

    Args:
        content: Raw LaTeX source text.

    Returns:
        Plain text suitable for grammar analysis.
    """
    if _PYLATEXENC_AVAILABLE:
        try:
            return _LatexNodes2Text().latex_to_text(content)
        except Exception:
            pass  # fall through to regex fallback
    text = re.sub(r"%[^\n]*", "", content)
    text = re.sub(r"\\[a-zA-Z]+\*?\s*(\{[^}]*\})*", " ", text)
    return text


class _LanguageToolChecker:
    """Grammar checker backed by a local LanguageTool server.

    A single server process is started on construction and reused across
    all files.  Call :meth:`close` (or use as a context manager) to shut
    the server down cleanly.

    Attributes:
        _tool: Live :class:`language_tool_python.LanguageTool` instance.
        _disabled: Set of rule IDs explicitly disabled by the caller.

    Example::

        with _LanguageToolChecker(disabled={"WHITESPACE_RULE"}) as checker:
            issues = list(checker.check_text("Some text.", Path("f.tex")))
    """

    def __init__(self, disabled: set[str] | None = None) -> None:
        self._tool = _ltp.LanguageTool("en-US")
        self._disabled: set[str] = disabled or set()

    def __enter__(self) -> "_LanguageToolChecker":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Shut down the LanguageTool server process."""
        try:
            self._tool.close()
        except Exception:
            pass

    def check_text(self, plain_text: str, source_path: Path) -> Iterator[GrammarIssue]:
        """Run LanguageTool on *plain_text* and yield :class:`GrammarIssue` objects.

        Args:
            plain_text: Stripped (non-LaTeX) text to analyse.
            source_path: Original file path used for reporting.

        Yields:
            :class:`GrammarIssue` for every match not in the disabled set.
        """
        matches = self._tool.check(plain_text)
        lines = plain_text.splitlines()
        for match in matches:
            if match.ruleId in self._disabled:
                continue
            lineno = plain_text[: match.offset].count("\n") + 1
            ctx_line = lines[lineno - 1] if lineno <= len(lines) else ""
            yield GrammarIssue(
                file=source_path,
                line=lineno,
                rule_id=match.ruleId,
                message=match.message,
                suggestions=tuple(match.replacements[:5]),
                context=ctx_line.strip(),
            )


class _RegexChecker:
    """Fallback grammar checker using a fixed set of regex rules.

    This checker is used automatically when ``language_tool_python`` is not
    installed.  It covers a small number of common errors but lacks the
    linguistic depth of the LanguageTool backend.

    Attributes:
        _rules: Compiled ``(pattern, description)`` pairs applied line-by-line.
    """

    def __init__(self) -> None:
        self._rules = _FALLBACK_RULES

    def check_text(self, plain_text: str, source_path: Path) -> Iterator[GrammarIssue]:
        """Scan *plain_text* line-by-line using the fallback rule set.

        Lines beginning with ``%`` (LaTeX comments, if stripping failed) are
        skipped.

        Args:
            plain_text: Text to analyse (ideally already stripped of LaTeX).
            source_path: Original file path used for reporting.

        Yields:
            :class:`GrammarIssue` for each match found.
        """
        for lineno, line in enumerate(plain_text.splitlines(), start=1):
            if line.lstrip().startswith("%"):
                continue
            for pattern, desc in self._rules:
                if pattern.search(line):
                    yield GrammarIssue(
                        file=source_path,
                        line=lineno,
                        rule_id="REGEX_RULE",
                        message=desc,
                        suggestions=(),
                        context=line.strip(),
                    )


class GrammarChecker:
    """Orchestrates grammar checking of LaTeX source files.

    Selects the best available backend (LanguageTool or regex fallback) and
    applies it to each file.  LaTeX markup is stripped before analysis.

    Attributes:
        _backend: Active checker backend (LanguageTool or regex).
        _disabled: Rule IDs to suppress in LanguageTool mode.

    Example::

        checker = GrammarChecker(disabled={"WHITESPACE_RULE"})
        for issue in checker.check_file(Path("paper.tex")):
            print(issue)
        checker.close()
    """

    def __init__(self, disabled: Sequence[str] | None = None) -> None:
        self._disabled: set[str] = set(disabled) if disabled else set()
        if _LTP_AVAILABLE:
            self._backend: _LanguageToolChecker | _RegexChecker = _LanguageToolChecker(
                disabled=self._disabled
            )
        else:
            print(
                "warning: language_tool_python not installed – "
                "using limited regex fallback.\n"
                "  Install with: pip install language-tool-python\n"
                "  (Requires Java 8+ on your PATH.)",
                file=sys.stderr,
            )
            self._backend = _RegexChecker()

    def close(self) -> None:
        """Shut down any background LanguageTool server process."""
        if isinstance(self._backend, _LanguageToolChecker):
            self._backend.close()

    def __enter__(self) -> "GrammarChecker":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def check_file(self, path: Path) -> Iterator[GrammarIssue]:
        """Check a single LaTeX file for grammar issues.

        The file is read, LaTeX markup is stripped, and the result is passed
        to the active backend.

        Args:
            path: Path to the ``.tex`` file to check.

        Yields:
            :class:`GrammarIssue` objects for every problem found.

        Raises:
            OSError: If *path* cannot be read.
        """
        raw = path.read_text(encoding="utf-8", errors="replace")
        plain = _strip_latex(raw)
        yield from self._backend.check_text(plain, path)


def _iter_tex_files(paths: list[str]) -> Iterator[Path]:
    """Expand CLI paths into individual ``.tex`` file paths.

    Directories are recursed; plain ``.tex`` files are yielded directly.
    Anything else emits a warning on ``stderr`` and is skipped.

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
    """Parse command-line arguments and run the grammar check.

    Results are printed as ``file:line: [RULE_ID] message`` lines.  When
    suggestions are available they are shown on a following indented line.
    Exits with code 1 when any issues are found.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Check LaTeX files for grammar errors using LanguageTool.\n\n"
            "LaTeX markup is stripped before analysis.  When language_tool_python\n"
            "is not installed a simple regex fallback is used instead."
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
        "--disable",
        metavar="RULE_IDS",
        default="",
        help=(
            "Comma-separated LanguageTool rule IDs to suppress "
            "(e.g. WHITESPACE_RULE,EN_QUOTES)."
        ),
    )
    args = parser.parse_args()
    disabled = [r.strip() for r in args.disable.split(",") if r.strip()]

    found_any = False

    with GrammarChecker(disabled=disabled) as checker:
        for tex_file in _iter_tex_files(args.paths):
            for issue in checker.check_file(tex_file):
                found_any = True
                sugg = (
                    f"  → {', '.join(issue.suggestions)}" if issue.suggestions else ""
                )
                print(
                    f"{issue.file}:{issue.line}: [{issue.rule_id}] {issue.message}{sugg}"
                )

    sys.exit(1 if found_any else 0)


if __name__ == "__main__":
    main()
