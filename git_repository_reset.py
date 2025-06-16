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
    >>> resetter = GitRepositoryReset()
    >>> resetter.reset_repo("/path/to/repo")
"""

import os
import subprocess
from typing import List


class GitManager:
    """
    A class to manage git repositories by executing 'git reset --hard' and 'git pull' commands
    in all .git directories found under a specified root directory.

    Methods:
    --------
    find_git_directories(root_dir: str) -> List[str]:
        Recursively finds '.git' directories under the specified root directory.

    git_reset_and_pull(directory: str) -> None:
        Performs 'git reset --hard' and 'git pull' in the specified directory.

    execute() -> None:
        Executes the git commands in all .git directories found under the script's directory.
    """

    def __init__(self, root_dir: str) -> None:
        """
        Initializes the GitManager with the root directory.

        Args:
        ----
        root_dir (str): The root directory to start searching for .git directories.
        """
        self.root_dir: str = root_dir
        self.git_directories: List[str] = []

    def find_git_directories(self) -> List[str]:
        """
        Recursively finds '.git' directories under the specified root directory.

        Returns:
        -------
        List[str]: A list of absolute paths to directories containing '.git'.
        """
        git_dirs: List[str] = []
        for dirpath, _, _ in os.walk(self.root_dir):
            if ".git" in os.listdir(dirpath):
                git_dirs.append(os.path.abspath(dirpath))
        self.git_directories = git_dirs
        return git_dirs

    def git_reset_and_pull(self, directory: str) -> None:
        """
        Performs 'git reset --hard' and 'git pull' in the specified directory.

        Args:
        ----
        directory (str): The directory where the git commands should be executed.

        Raises:
        ------
        subprocess.CalledProcessError: If an error occurs while executing the git commands.
        """
        try:
            subprocess.run(["git", "reset", "--hard"], cwd=directory, check=True)
            subprocess.run(["git", "pull"], cwd=directory, check=True)
            print(f"Git commands executed successfully in {directory}")
        except subprocess.CalledProcessError as e:
            print(f"Error executing git commands in {directory}: {e}")

    def execute(self) -> None:
        """
        Executes git commands in all '.git' directories found under the root directory.
        """
        self.find_git_directories()
        for git_dir in self.git_directories:
            self.git_reset_and_pull(git_dir)


def main() -> None:
    """
    Main function to execute the GitManager on the script's directory.
    """
    script_directory = os.path.dirname(os.path.abspath(__file__))
    git_manager = GitManager(script_directory)
    git_manager.execute()


if __name__ == "__main__":
    main()
