#!/usr/bin/env python3
"""
track_repos.py

This script provides an object-oriented interface for interactively discovering all Git repositories
under the current directory, displaying their status, branch, and sync state, and allowing the user
to select which repositories to check. Output is colorized for clarity.

Usage:
    python track_repos.py
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
    BLUE: str = "\033[1;34m"
    CYAN: str = "\033[1;36m"
    MAGENTA: str = "\033[1;35m"
    BOLD: str = "\033[1m"
    RESET: str = "\033[0m"


class TerminalPrinter:
    """Handles all terminal output formatting and printing."""

    @staticmethod
    def print_horizontal_rule() -> None:
        """Prints a horizontal rule in cyan color."""
        print(f"{TerminalColor.CYAN}{'─' * 44}{TerminalColor.RESET}")

    @staticmethod
    def print_error(message: str) -> None:
        """Prints an error message in red.

        Args:
            message (str): The error message to print.
        """
        print(f"{TerminalColor.RED}{message}{TerminalColor.RESET}")

    @staticmethod
    def print_success(message: str) -> None:
        """Prints a success message in green.

        Args:
            message (str): The success message to print.
        """
        print(f"{TerminalColor.GREEN}{message}{TerminalColor.RESET}")

    @staticmethod
    def print_warning(message: str) -> None:
        """Prints a warning message in yellow.

        Args:
            message (str): The warning message to print.
        """
        print(f"{TerminalColor.YELLOW}{message}{TerminalColor.RESET}")

    @staticmethod
    def print_bold(message: str) -> None:
        """Prints a bold message.

        Args:
            message (str): The message to print in bold.
        """
        print(f"{TerminalColor.BOLD}{message}{TerminalColor.RESET}")

    @staticmethod
    def print_repo_header(name: str, path: str) -> None:
        """Prints the repository header with name and path.

        Args:
            name (str): The name of the repository.
            path (str): The path to the repository.
        """
        print(
            f"{TerminalColor.BOLD}{TerminalColor.BLUE}{name}{TerminalColor.RESET} "
            f"{TerminalColor.CYAN}({path}){TerminalColor.RESET}"
        )


class GitCommandRunner:
    """Executes git commands in a given repository."""

    def __init__(self, repo_path: str) -> None:
        """Initializes the command runner with the repository path.

        Args:
            repo_path (str): The path to the git repository.
        """
        self.repo_path: str = repo_path

    def run(self, args: List[str]) -> str:
        """Runs a git command and returns its output.

        Args:
            args (List[str]): List of git command arguments.

        Returns:
            str: Output of the git command as a string.
        """
        try:
            result: subprocess.CompletedProcess[str] = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""


class GitRepository:
    """Represents a single Git repository and provides status information."""

    def __init__(self, path: str) -> None:
        """Initializes a GitRepository instance.

        Args:
            path (str): The filesystem path to the git repository.
        """
        self.path: str = os.path.abspath(path)
        self.name: str = os.path.basename(self.path)
        self.git: GitCommandRunner = GitCommandRunner(self.path)

    def is_valid(self) -> bool:
        """Checks if the path is a valid git repository.

        Returns:
            bool: True if valid, False otherwise.
        """
        return os.path.isdir(os.path.join(self.path, ".git"))

    def get_current_branch(self) -> Optional[str]:
        """Gets the current branch name or None if in detached HEAD.

        Returns:
            Optional[str]: Branch name as string, or None if detached.
        """
        branch: str = self.git.run(["symbolic-ref", "--short", "HEAD"])
        return branch if branch else None

    def get_head_commit(self) -> str:
        """Gets the short SHA of the current HEAD commit.

        Returns:
            str: Short SHA string or '?' if not available.
        """
        commit: str = self.git.run(["rev-parse", "--short", "HEAD"])
        return commit if commit else "?"

    def get_working_tree_status(self) -> List[str]:
        """Gets the working tree status (uncommitted changes).

        Returns:
            List[str]: List of status lines.
        """
        status: str = self.git.run(["status", "--porcelain"])
        return status.splitlines() if status else []

    def has_upstream(self) -> bool:
        """Checks if the current branch has an upstream tracking branch.

        Returns:
            bool: True if upstream exists, False otherwise.
        """
        result: str = self.git.run(
            ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"]
        )
        return bool(result)

    def get_ahead_behind(self) -> Tuple[int, int]:
        """Gets the number of commits ahead/behind the upstream.

        Returns:
            Tuple[int, int]: Tuple (commits_ahead, commits_behind).
        """
        output: str = self.git.run(
            ["rev-list", "--left-right", "--count", "HEAD...@{u}"]
        )
        if output:
            try:
                ahead, behind = map(int, output.split())
                return ahead, behind
            except Exception:
                return 0, 0
        return 0, 0


class RepositoryStatusPresenter:
    """Handles the presentation of repository status."""

    def __init__(self, repo: GitRepository) -> None:
        """Initializes the presenter with a GitRepository.

        Args:
            repo (GitRepository): The repository to present.
        """
        self.repo: GitRepository = repo

    def display(self) -> None:
        """Displays the status of the repository in a colorized, formatted way."""
        if not self.repo.is_valid():
            TerminalPrinter.print_error(
                f"Error: '{self.repo.path}' is not a valid git repository."
            )
            return

        TerminalPrinter.print_repo_header(self.repo.name, self.repo.path)
        TerminalPrinter.print_horizontal_rule()

        # Branch or detached HEAD
        branch: Optional[str] = self.repo.get_current_branch()
        if branch:
            print(
                f"{TerminalColor.BOLD}Branch:{TerminalColor.RESET} "
                f"{TerminalColor.MAGENTA}{branch}{TerminalColor.RESET}"
            )
        else:
            head_commit: str = self.repo.get_head_commit()
            print(
                f"{TerminalColor.BOLD}Branch:{TerminalColor.RESET} "
                f"{TerminalColor.RED}(detached HEAD at {head_commit}){TerminalColor.RESET}"
            )

        # Working tree status
        status_lines: List[str] = self.repo.get_working_tree_status()
        if not status_lines:
            TerminalPrinter.print_success("✔ Clean")
        else:
            TerminalPrinter.print_warning("⚠ Uncommitted changes:")
            for line in status_lines:
                print(f"{TerminalColor.MAGENTA}  | {line}{TerminalColor.RESET}")

        # Ahead/behind info
        if self.repo.has_upstream():
            ahead, behind = self.repo.get_ahead_behind()
            if ahead > 0 or behind > 0:
                print(f"{TerminalColor.BOLD}Sync:{TerminalColor.RESET} ", end="")
                if ahead > 0:
                    print(
                        f"{TerminalColor.YELLOW}↑{ahead} ahead{TerminalColor.RESET} ",
                        end="",
                    )
                if behind > 0:
                    print(
                        f"{TerminalColor.YELLOW}↓{behind} behind{TerminalColor.RESET} ",
                        end="",
                    )
                print()
            else:
                TerminalPrinter.print_success("✔ Up to date with remote")
        else:
            TerminalPrinter.print_warning("No upstream tracking branch set.")

        print()


class GitRepositoryFinder:
    """Finds all Git repositories under a directory."""

    def __init__(self, root_dir: str = ".") -> None:
        """Initializes the GitRepositoryFinder.

        Args:
            root_dir (str, optional): The root directory to search from. Defaults to ".".
        """
        self.root_dir: str = root_dir

    def find_repositories(self) -> List[str]:
        """Recursively finds all Git repositories under the given directory.

        Returns:
            List[str]: List of repository paths.
        """
        repo_paths: List[str] = []
        for dirpath, dirnames, _ in os.walk(self.root_dir):
            if ".git" in dirnames:
                repo_paths.append(os.path.abspath(dirpath))
                # Don't recurse into .git directories
                dirnames.remove(".git")
        return sorted(set(repo_paths))


class RepositorySelector:
    """Handles interactive selection of repositories."""

    def __init__(self, repo_paths: List[str]) -> None:
        """Initializes the RepositorySelector.

        Args:
            repo_paths (List[str]): List of repository paths.
        """
        self.repo_paths: List[str] = repo_paths

    def select_repositories_interactive(self) -> List[str]:
        """Prompts the user to select repositories to check.

        Returns:
            List[str]: List of selected repository paths.
        """
        if not self.repo_paths:
            TerminalPrinter.print_warning("No repositories to select.")
            return []

        TerminalPrinter.print_bold("Found the following git repositories:")
        for idx, path in enumerate(self.repo_paths, 1):
            print(f"{idx}) {path}")

        while True:
            try:
                user_input: str = input(
                    f"{TerminalColor.BOLD}Enter numbers to check (comma-separated, 'a' for all, or empty to quit):{TerminalColor.RESET} "
                ).replace(" ", "")
            except EOFError:
                print("\nNo selection. Exiting.")
                return []

            if not user_input:
                print("No selection. Exiting.")
                return []

            if user_input.lower() == "a":
                return self.repo_paths

            selected_indices: List[int] = []
            valid_selection: bool = True
            for part in user_input.split(","):
                if part.isdigit():
                    idx: int = int(part) - 1
                    if 0 <= idx < len(self.repo_paths):
                        selected_indices.append(idx)
                    else:
                        TerminalPrinter.print_error(f"Invalid selection: {part}")
                        valid_selection = False
                else:
                    TerminalPrinter.print_error(f"Invalid input: {part}")
                    valid_selection = False

            if valid_selection and selected_indices:
                return [self.repo_paths[i] for i in selected_indices]
            else:
                TerminalPrinter.print_warning("Please enter valid selection(s).")


class GitRepoStatusApp:
    """Main application class for displaying git repository statuses."""

    def __init__(self, root_dir: str = ".") -> None:
        """Initializes the application.

        Args:
            root_dir (str, optional): The root directory to search for repositories. Defaults to ".".
        """
        self.root_dir: str = root_dir
        self.repositories: List[str] = []

    def discover_repositories(self) -> None:
        """Discovers all git repositories under the root directory."""
        finder: GitRepositoryFinder = GitRepositoryFinder(self.root_dir)
        self.repositories = finder.find_repositories()

    def select_repositories(self) -> List[str]:
        """Prompts the user to select repositories to check.

        Returns:
            List[str]: List of selected repository paths.
        """
        selector: RepositorySelector = RepositorySelector(self.repositories)
        return selector.select_repositories_interactive()

    def show_statuses(self, selected_repositories: List[str]) -> None:
        """Displays the status for each selected repository.

        Args:
            selected_repositories (List[str]): List of repository paths to display.
        """
        for repo_path in selected_repositories:
            repo: GitRepository = GitRepository(repo_path)
            try:
                presenter: RepositoryStatusPresenter = RepositoryStatusPresenter(repo)
                presenter.display()
            except Exception as exc:
                TerminalPrinter.print_error(f"Failed to show status for: {repo_path}")
                TerminalPrinter.print_error(str(exc))

    def run(self) -> None:
        """Runs the main application logic."""
        TerminalPrinter.print_bold(
            f"{TerminalColor.CYAN}Git Repository Status Overview (Recursive){TerminalColor.RESET}"
        )
        TerminalPrinter.print_horizontal_rule()

        self.discover_repositories()

        if not self.repositories:
            TerminalPrinter.print_warning(
                "No git repositories found in this directory or subdirectories."
            )
            sys.exit(0)

        selected_repositories: List[str] = self.select_repositories()
        if not selected_repositories:
            print("No repositories selected. Exiting.")
            sys.exit(0)

        self.show_statuses(selected_repositories)


class MainApp:
    """Entry point for the Git repository status application."""

    @staticmethod
    def main() -> None:
        """Main entry point for the script."""
        app: GitRepoStatusApp = GitRepoStatusApp(".")
        app.run()


if __name__ == "__main__":
    MainApp.main()
