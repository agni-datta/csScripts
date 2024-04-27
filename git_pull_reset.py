"""
This Python script is designed to recursively find '.git' directories
under a specified root directory and perform 'git reset --hard' and
'git pull' commands within those directories.

Functions:
1. find_git_directories(root_dir: str) -> List[str]:
   - Recursively finds '.git' directories under the specified root directory.
   - Args:
       - root_dir (str): The root directory to start searching from.
   - Returns:
       - git_dirs (List[str]): List of absolute paths to directories containing '.git'.

2. git_reset_and_pull(directory: str) -> None:
   - Performs 'git reset --hard' and 'git pull' in the specified directory.
   - Args:
       - directory (str): The directory where the git commands should be executed.
   - Raises:
       - subprocess.CalledProcessError: If an error occurs while executing the git commands.

3. main() -> None:
   - Main function to execute git commands in '.git' directories found under the script's directory.
     - Finds the script's directory.
     - Finds '.git' directories under the script's directory.
     - Executes 'git reset --hard' and 'git pull' commands in each found '.git' directory.

Main Block:
- Calls the main() function if the script is executed as the main program.
"""

import os
import subprocess
from typing import List


def find_git_directories(root_dir: str) -> List[str]:
    """
    Recursively find .git directories under the specified root directory.

    Args:
    - root_dir (str): The root directory to start searching from.

    Returns:
    - git_dirs (List[str]): List of absolute paths to directories containing .git.
    """
    git_dirs = []
    for dirpath, _, _ in os.walk(root_dir):
        if ".git" in os.listdir(dirpath):
            git_dirs.append(os.path.abspath(dirpath))
    return git_dirs


def git_reset_and_pull(directory: str) -> None:
    """
    Perform git reset --hard and git pull in the specified directory.

    Args:
    - directory (str): The directory where the git commands should be executed.
    """
    try:
        subprocess.run(["git", "reset", "--hard"], cwd=directory, check=True)
        subprocess.run(["git", "pull"], cwd=directory, check=True)
        print(f"Git commands executed successfully in {directory}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing git commands in {directory}: {e}")


def main() -> None:
    """
    Main function to execute git commands in .git directories found under the script's directory.
    """
    script_directory = os.path.dirname(os.path.abspath(__file__))
    git_directories = find_git_directories(script_directory)
    for git_dir in git_directories:
        git_reset_and_pull(git_dir)


if __name__ == "__main__":
    main()
