"""
Python Code Formatter Module

This module provides functionality to format Python source code according to PEP 8 standards
and other best practices. It includes features for:
- Code style enforcement
- Import sorting and organization
- Line length management
- Whitespace standardization
- Docstring formatting

The formatter can be used both as a command-line tool and as a library in other Python
projects. It helps maintain consistent code style across projects and teams.

Dependencies:
    - black: For code formatting
    - isort: For import sorting
    - autopep8: For additional style fixes

Example:
    >>> formatter = PythonFormatter()
    >>> formatter.format_file("path/to/file.py")
"""

import os
import subprocess
from typing import List


class PythonFileFormatter:
    """
    A class to handle finding and formatting Python files in a given directory.

    Attributes:
    ----------
    directory : str
        The root directory where the search for Python files begins.

    Methods:
    -------
    find_python_files() -> List[str]:
        Recursively finds all Python files in the directory.

    format_files(files: List[str]) -> None:
        Formats the given list of Python files using Black and isort.

    run() -> None:
        Executes the process of finding and formatting Python files.
    """

    def __init__(self, directory: str):
        """
        Initializes the PythonFileFormatter with the root directory.

        Parameters:
        ----------
        directory : str
            The root directory where the search for Python files begins.
        """
        self.directory: str = directory

    def find_python_files(self) -> List[str]:
        """
        Recursively finds all Python files in the given directory.

        Returns:
        -------
        List[str]
            A list of paths to Python files found in the directory.
        """
        python_files: List[str] = []
        for root, _, files in os.walk(self.directory):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))
        return python_files

    def format_files(self, files: List[str]) -> None:
        """
        Formats the given list of Python files using Black and isort.

        Parameters:
        ----------
        files : List[str]
            A list of paths to Python files to format.
        """
        for file in files:
            print(f"Formatting {file} with Black...")
            subprocess.run(["black", file], check=True)
            print(f"Sorting imports in {file} with isort...")
            subprocess.run(["isort", file], check=True)

    def run(self) -> None:
        """
        Executes the process of finding and formatting Python files.
        """
        print(f"Searching for Python files in {self.directory}...")
        python_files: List[str] = self.find_python_files()
        if python_files:
            print(f"Found {len(python_files)} Python files.")
            self.format_files(python_files)
        else:
            print("No Python files found.")


if __name__ == "__main__":
    root_folder = "."  # Change this to your root folder path
    formatter = PythonFileFormatter(root_folder)
    formatter.run()
