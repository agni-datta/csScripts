#!/usr/bin/env python3
"""Squash all commits in one or more Git repositories to a single initial commit and force-push.

For each target repository this script:

1. Creates an orphan branch (``temp_branch``) with no history.
2. Stages and commits all current files as ``"Initial commit"``.
3. Deletes the old ``main`` branch and renames ``temp_branch`` to ``main``.
4. Force-pushes to ``origin main``, setting the upstream if needed.

Usage::

    # Squash one repository (interactive confirmation)
    python -m scripts.utils.git_squash_and_push /path/to/repo

    # Squash several repositories
    python -m scripts.utils.git_squash_and_push /path/to/repo-a /path/to/repo-b

    # Library usage
    >>> from scripts.utils.git_squash_and_push import GitSquashAndPushService
    >>> GitSquashAndPushService(["/path/to/repo"]).run()

Example::

    $ python -m scripts.utils.git_squash_and_push ~/repos/csNotes ~/repos/csWallpapers
    Squashing csNotes ... done (force-pushed)
    Squashing csWallpapers ... done (force-pushed)
    Done. 2 succeeded, 0 failed.
"""

import os
import subprocess
import sys
from typing import List, Optional, Tuple


class TerminalColor:
    """ANSI color codes for terminal output."""

    RED: str = "\033[0;31m"
    GREEN: str = "\033[0;32m"
    YELLOW: str = "\033[1;33m"
    BOLD: str = "\033[1m"
    RESET: str = "\033[0m"


class TerminalPrinter:
    """Handles formatted terminal output."""

    @staticmethod
    def info(message: str) -> None:
        """Print an informational message."""
        print(f"{TerminalColor.BOLD}{message}{TerminalColor.RESET}")

    @staticmethod
    def success(message: str) -> None:
        """Print a success message in green."""
        print(f"{TerminalColor.GREEN}{message}{TerminalColor.RESET}")

    @staticmethod
    def warning(message: str) -> None:
        """Print a warning message in yellow."""
        print(f"{TerminalColor.YELLOW}{message}{TerminalColor.RESET}")

    @staticmethod
    def error(message: str) -> None:
        """Print an error message in red."""
        print(f"{TerminalColor.RED}{message}{TerminalColor.RESET}")


class GitCommandRunner:
    """Runs git sub-commands in a given repository directory."""

    def __init__(self, repo_path: str) -> None:
        """Initialise with the path to a git repository.

        Args:
            repo_path: Absolute or relative path to the repository root.
        """
        self.repo_path: str = os.path.abspath(repo_path)

    def run(
        self,
        args: List[str],
        check: bool = True,
        capture: bool = True,
    ) -> Tuple[int, str, str]:
        """Execute a git command and return (returncode, stdout, stderr).

        Args:
            args: Git sub-command and its arguments, e.g. ``["status", "--short"]``.
            check: Raise ``subprocess.CalledProcessError`` on non-zero exit when True.
            capture: Capture stdout/stderr when True (suppresses terminal output).

        Returns:
            Tuple of (returncode, stdout, stderr) as strings.
        """
        result = subprocess.run(
            ["git"] + args,
            cwd=self.repo_path,
            check=check,
            capture_output=capture,
            text=True,
        )
        stdout = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.strip() if result.stderr else ""
        return result.returncode, stdout, stderr


class GitRepositoryValidator:
    """Validates that a path is a clean, pushable git repository."""

    def __init__(self, repo_path: str) -> None:
        """Initialise with the path to validate.

        Args:
            repo_path: Path to the repository root.
        """
        self.repo_path: str = os.path.abspath(repo_path)

    def is_git_repository(self) -> bool:
        """Return True if the path contains a ``.git`` directory."""
        return os.path.isdir(os.path.join(self.repo_path, ".git"))

    def get_default_branch(self, runner: GitCommandRunner) -> str:
        """Return the name of the repository's default branch.

        Falls back to ``main`` if symbolic-ref cannot resolve HEAD.

        Args:
            runner: A ``GitCommandRunner`` bound to this repository.

        Returns:
            Branch name string.
        """
        code, stdout, _ = runner.run(["symbolic-ref", "--short", "HEAD"], check=False)
        return stdout if code == 0 and stdout else "main"

    def has_remote(self, runner: GitCommandRunner) -> bool:
        """Return True if ``origin`` is a configured remote.

        Args:
            runner: A ``GitCommandRunner`` bound to this repository.
        """
        code, stdout, _ = runner.run(["remote"], check=False)
        return "origin" in stdout.splitlines()


class GitSquasher:
    """Squashes all commits in a repository to a single initial commit."""

    TEMP_BRANCH: str = "temp_squash_branch"
    COMMIT_MESSAGE: str = "Initial commit"

    def __init__(self, repo_path: str) -> None:
        """Initialise with the repository path.

        Args:
            repo_path: Absolute path to the repository root.
        """
        self.repo_path: str = os.path.abspath(repo_path)
        self.runner: GitCommandRunner = GitCommandRunner(repo_path)
        self.validator: GitRepositoryValidator = GitRepositoryValidator(repo_path)

    def _cleanup_temp_branch(self) -> None:
        """Delete the temporary branch if it exists (best-effort)."""
        self.runner.run(["branch", "-D", self.TEMP_BRANCH], check=False)

    def squash(self, branch: str) -> None:
        """Squash all commits onto ``branch`` via an orphan branch.

        Args:
            branch: The branch name to replace (e.g. ``"main"``).

        Raises:
            subprocess.CalledProcessError: If any git command fails.
            RuntimeError: If there are no files to commit.
        """
        self._cleanup_temp_branch()

        self.runner.run(["checkout", "--orphan", self.TEMP_BRANCH])

        _, status, _ = self.runner.run(["status", "--porcelain"], check=False)
        if not status:
            self._cleanup_temp_branch()
            raise RuntimeError(
                f"No files to commit in {self.repo_path} after creating orphan branch."
            )

        self.runner.run(["add", "-A"])
        self.runner.run(["commit", "-m", self.COMMIT_MESSAGE])

        self.runner.run(["branch", "-D", branch])
        self.runner.run(["branch", "-m", branch])

    def force_push(self, branch: str) -> None:
        """Force-push ``branch`` to ``origin``, setting upstream if needed.

        Args:
            branch: The local branch name to push.

        Raises:
            subprocess.CalledProcessError: If the push fails.
        """
        self.runner.run(["push", "--force", "--set-upstream", "origin", branch])


class OperationResultTracker:
    """Tracks success and failure counts across multiple repositories."""

    def __init__(self) -> None:
        """Initialise counters."""
        self.succeeded: int = 0
        self.failed: int = 0

    def record(self, success: bool) -> None:
        """Record the outcome of one operation.

        Args:
            success: True if the operation succeeded.
        """
        if success:
            self.succeeded += 1
        else:
            self.failed += 1

    def summary(self) -> str:
        """Return a human-readable summary string."""
        total = self.succeeded + self.failed
        return f"Done. {self.succeeded}/{total} succeeded, {self.failed} failed."


class GitSquashAndPushService:
    """Orchestrates squash-and-push across one or more repositories."""

    def __init__(
        self,
        repo_paths: List[str],
        skip_confirmation: bool = False,
    ) -> None:
        """Initialise the service.

        Args:
            repo_paths: Paths to the repositories to process.
            skip_confirmation: Skip the interactive confirmation prompt when True.
        """
        self.repo_paths: List[str] = [os.path.abspath(p) for p in repo_paths]
        self.skip_confirmation: bool = skip_confirmation
        self.tracker: OperationResultTracker = OperationResultTracker()

    def _confirm(self) -> bool:
        """Prompt the user for confirmation and return their answer.

        Returns:
            True if the user confirms, False otherwise.
        """
        if self.skip_confirmation:
            return True

        TerminalPrinter.warning(
            "This will PERMANENTLY erase all commit history in the following "
            "repositories and force-push to origin:"
        )
        for path in self.repo_paths:
            print(f"  {path}")

        try:
            answer = input("Proceed? [y/N] ").strip().lower()
        except EOFError:
            answer = ""

        return answer in {"y", "yes"}

    def _process_one(self, repo_path: str) -> bool:
        """Squash and push a single repository.

        Args:
            repo_path: Absolute path to the repository.

        Returns:
            True on success, False on failure.
        """
        name = os.path.basename(repo_path)
        runner = GitCommandRunner(repo_path)
        validator = GitRepositoryValidator(repo_path)

        if not validator.is_git_repository():
            TerminalPrinter.error(f"  {name}: not a git repository, skipping.")
            return False

        branch = validator.get_default_branch(runner)
        has_remote = validator.has_remote(runner)

        squasher = GitSquasher(repo_path)
        try:
            print(f"  Squashing {name} (branch: {branch}) ...", end=" ", flush=True)
            squasher.squash(branch)

            if has_remote:
                squasher.force_push(branch)
                TerminalPrinter.success("done (force-pushed)")
            else:
                TerminalPrinter.success("done (no remote configured, skipped push)")

            return True

        except subprocess.CalledProcessError as exc:
            TerminalPrinter.error(f"failed\n    git error: {exc.stderr or exc}")
            return False
        except RuntimeError as exc:
            TerminalPrinter.error(f"failed\n    {exc}")
            return False

    def run(self) -> None:
        """Execute squash-and-push for all configured repositories."""
        if not self.repo_paths:
            TerminalPrinter.warning("No repositories specified.")
            return

        if not self._confirm():
            TerminalPrinter.info("Aborted.")
            return

        for repo_path in self.repo_paths:
            success = self._process_one(repo_path)
            self.tracker.record(success)

        if self.tracker.failed:
            TerminalPrinter.warning(self.tracker.summary())
        else:
            TerminalPrinter.success(self.tracker.summary())


def _parse_args(argv: Optional[List[str]] = None) -> List[str]:
    """Parse command-line arguments and return a list of repository paths.

    Exits with usage information when no paths are supplied.

    Args:
        argv: Argument list (defaults to ``sys.argv[1:]``).

    Returns:
        List of repository path strings.
    """
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        prog = "python -m scripts.utils.git_squash_and_push"
        print(f"Usage: {prog} <repo-path> [<repo-path> ...]")
        print()
        print("Squash all commits in each repository to a single initial")
        print("commit and force-push to origin/main.")
        sys.exit(1)
    return args


def main() -> None:
    """Entry point for the git-squash-and-push script."""
    repo_paths = _parse_args()
    service = GitSquashAndPushService(repo_paths)
    service.run()


if __name__ == "__main__":
    main()
