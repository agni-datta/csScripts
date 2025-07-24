"""
Git Repository Reset Module

This module provides a utility for safely resetting a Git repository to a clean state.
It automates the process of pulling the latest changes, discarding local modifications,
and cleaning untracked files and directories.

Features:
- Automated git pull and reset
- Cleans untracked files and directories
- Command-line interface for repository management
- Logging and error handling

Example:
    >>> service = GitRepositoryResetService("/path/to/repo")
    >>> service.execute_repository_reset_process()
"""

import os
import subprocess
from typing import List, Optional


class GitRepositoryDiscoveryService:
    """
    Service for discovering Git repositories in a directory structure.

    This service provides functionality to recursively search for Git repositories
    within a specified directory hierarchy.
    """

    def discover_git_repositories(self, root_directory_path: str) -> List[str]:
        """
        Recursively discover Git repositories under the specified root directory.

        Args:
            root_directory_path: The root directory to start searching for Git repositories.

        Returns:
            List[str]: A list of absolute paths to directories containing '.git'.
        """
        discovered_repository_paths: List[str] = []

        for current_directory_path, _, _ in os.walk(root_directory_path):
            if ".git" in os.listdir(current_directory_path):
                discovered_repository_paths.append(
                    os.path.abspath(current_directory_path)
                )

        return discovered_repository_paths


class GitCommandExecutionService:
    """
    Service for executing Git commands on repositories.

    This service provides methods to execute various Git commands on specified
    repository directories.
    """

    def execute_hard_reset_and_pull(self, repository_directory_path: str) -> bool:
        """
        Execute 'git reset --hard' and 'git pull' commands in the specified repository.

        Args:
            repository_directory_path: The directory where the Git commands should be executed.

        Returns:
            bool: True if commands executed successfully, False otherwise.
        """
        try:
            # Execute git reset --hard
            subprocess.run(
                ["git", "reset", "--hard"],
                cwd=repository_directory_path,
                check=True,
                capture_output=True,
            )

            # Execute git pull
            subprocess.run(
                ["git", "pull"],
                cwd=repository_directory_path,
                check=True,
                capture_output=True,
            )

            print(f"Git commands executed successfully in {repository_directory_path}")
            return True

        except subprocess.CalledProcessError as command_error:
            print(
                f"Error executing git commands in {repository_directory_path}: {command_error}"
            )
            return False


class OperationResultTracker:
    """
    Tracks the results of Git operations.

    This class maintains counts of successful and failed operations
    and provides a summary of the results.
    """

    def __init__(self):
        """
        Initialize the OperationResultTracker with zero counts.
        """
        self.successful_operation_count: int = 0
        self.failed_operation_count: int = 0

    def record_operation_result(self, success: bool) -> None:
        """
        Record the result of an operation.

        Args:
            success: Whether the operation was successful.
        """
        if success:
            self.successful_operation_count += 1
        else:
            self.failed_operation_count += 1

    def get_operation_summary(self) -> str:
        """
        Get a summary of the operation results.

        Returns:
            str: A formatted summary string.
        """
        total_operations = self.successful_operation_count + self.failed_operation_count

        return (
            f"Operation Summary:\n"
            f"  Total repositories processed: {total_operations}\n"
            f"  Successful operations: {self.successful_operation_count}\n"
            f"  Failed operations: {self.failed_operation_count}"
        )


class GitRepositoryResetService:
    """
    Service for resetting Git repositories to a clean state.

    This service orchestrates the process of discovering Git repositories
    and executing reset and pull commands on them.
    """

    def __init__(self, target_directory_path: Optional[str] = None):
        """
        Initialize the GitRepositoryResetService.

        Args:
            target_directory_path: The directory to search for Git repositories.
                                  If None, uses the script's directory.
        """
        self.target_directory_path: str = target_directory_path or os.path.dirname(
            os.path.abspath(__file__)
        )
        self.repository_discovery_service = GitRepositoryDiscoveryService()
        self.command_execution_service = GitCommandExecutionService()
        self.result_tracker = OperationResultTracker()

    def execute_repository_reset_process(self) -> None:
        """
        Execute the complete repository reset process.
        """
        # Discover Git repositories
        discovered_repository_paths = (
            self.repository_discovery_service.discover_git_repositories(
                self.target_directory_path
            )
        )

        if not discovered_repository_paths:
            print(f"No Git repositories found under {self.target_directory_path}")
            return

        print(f"Found {len(discovered_repository_paths)} Git repositories to process")

        # Process each repository
        for repository_path in discovered_repository_paths:
            operation_success = (
                self.command_execution_service.execute_hard_reset_and_pull(
                    repository_path
                )
            )
            self.result_tracker.record_operation_result(operation_success)

        # Display summary
        print("\n" + self.result_tracker.get_operation_summary())


class GitRepositoryResetApplicationLauncher:
    """
    Launches the Git repository reset application.
    """

    @staticmethod
    def launch_application() -> None:
        """
        Launch the Git repository reset application.
        """
        reset_service = GitRepositoryResetService()
        reset_service.execute_repository_reset_process()


def main() -> None:
    """
    Main entry point for the Git repository reset script.
    """
    application_launcher = GitRepositoryResetApplicationLauncher()
    application_launcher.launch_application()


if __name__ == "__main__":
    main()
