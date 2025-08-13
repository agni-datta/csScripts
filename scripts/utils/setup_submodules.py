#!/usr/bin/env python3
"""Git Submodule Manager.

A modern Python utility for managing git submodules across GitHub, GitLab,
and Overleaf repositories, with interactive internal repository discovery,
conversion, and Catppuccin-themed logging.

Example:
    $ python setup_submodules.py
    $ python setup_submodules.py scan-internal
    $ python setup_submodules.py add
"""

import argparse
import csv
from enum import Enum
import logging
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Type, TypeVar

# Catppuccin color palette for terminal output
CATPPUCCIN: Dict[str, str] = {
    "rosewater": "\033[38;2;245;224;220m",
    "flamingo": "\033[38;2;242;205;205m",
    "pink": "\033[38;2;245;194;231m",
    "mauve": "\033[38;2;203;166;247m",
    "red": "\033[38;2;243;139;168m",
    "maroon": "\033[38;2;235;160;172m",
    "peach": "\033[38;2;250;179;135m",
    "yellow": "\033[38;2;249;226;175m",
    "green": "\033[38;2;166;227;161m",
    "teal": "\033[38;2;148;226;213m",
    "sky": "\033[38;2;137;220;235m",
    "sapphire": "\033[38;2;116;199;236m",
    "blue": "\033[38;2;137;180;250m",
    "lavender": "\033[38;2;180;190;254m",
    "text": "\033[38;2;205;214;244m",
    "subtext1": "\033[38;2;186;194;222m",
    "subtext0": "\033[38;2;166;173;200m",
    "overlay2": "\033[38;2;147;153;178m",
    "overlay1": "\033[38;2;127;132;156m",
    "overlay0": "\033[38;2;108;112;134m",
    "surface2": "\033[38;2;88;91;112m",
    "surface1": "\033[38;2;69;71;90m",
    "surface0": "\033[38;2;49;50;68m",
    "base": "\033[38;2;30;30;46m",
    "mantle": "\033[38;2;24;24;37m",
    "crust": "\033[38;2;17;17;27m",
    "reset": "\033[0m",
}


def colorize(text: str, color: str) -> str:
    """Colorize the given text using the Catppuccin color palette.

    Args:
        text (str): The text to colorize.
        color (str): The color name from the Catppuccin palette.

    Returns:
        str: The colorized text.
    """
    return f"{CATPPUCCIN.get(color, CATPPUCCIN['text'])}{text}{CATPPUCCIN['reset']}"


class CatppuccinFormatter(logging.Formatter):
    """A logging formatter that applies Catppuccin color themes to log output."""

    LEVEL_COLORS: Dict[int, str] = {
        logging.DEBUG: "overlay2",
        logging.INFO: "blue",
        logging.WARNING: "yellow",
        logging.ERROR: "red",
        logging.CRITICAL: "maroon",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record with Catppuccin colors.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log message.
        """
        level_color: str = self.LEVEL_COLORS.get(record.levelno, "text")
        levelname: str = colorize(f"{record.levelname:8}", level_color)
        name: str = colorize(record.name, "mauve")
        msg: str = colorize(record.getMessage(), "text")
        asctime: str = colorize(self.formatTime(record, self.datefmt), "overlay1")
        return f"{asctime} {name} {levelname} {msg}"


class CatppuccinLogger:
    """Utility class to set up Catppuccin-themed logging."""

    @staticmethod
    def setup(level: int = logging.INFO) -> None:
        """Set up the root logger with CatppuccinFormatter.

        Args:
            level (int, optional): Logging level. Defaults to logging.INFO.
        """
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            CatppuccinFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
        )
        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)
        root.setLevel(level)


class RepositoryType(Enum):
    """Enumeration of supported repository types."""

    GITHUB = "github"
    GITLAB = "gitlab"
    OVERLEAF = "overleaf"


class SubmoduleOperationError(Exception):
    """Exception raised for errors during submodule operations."""

    pass


class GitCommandExecutor:
    """Executes git commands within a specified working directory."""

    def __init__(self, working_directory: Path) -> None:
        """Initialize the GitCommandExecutor.

        Args:
            working_directory (Path): The working directory for git commands.
        """
        self._working_directory = working_directory
        self._logger = logging.getLogger(__name__)

    def execute_command(
        self, command: List[str], check: bool = True, capture_output: bool = True
    ) -> subprocess.CompletedProcess[str]:
        """Execute a git command in the working directory.

        Args:
            command (List[str]): The command and its arguments.
            check (bool, optional): Whether to raise an error on failure. Defaults to True.
            capture_output (bool, optional): Whether to capture stdout/stderr. Defaults to True.

        Returns:
            subprocess.CompletedProcess[str]: The result of the command.

        Raises:
            SubmoduleOperationError: If the command fails.
        """
        self._logger.debug(
            colorize(f"Executing command: {' '.join(command)}", "overlay2")
        )
        try:
            result = subprocess.run(
                command,
                cwd=self._working_directory,
                check=check,
                capture_output=capture_output,
                text=True,
            )
            return result
        except subprocess.CalledProcessError as e:
            error_msg = f"Git command failed: {' '.join(command)}"
            if e.stderr:
                error_msg += f"\nError: {e.stderr}"
            self._logger.error(colorize(error_msg, "red"))
            raise SubmoduleOperationError(error_msg) from e

    def is_git_repository(self, path: Path) -> bool:
        """Check if the given path is a git repository.

        Args:
            path (Path): The path to check.

        Returns:
            bool: True if the path is a git repository, False otherwise.
        """
        git_dir = path / ".git"
        return git_dir.exists() and (git_dir.is_dir() or git_dir.is_file())

    def get_remote_url(
        self, repository_path: Path, remote_name: str = "origin"
    ) -> Optional[str]:
        """Get the remote URL for a repository.

        Args:
            repository_path (Path): The path to the repository.
            remote_name (str, optional): The remote name. Defaults to "origin".

        Returns:
            Optional[str]: The remote URL, or None if not found.
        """
        try:
            result = self.execute_command(
                ["git", "-C", str(repository_path), "remote", "get-url", remote_name]
            )
            return result.stdout.strip()
        except SubmoduleOperationError:
            return None

    def is_submodule(self, path: Path) -> bool:
        """Check if the given path is a git submodule.

        Args:
            path (Path): The path to check.

        Returns:
            bool: True if the path is a submodule, False otherwise.
        """
        try:
            relative_path = path.relative_to(self._working_directory)
            self.execute_command(["git", "submodule", "status", str(relative_path)])
            return True
        except (SubmoduleOperationError, ValueError):
            return False


class RepositoryTypeDetector:
    """Detects the type of a repository based on its remote URL."""

    _URL_PATTERNS: Dict[RepositoryType, List[str]] = {
        RepositoryType.GITHUB: [r"github\.com"],
        RepositoryType.GITLAB: [r"gitlab\.com", r"gitlab\."],
        RepositoryType.OVERLEAF: [r"overleaf\.com"],
    }

    def detect_repository_type(self, remote_url: str) -> RepositoryType:
        """Detect the repository type from its remote URL.

        Args:
            remote_url (str): The remote URL of the repository.

        Returns:
            RepositoryType: The detected repository type.
        """
        for repo_type, patterns in self._URL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, remote_url):
                    return repo_type
        return RepositoryType.GITHUB


T = TypeVar("T", bound="SubmoduleRecord")


class SubmoduleRecord:
    """Represents a submodule record with type, URL, and target path."""

    def __init__(
        self, repository_type: RepositoryType, remote_url: str, target_path: Path
    ) -> None:
        """Initialize a SubmoduleRecord.

        Args:
            repository_type (RepositoryType): The type of the repository.
            remote_url (str): The remote URL of the repository.
            target_path (Path): The local target path for the submodule.
        """
        self.repository_type = repository_type
        self.remote_url = remote_url
        self.target_path = target_path

    def to_csv_row(self) -> List[str]:
        """Convert the submodule record to a CSV row.

        Returns:
            List[str]: The CSV row representation.
        """
        return [self.repository_type.value, self.remote_url, str(self.target_path)]

    @classmethod
    def from_csv_row(cls: Type[T], row: List[str]) -> T:
        """Create a SubmoduleRecord from a CSV row.

        Args:
            row (List[str]): The CSV row.

        Returns:
            SubmoduleRecord: The created submodule record.

        Raises:
            ValueError: If the repository type is invalid.
        """
        try:
            repo_type = RepositoryType(row[0])
        except ValueError as e:
            raise ValueError(f"Invalid repository type: {row[0]}") from e
        return cls(repo_type, row[1], Path(row[2]))


class SubmoduleConfigurationManager:
    """Manages loading and saving submodule configuration records."""

    def __init__(self, config_file_path: Path) -> None:
        """Initialize the SubmoduleConfigurationManager.

        Args:
            config_file_path (Path): Path to the configuration file.
        """
        self._config_file_path = config_file_path
        self._logger = logging.getLogger(__name__)

    def load_submodule_records(self) -> List[SubmoduleRecord]:
        """Load submodule records from the configuration file.

        Returns:
            List[SubmoduleRecord]: The list of loaded submodule records.
        """
        records: List[SubmoduleRecord] = []
        if not self._config_file_path.exists():
            return records
        try:
            with open(
                self._config_file_path, "r", newline="", encoding="utf-8"
            ) as file:
                reader = csv.reader(file)
                for row in reader:
                    if not row or row[0].startswith("#"):
                        continue
                    try:
                        if len(row) >= 3:
                            records.append(SubmoduleRecord.from_csv_row(row))
                    except ValueError:
                        continue
        except IOError:
            pass
        return records

    def save_submodule_record(self, record: SubmoduleRecord) -> None:
        """Append a submodule record to the configuration file.

        Args:
            record (SubmoduleRecord): The submodule record to save.

        Raises:
            SubmoduleOperationError: If saving fails.
        """
        try:
            with open(
                self._config_file_path, "a", newline="", encoding="utf-8"
            ) as file:
                writer = csv.writer(file)
                writer.writerow(record.to_csv_row())
        except IOError as e:
            raise SubmoduleOperationError(f"Failed to save configuration: {e}")

    def initialize_default_configuration(self) -> None:
        """Initialize the configuration file with default entries if it does not exist.

        Raises:
            SubmoduleOperationError: If initialization fails.
        """
        if self._config_file_path.exists():
            return
        default_entries = [
            "# repo_type,repo_url,target_path",
            "# Example GitHub entries",
            "github,https://github.com/agni-datta/ObfPrivateCoinRoundCollapse.git,papers/csPrivateCoinRoundCollapsePaper",
            "github,https://github.com/agni-datta/csSoKMemProofs.git,texts/csAccumulatorsText",
            "github,https://github.com/agni-datta/csComplexityTheoreticPKCText.git,texts/csComplexityTheoreticPKCText",
            "github,https://github.com/agni-datta/csCybercrimeInvestigationText.git,texts/csCybercrimeInvestigationText",
            "github,https://github.com/agni-datta/csPropositionalLogicText.git,texts/csPropositionalLogicText",
            "github,https://github.com/agni-datta/csQuantumCryptographyText.git,texts/csQuantumCryptographyText",
            "# Example Overleaf entries",
            "overleaf,https://git@git.overleaf.com/67c0aa409a56b0a18ce35e60,papers/csE2ECloudSecurityPaper",
            "overleaf,https://git@git.overleaf.com/68778c61966f2ddf5c9cc499,papers/csNonInteractiveRationalProofsPaper",
            "overleaf,https://git@git.overleaf.com/6826e22deb3c9036139b1fb8,papers/csNonInteractiveStreamingInteractiveProofsPaper",
            "overleaf,https://git@git.overleaf.com/6867d4a5e5af53a598ff3c82,papers/csSecurityAnalysisXHMQVPaper",
        ]
        try:
            with open(self._config_file_path, "w", encoding="utf-8") as file:
                file.write("\n".join(default_entries) + "\n")
        except IOError as e:
            raise SubmoduleOperationError(f"Failed to initialize configuration: {e}")


class InternalRepositoryScanner:
    """Scans for internal git repositories within a project."""

    def __init__(
        self,
        project_root: Path,
        git_executor: GitCommandExecutor,
        repository_detector: RepositoryTypeDetector,
    ) -> None:
        """Initialize the InternalRepositoryScanner.

        Args:
            project_root (Path): The root directory of the project.
            git_executor (GitCommandExecutor): Executor for git commands.
            repository_detector (RepositoryTypeDetector): Detector for repository types.
        """
        self._project_root = project_root
        self._git_executor = git_executor
        self._repository_detector = repository_detector
        self._logger = logging.getLogger(__name__)

    def find_internal_repositories(self) -> List[SubmoduleRecord]:
        """Find all internal git repositories that are not submodules.

        Returns:
            List[SubmoduleRecord]: List of discovered internal repositories.
        """
        internal_repos: List[SubmoduleRecord] = []
        for git_dir in self._project_root.rglob(".git"):
            if not git_dir.is_dir():
                continue
            repo_path = git_dir.parent
            if repo_path == self._project_root:
                continue
            if self._git_executor.is_submodule(repo_path):
                continue
            remote_url = self._git_executor.get_remote_url(repo_path)
            if not remote_url:
                continue
            repo_type = self._repository_detector.detect_repository_type(remote_url)
            try:
                relative_path = repo_path.relative_to(self._project_root)
                internal_repos.append(
                    SubmoduleRecord(repo_type, remote_url, relative_path)
                )
            except ValueError:
                continue
        return internal_repos


class SubmoduleManager:
    """Manages submodules for a project, including adding and scanning."""

    def __init__(
        self,
        working_directory: Path,
        config_file: str = "github_repo.txt",
        log_level: int = logging.INFO,
    ) -> None:
        """Initialize the SubmoduleManager.

        Args:
            working_directory (Path): The working directory for the project.
            config_file (str, optional): The configuration file name. Defaults to "github_repo.txt".
            log_level (int, optional): Logging level. Defaults to logging.INFO.
        """
        self._working_directory = working_directory
        self._config_file_path = working_directory / config_file
        self._git_executor = GitCommandExecutor(working_directory)
        self._repository_detector = RepositoryTypeDetector()
        self._config_manager = SubmoduleConfigurationManager(self._config_file_path)
        self._internal_scanner = InternalRepositoryScanner(
            working_directory, self._git_executor, self._repository_detector
        )
        self._logger = logging.getLogger(__name__)
        self._setup_logging(log_level)
        self._config_manager.initialize_default_configuration()

    def _setup_logging(self, level: int) -> None:
        """Set up Catppuccin-themed logging.

        Args:
            level (int): Logging level.
        """
        CatppuccinLogger.setup(level)

    def add_submodule(self, record: SubmoduleRecord) -> None:
        """Add a submodule to the project.

        Args:
            record (SubmoduleRecord): The submodule record to add.

        Raises:
            SubmoduleOperationError: If adding the submodule fails.
        """
        if record.repository_type == RepositoryType.OVERLEAF:
            pass
        try:
            self._git_executor.execute_command(
                ["git", "submodule", "add", record.remote_url, str(record.target_path)]
            )
        except SubmoduleOperationError as e:
            raise SubmoduleOperationError(
                f"Failed to add submodule {record.target_path}: {e}"
            ) from e

    def add_all_submodules_from_config(self) -> None:
        """Add all submodules listed in the configuration file."""
        records = self._config_manager.load_submodule_records()
        for record in records:
            try:
                self.add_submodule(record)
            except SubmoduleOperationError:
                continue

    def scan_and_add_internal_repositories(self, interactive: bool = True) -> None:
        """Scan for internal repositories and add them as submodules.

        Args:
            interactive (bool, optional): Whether to prompt the user interactively. Defaults to True.
        """
        internal_repos = self._internal_scanner.find_internal_repositories()
        if not internal_repos:
            return
        if interactive:
            self._add_internal_repositories_interactively(internal_repos)
        else:
            self._add_internal_repositories_batch(internal_repos)

    def _add_internal_repositories_interactively(
        self, repositories: List[SubmoduleRecord]
    ) -> None:
        """Interactively add internal repositories as submodules.

        Args:
            repositories (List[SubmoduleRecord]): List of internal repositories.
        """
        for repo in repositories:
            print(colorize("\nFound internal repository:", "mauve"))
            print(colorize(f"  Path: {repo.target_path}", "blue"))
            print(colorize(f"  Type: {repo.repository_type.value}", "teal"))
            print(colorize(f"  URL: {repo.remote_url}", "overlay2"))
            response = (
                input(colorize("Add this repository as a submodule? [y/N]: ", "peach"))
                .strip()
                .lower()
            )
            if response in ["y", "yes"]:
                try:
                    self._convert_internal_to_submodule(repo)
                    self._config_manager.save_submodule_record(repo)
                    print(
                        colorize(
                            f"✓ Successfully converted {repo.target_path} to submodule",
                            "green",
                        )
                    )
                except SubmoduleOperationError:
                    print(colorize(f"✗ Failed to convert {repo.target_path}", "red"))
            else:
                print(colorize(f"Skipped {repo.target_path}", "yellow"))

    def _add_internal_repositories_batch(
        self, repositories: List[SubmoduleRecord]
    ) -> None:
        """Add internal repositories as submodules without user prompts.

        Args:
            repositories (List[SubmoduleRecord]): List of internal repositories.
        """
        for repo in repositories:
            try:
                self._convert_internal_to_submodule(repo)
                self._config_manager.save_submodule_record(repo)
            except SubmoduleOperationError:
                pass

    def _convert_internal_to_submodule(self, record: SubmoduleRecord) -> None:
        """Convert an internal repository to a submodule.

        Args:
            record (SubmoduleRecord): The internal repository record.

        Raises:
            SubmoduleOperationError: If conversion fails.
        """
        repo_path = self._working_directory / record.target_path
        if repo_path.exists():
            try:
                self._git_executor.execute_command(
                    ["git", "rm", "-rf", str(record.target_path)], check=False
                )
            except SubmoduleOperationError:
                pass
            if repo_path.exists():
                shutil.rmtree(repo_path)
        self.add_submodule(record)

    def add_submodule_interactively(self) -> None:
        """Interactively prompt the user to add a new submodule."""
        print(colorize("\n=== Add Submodule Interactively ===", "mauve"))
        print(colorize("Available repository types:", "teal"))
        for i, repo_type in enumerate(RepositoryType, 1):
            print(colorize(f"  {i}. {repo_type.value}", "blue"))
        repo_type = None
        while True:
            try:
                choice = int(
                    input(colorize("Select repository type (1-3): ", "peach")).strip()
                )
                if 1 <= choice <= len(RepositoryType):
                    repo_type = list(RepositoryType)[choice - 1]
                    break
                else:
                    print(
                        colorize("Invalid choice. Please enter 1, 2, or 3.", "yellow")
                    )
            except ValueError:
                print(colorize("Invalid input. Please enter a number.", "yellow"))
        remote_url = input(colorize("Enter the repository URL: ", "sky")).strip()
        if not remote_url:
            print(colorize("Error: Repository URL is required.", "red"))
            return
        target_path_str = input(
            colorize("Enter the target local path (e.g., papers/myPaper): ", "sky")
        ).strip()
        if not target_path_str:
            print(colorize("Error: Target path is required.", "red"))
            return
        target_path = Path(target_path_str)
        record = SubmoduleRecord(repo_type, remote_url, target_path)
        try:
            self.add_submodule(record)
            self._config_manager.save_submodule_record(record)
            print(colorize(f"✓ Successfully added submodule: {target_path}", "green"))
        except SubmoduleOperationError:
            print(colorize(f"✗ Failed to add submodule", "red"))


class CommandLineInterface:
    """Command-line interface for the Git Submodule Manager."""

    def __init__(self) -> None:
        """Initialize the CommandLineInterface."""
        self._submodule_manager: Optional[SubmoduleManager] = None

    def run(self) -> None:
        """Parse command-line arguments and execute the selected command."""
        parser = self._create_argument_parser()
        args = parser.parse_args()
        # Set log level based on --log-catppuccin flag
        log_level = logging.INFO
        if getattr(args, "log_catppuccin", False):
            log_level = logging.DEBUG
        self._submodule_manager = SubmoduleManager(Path.cwd(), log_level=log_level)
        try:
            if args.command == "add":
                if len(sys.argv) == 2:
                    self._submodule_manager.add_submodule_interactively()
                elif len(sys.argv) == 5:
                    repo_type = RepositoryType(sys.argv[2])
                    remote_url = sys.argv[3]
                    target_path = Path(sys.argv[4])
                    record = SubmoduleRecord(repo_type, remote_url, target_path)
                    self._submodule_manager.add_submodule(record)
                    self._submodule_manager._config_manager.save_submodule_record(
                        record
                    )
                else:
                    parser.print_help()
                    sys.exit(1)
            elif args.command == "scan-internal":
                self._submodule_manager.scan_and_add_internal_repositories(
                    interactive=args.interactive
                )
            elif args.command is None:
                self._print_overleaf_instructions()
                self._submodule_manager.add_all_submodules_from_config()
            else:
                parser.print_help()
                sys.exit(1)
        except KeyboardInterrupt:
            print(colorize("\nOperation cancelled by user.", "yellow"))
            sys.exit(1)
        except Exception:
            sys.exit(1)

    def _create_argument_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser for the command-line interface.

        Returns:
            argparse.ArgumentParser: The configured argument parser.
        """
        parser = argparse.ArgumentParser(
            description="Git Submodule Manager - Modern Python utility for managing git submodules",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=colorize(
                """
Examples:
  %(prog)s                          # Add all submodules from configuration file
  %(prog)s add                      # Add submodule interactively
  %(prog)s add github <url> <path>  # Add submodule directly
  %(prog)s scan-internal            # Scan and interactively add internal repos
  %(prog)s scan-internal --batch    # Scan and add internal repos without prompts
  %(prog)s --log-catppuccin         # Log everything in Catppuccin theme (DEBUG)
                """,
                "lavender",
            ),
        )
        parser.add_argument(
            "command",
            nargs="?",
            choices=["add", "scan-internal"],
            help=colorize("Command to execute", "blue"),
        )
        parser.add_argument(
            "--interactive",
            action="store_true",
            default=True,
            help=colorize("Interactive mode for scan-internal (default: True)", "teal"),
        )
        parser.add_argument(
            "--batch",
            action="store_false",
            dest="interactive",
            help=colorize("Batch mode for scan-internal (no user prompts)", "peach"),
        )
        parser.add_argument(
            "--log-catppuccin",
            action="store_true",
            help=colorize("Log everything in Catppuccin theme (DEBUG level)", "mauve"),
        )
        return parser

    def _print_overleaf_instructions(self) -> None:
        """Print instructions for handling Overleaf submodules."""
        print(
            colorize(
                """
If you have Overleaf submodules, make sure authentication is set up before running this script.
You can add Overleaf submodules interactively or by editing the configuration file.
""",
                "yellow",
            )
        )


class SubmoduleMainApp:
    """Main application class for the Git Submodule Manager."""

    def __init__(self) -> None:
        """Initialize the SubmoduleMainApp."""
        self.cli = CommandLineInterface()

    def run(self) -> None:
        """Run the main application."""
        self.cli.run()


if __name__ == "__main__":
    app = SubmoduleMainApp()
    app.run()
