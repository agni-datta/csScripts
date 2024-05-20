import os
import subprocess
from typing import List


def find_python_files(directory: str) -> List[str]:
    """
    Recursively finds all Python files in the given directory.

    Args:
        directory (str): The root directory to start searching from.

    Returns:
        List[str]: A list of paths to Python files found in the directory.
    """
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def format_files(files: List[str]) -> None:
    """
    Formats the given list of Python files using Black and isort.

    Args:
        files (List[str]): A list of paths to Python files to format.
    """
    for file in files:
        print(f"Formatting {file} with Black...")
        subprocess.run(["black", file])
        print(f"Sorting imports in {file} with isort...")
        subprocess.run(["isort", file])


if __name__ == "__main__":
    root_folder = "."  # Change this to your root folder path
    print(f"Searching for Python files in {root_folder}...")
    python_files = find_python_files(root_folder)
    if python_files:
        print(f"Found {len(python_files)} Python files.")
        format_files(python_files)
    else:
        print("No Python files found.")
