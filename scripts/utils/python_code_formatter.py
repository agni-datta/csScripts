#!/usr/bin/env python3
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
    >>> formatter = PythonCodeFormattingService()
    >>> formatter.format_file("path/to/file.py")
"""

import os
import subprocess
from typing import List, Type


class PythonFileDiscoveryService:
    """
    Service for discovering Python files in a directory structure.

    This service provides methods to recursively search for Python files
    within a specified directory hierarchy.
    """

    def __init__(self, root_directory_path: str) -> None:
        """
        Initialize the PythonFileDiscoveryService with a root directory.

        Args:
            root_directory_path: The root directory where the search for Python files begins.
        """
        self.root_directory_path: str = root_directory_path

    def discover_python_files_recursively(self) -> List[str]:
        """
        Recursively discover all Python files in the given directory.

        Returns:
            List[str]: A list of absolute paths to Python files found in the directory.
        """
        discovered_python_file_paths: List[str] = []

        for current_directory_path, _, file_names in os.walk(self.root_directory_path):
            for current_file_name in file_names:
                if current_file_name.endswith(".py"):
                    absolute_file_path: str = os.path.join(
                        current_directory_path, current_file_name
                    )
                    discovered_python_file_paths.append(absolute_file_path)

        return discovered_python_file_paths


class CodeFormattingToolExecutor:
    """
    Executes code formatting tools on Python files.

    This class handles the execution of external formatting tools like Black and isort
    to format Python source code according to style guidelines.
    """

    @staticmethod
    def print_success(message: str) -> None:
        print(message)

    @staticmethod
    def print_warning(message: str) -> None:
        print(message)

    @staticmethod
    def print_error(message: str) -> None:
        print(message)

    @staticmethod
    def apply_black_formatter(target_file_path: str) -> bool:
        """
        Apply the Black code formatter to a Python file.

        Args:
            target_file_path: Path to the Python file to format.

        Returns:
            bool: True if formatting was successful, False otherwise.
        """
        try:
            subprocess.run(
                ["black", target_file_path],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"{target_file_path}  ✓ black")
            return True
        except subprocess.CalledProcessError:
            CodeFormattingToolExecutor.print_error(f"{target_file_path}  ✗ black")
            return False
        except FileNotFoundError:
            CodeFormattingToolExecutor.print_error(
                "Error: Black formatter not found. Please install it with 'pip install black'"
            )
            return False

    @staticmethod
    def apply_isort_formatter(target_file_path: str) -> bool:
        """
        Apply the isort import sorter to a Python file.

        Args:
            target_file_path: Path to the Python file to format.

        Returns:
            bool: True if import sorting was successful, False otherwise.
        """
        try:
            subprocess.run(
                ["isort", target_file_path],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"{target_file_path}  ✓ isort")
            return True
        except subprocess.CalledProcessError:
            CodeFormattingToolExecutor.print_error(f"{target_file_path}  ✗ isort")
            return False
        except FileNotFoundError:
            CodeFormattingToolExecutor.print_error(
                "Error: isort not found. Please install it with 'pip install isort'"
            )
            return False


class PythonCodeFormattingService:
    """
    Service for formatting Python code files.

    This service orchestrates the process of discovering Python files
    and applying code formatting tools to them.

    Attributes:
        root_directory_path: The root directory where the search for Python files begins.
        file_discovery_service: Service for discovering Python files.
        formatting_tool_executor: Executor for code formatting tools.
    """

    def __init__(self, root_directory_path: str) -> None:
        """
        Initialize the PythonCodeFormattingService with a root directory.

        Args:
            root_directory_path: The root directory where the search for Python files begins.
        """
        self.root_directory_path: str = root_directory_path
        self.file_discovery_service: PythonFileDiscoveryService = (
            PythonFileDiscoveryService(root_directory_path)
        )
        self.formatting_tool_executor: Type[CodeFormattingToolExecutor] = (
            CodeFormattingToolExecutor
        )

    def format_multiple_files(self, target_file_paths: List[str]) -> None:
        """
        Format multiple Python files using Black and isort.

        Args:
            target_file_paths: List of paths to Python files to format.
        """
        successful_format_count: int = 0
        failed_format_count: int = 0

        for current_file_path in target_file_paths:
            black_success: bool = self.formatting_tool_executor.apply_black_formatter(
                current_file_path
            )
            isort_success: bool = self.formatting_tool_executor.apply_isort_formatter(
                current_file_path
            )

            if black_success and isort_success:
                successful_format_count += 1
            else:
                failed_format_count += 1

        if successful_format_count > 0:
            print(
                f"\nFormatting complete: {successful_format_count} files formatted successfully."
            )
        if failed_format_count > 0:
            print(f"{failed_format_count} files had formatting errors.")

    def execute_formatting_process(self) -> None:
        """
        Execute the complete Python code formatting process.

        This method discovers Python files in the specified directory
        and applies formatting tools to them.
        """
        print(f"Searching for Python files in {self.root_directory_path}...")
        discovered_python_files: List[str] = (
            self.file_discovery_service.discover_python_files_recursively()
        )

        if discovered_python_files:
            print(f"Found {len(discovered_python_files)} Python files.")
            self.format_multiple_files(discovered_python_files)
        else:
            CodeFormattingToolExecutor.print_warning("No Python files found.")


class FormattingApplicationLauncher:
    """
    Launches the Python code formatting application.
    """

    @staticmethod
    def launch_formatting_application(target_directory_path: str = ".") -> None:
        """
        Launch the Python code formatting application.

        Args:
            target_directory_path: Directory containing Python files to format.
                                   Defaults to the current directory.
        """
        formatting_service: PythonCodeFormattingService = PythonCodeFormattingService(
            target_directory_path
        )
        formatting_service.execute_formatting_process()


def main() -> None:
    """
    Main entry point for the Python code formatter script.

    This function creates a FormattingApplicationLauncher and launches the application.
    """
    target_directory_path: str = (
        "."  # Change this to your target directory path if needed
    )
    application_launcher: FormattingApplicationLauncher = (
        FormattingApplicationLauncher()
    )
    application_launcher.launch_formatting_application(target_directory_path)


if __name__ == "__main__":
    main()
