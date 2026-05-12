#!/usr/bin/env python3
"""Clean LaTeX intermediate files using .gitignore patterns and optionally indent .tex files.

Two modes are available, controlled by ``--mode``:

``clean`` (default)
    Read the ``.gitignore`` in the target root directory, extract every glob
    pattern that refers to a file (not a directory), then delete all matching
    files found recursively under that root.  Patterns beginning with ``#`` or
    consisting only of whitespace are skipped.  Directory patterns (trailing
    ``/``) are also skipped so that source trees are never removed wholesale.

``indent``
    Run ``latexindent`` in-place on every ``*.tex`` file found recursively
    under the target root directory.  A ``.bak`` backup is created alongside
    each file before it is modified.

``all``
    Run ``clean`` followed by ``indent``.

Usage::

    # Clean using .gitignore in the current directory
    cs-latex-gitignore-cleaner

    # Clean a specific project root
    cs-latex-gitignore-cleaner --root ~/papers/my-paper

    # Only indent all .tex files
    cs-latex-gitignore-cleaner --mode indent

    # Clean then indent
    cs-latex-gitignore-cleaner --mode all

    # Library usage
    >>> from scripts.document.latex_gitignore_cleaner import LatexGitignoreCleanerService
    >>> LatexGitignoreCleanerService().run(root_path="/path/to/project", mode="all")

Dependencies:
    ``latexindent`` (part of TeX Live / MiKTeX) must be on ``$PATH`` for indent
    mode.

Example::

    $ cd ~/papers/phd-thesis
    $ cs-latex-gitignore-cleaner --mode all
    Reading .gitignore from: /Users/me/papers/phd-thesis
    Deleted 42 intermediate file(s).
    Indenting .tex files...
    Indented: main.tex
    Indented: sections/intro.tex
    Done. 2 file(s) indented.
"""

import argparse
import fnmatch
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple


class GitignorePatternLoader:
    """Loads and parses glob patterns from a .gitignore file."""

    @staticmethod
    def load_file_patterns(root_directory_path: str) -> List[str]:
        """Return file-level glob patterns from the .gitignore in root_directory_path.

        Directory patterns (trailing ``/``) and comment / blank lines are
        excluded so that only individual-file patterns are returned.

        Args:
            root_directory_path: Directory that contains the .gitignore file.

        Returns:
            List of glob pattern strings (e.g. ``["*.aux", "*.log", ...]``).

        Raises:
            FileNotFoundError: If no .gitignore exists in the given directory.
        """
        gitignore_path = os.path.join(root_directory_path, ".gitignore")
        if not os.path.isfile(gitignore_path):
            raise FileNotFoundError(
                f"No .gitignore found in: {root_directory_path}"
            )

        patterns: List[str] = []
        with open(gitignore_path, encoding="utf-8") as fh:
            for raw_line in fh:
                line = raw_line.rstrip("\n").strip()
                if not line or line.startswith("#"):
                    continue
                if line.endswith("/"):
                    # Directory pattern — skip to avoid mass-deleting directories.
                    continue
                patterns.append(line)
        return patterns


class IntermediateFileCollector:
    """Collects files under a directory tree that match a set of glob patterns."""

    @staticmethod
    def collect_matching_files(
        root_directory_path: str, glob_patterns: List[str]
    ) -> List[str]:
        """Walk root_directory_path and return paths of files matching any pattern.

        Only the file *name* (not the full path) is tested against each pattern,
        which mirrors the typical .gitignore behaviour for simple ``*.ext``
        patterns.

        Args:
            root_directory_path: Root of the directory tree to search.
            glob_patterns: List of glob patterns to test file names against.

        Returns:
            Sorted list of absolute file paths that matched at least one pattern.
        """
        matched_file_paths: List[str] = []
        for current_directory_path, _, file_names in os.walk(root_directory_path):
            for file_name in file_names:
                if any(fnmatch.fnmatch(file_name, pattern) for pattern in glob_patterns):
                    matched_file_paths.append(
                        os.path.join(current_directory_path, file_name)
                    )
        return sorted(matched_file_paths)


class IntermediateFileDeletionService:
    """Deletes a list of files using a thread pool for speed."""

    def __init__(self, max_worker_threads: int = 18):
        """Initialise the deletion service.

        Args:
            max_worker_threads: Maximum number of parallel deletion threads.
        """
        self.max_worker_threads = max_worker_threads

    def delete_files(self, file_paths: List[str]) -> Tuple[int, int]:
        """Delete every path in file_paths, returning success and failure counts.

        Args:
            file_paths: Absolute paths of files to delete.

        Returns:
            Tuple of (successful_deletions, failed_deletions).
        """
        successful_deletion_count = 0
        failed_deletion_count = 0
        results: List[bool] = []

        def _delete_single_file(file_path: str) -> bool:
            try:
                os.remove(file_path)
                return True
            except OSError as deletion_error:
                print(f"  Warning: could not delete {file_path}: {deletion_error}")
                return False

        with ThreadPoolExecutor(max_workers=self.max_worker_threads) as executor:
            results = list(executor.map(_delete_single_file, file_paths))

        successful_deletion_count = sum(1 for result in results if result)
        failed_deletion_count = sum(1 for result in results if not result)
        return successful_deletion_count, failed_deletion_count


class LatexIndentService:
    """Runs ``latexindent`` in-place on .tex files, creating .bak backups."""

    @staticmethod
    def collect_tex_files(root_directory_path: str) -> List[str]:
        """Return sorted list of all .tex files under root_directory_path.

        Args:
            root_directory_path: Root directory to search recursively.

        Returns:
            Sorted list of absolute .tex file paths.
        """
        tex_file_paths: List[str] = []
        for current_directory_path, _, file_names in os.walk(root_directory_path):
            for file_name in file_names:
                if file_name.endswith(".tex"):
                    tex_file_paths.append(
                        os.path.join(current_directory_path, file_name)
                    )
        return sorted(tex_file_paths)

    def indent_single_file(self, tex_file_path: str) -> bool:
        """Run ``latexindent`` in-place on a single .tex file.

        A ``.bak`` backup of the original is created via the ``-w`` flag of
        ``latexindent`` (``--overwrite`` with implicit backup).

        Args:
            tex_file_path: Absolute path to the .tex file.

        Returns:
            True if latexindent succeeded, False otherwise.
        """
        try:
            subprocess.run(
                ["latexindent", "--overwrite", "--silent", tex_file_path],
                check=True,
                capture_output=True,
            )
            return True
        except FileNotFoundError:
            print(
                "  Error: 'latexindent' not found on PATH. "
                "Install it via TeX Live or MiKTeX."
            )
            return False
        except subprocess.CalledProcessError as process_error:
            print(
                f"  Warning: latexindent failed for {tex_file_path}: {process_error}"
            )
            return False

    def indent_all_tex_files(
        self, root_directory_path: str
    ) -> Tuple[int, int]:
        """Run ``latexindent`` on every .tex file under root_directory_path.

        Args:
            root_directory_path: Root directory to search for .tex files.

        Returns:
            Tuple of (successful_count, failed_count).
        """
        tex_file_paths = self.collect_tex_files(root_directory_path)
        if not tex_file_paths:
            print("  No .tex files found.")
            return 0, 0

        successful_indent_count = 0
        failed_indent_count = 0
        for tex_file_path in tex_file_paths:
            if self.indent_single_file(tex_file_path):
                print(f"  Indented: {tex_file_path}")
                successful_indent_count += 1
            else:
                failed_indent_count += 1

        return successful_indent_count, failed_indent_count


class LatexGitignoreCleanerService:
    """Orchestrates .gitignore-driven cleaning and optional latexindent formatting."""

    def __init__(self):
        """Initialise all component services."""
        self.pattern_loader = GitignorePatternLoader()
        self.file_collector = IntermediateFileCollector()
        self.deletion_service = IntermediateFileDeletionService()
        self.indent_service = LatexIndentService()

    def run_clean(self, root_path: str) -> None:
        """Delete all files matched by .gitignore patterns under root_path.

        Args:
            root_path: Absolute path to the project root directory.
        """
        print(f"Reading .gitignore from: {root_path}")
        patterns = self.pattern_loader.load_file_patterns(root_path)
        print(f"Loaded {len(patterns)} pattern(s) from .gitignore.")

        matched_files = self.file_collector.collect_matching_files(root_path, patterns)
        if not matched_files:
            print("No matching intermediate files found.")
            return

        print(f"Deleting {len(matched_files)} file(s)...")
        successful, failed = self.deletion_service.delete_files(matched_files)
        print(
            f"Deleted {successful} intermediate file(s)."
            + (f" ({failed} failed)" if failed else "")
        )

    def run_indent(self, root_path: str) -> None:
        """Run latexindent on all .tex files under root_path.

        Args:
            root_path: Absolute path to the project root directory.
        """
        print("Indenting .tex files...")
        successful, failed = self.indent_service.indent_all_tex_files(root_path)
        print(
            f"Done. {successful} file(s) indented."
            + (f" ({failed} failed)" if failed else "")
        )

    def run(self, root_path: Optional[str] = None, mode: str = "clean") -> None:
        """Execute the requested operation mode.

        Args:
            root_path: Project root directory. Defaults to the current directory.
            mode: One of ``"clean"``, ``"indent"``, or ``"all"``.
        """
        effective_root = os.path.abspath(root_path or os.getcwd())

        if mode in ("clean", "all"):
            self.run_clean(effective_root)

        if mode in ("indent", "all"):
            self.run_indent(effective_root)


class CommandLineArgumentParser:
    """Parses command-line arguments for the latex-gitignore-cleaner tool."""

    @staticmethod
    def parse_arguments() -> argparse.Namespace:
        """Parse and return command-line arguments.

        Returns:
            Parsed argparse Namespace.
        """
        parser = argparse.ArgumentParser(
            description=(
                "Clean LaTeX intermediate files using .gitignore patterns "
                "and optionally run latexindent on all .tex files."
            )
        )
        parser.add_argument(
            "--root",
            default=None,
            help=(
                "Project root directory containing the .gitignore. "
                "Defaults to the current working directory."
            ),
        )
        parser.add_argument(
            "--mode",
            choices=["clean", "indent", "all"],
            default="clean",
            help=(
                "Operation mode: 'clean' deletes .gitignore-matched files, "
                "'indent' runs latexindent on all .tex files, "
                "'all' does both. Default: clean."
            ),
        )
        return parser.parse_args()


class CleanerApplicationLauncher:
    """Launches the latex-gitignore-cleaner application."""

    @staticmethod
    def launch_application() -> None:
        """Parse arguments and run the cleaner service."""
        args = CommandLineArgumentParser.parse_arguments()
        service = LatexGitignoreCleanerService()
        service.run(root_path=args.root, mode=args.mode)


def main() -> None:
    """Main entry point for the latex-gitignore-cleaner script."""
    application_launcher = CleanerApplicationLauncher()
    application_launcher.launch_application()


if __name__ == "__main__":
    main()
