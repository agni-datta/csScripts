#!/usr/bin/env python3
"""
Code Formatter Utility

This module provides functionality to format Python code according to Google's
Python style guide using isort and black.

Features:
- Automatic code formatting using industry-standard tools
- Support for Google's Python style guide
- Recursive directory processing
- Configurable line length and formatting options
- Detailed success/failure reporting

Example:
    >>> service = CodeFormattingService()
    >>> service.format_directory_recursively("/path/to/project")
"""

import os
import subprocess
from typing import Any, Dict, List, Optional, Tuple


class PythonFileDiscoveryService:
    """
    Service for discovering Python files in a directory structure.
    """

    @staticmethod
    def find_python_files_recursively(directory_path: str) -> List[str]:
        """
        Find all Python files in a directory and its subdirectories.

        Args:
            directory_path: Path to the directory to search.

        Returns:
            List of paths to Python files found.
        """
        discovered_python_file_paths = []

        for current_directory_path, _, file_names in os.walk(directory_path):
            for file_name in file_names:
                if file_name.endswith(".py"):
                    full_file_path = os.path.join(current_directory_path, file_name)
                    discovered_python_file_paths.append(full_file_path)

        return discovered_python_file_paths


class CommandExecutionService:
    """
    Service for executing external commands.
    """

    @staticmethod
    def execute_command(command_arguments: List[str]) -> Tuple[bool, str]:
        """
        Execute a command and capture its output.

        Args:
            command_arguments: Command to execute as a list of arguments.

        Returns:
            Tuple containing (success status, command output or error message).
        """
        try:
            execution_result = subprocess.run(
                command_arguments, check=True, capture_output=True, text=True
            )
            return True, execution_result.stdout
        except subprocess.CalledProcessError as command_error:
            return False, f"Error: {command_error.stderr}"


class FormattingToolConfigurationProvider:
    """
    Provider for formatting tool configurations.
    """

    def __init__(self, line_length: int = 88, multi_line_output: int = 3):
        """
        Initialize the FormattingToolConfigurationProvider.

        Args:
            line_length: Maximum line length for code formatting.
            multi_line_output: Import style for isort (3 is vertical).
        """
        self.line_length = line_length
        self.multi_line_output = multi_line_output

    def get_isort_command_arguments(self, file_path: str) -> List[str]:
        """
        Get the command arguments for running isort on a file.

        Args:
            file_path: Path to the file to format.

        Returns:
            List of command arguments for isort.
        """
        return [
            "isort",
            "--profile",
            "google",
            "--line-length",
            str(self.line_length),
            "--multi-line",
            str(self.multi_line_output),
            file_path,
        ]

    def get_black_command_arguments(self, file_path: str) -> List[str]:
        """
        Get the command arguments for running black on a file.

        Args:
            file_path: Path to the file to format.

        Returns:
            List of command arguments for black.
        """
        return ["black", "--line-length", str(self.line_length), file_path]


class FormattingResultTracker:
    """
    Tracker for formatting operation results.
    """

    def __init__(self):
        """
        Initialize the FormattingResultTracker.
        """
        self.formatting_results: List[Tuple[str, bool, str]] = []

    def add_result(self, file_path: str, success: bool, message: str) -> None:
        """
        Add a formatting result to the tracker.

        Args:
            file_path: Path to the formatted file.
            success: Whether formatting was successful.
            message: Success or error message.
        """
        self.formatting_results.append((file_path, success, message))

    def get_success_count(self) -> int:
        """
        Get the count of successful formatting operations.

        Returns:
            Number of successful formatting operations.
        """
        return sum(1 for _, success, _ in self.formatting_results if success)

    def get_total_count(self) -> int:
        """
        Get the total count of formatting operations.

        Returns:
            Total number of formatting operations.
        """
        return len(self.formatting_results)

    def get_failures(self) -> List[Tuple[str, str]]:
        """
        Get the list of failed formatting operations.

        Returns:
            List of tuples containing (file path, error message) for failed operations.
        """
        return [
            (path, message)
            for path, success, message in self.formatting_results
            if not success
        ]


class CodeFormattingService:
    """
    Service for formatting Python code according to Google's style guide.
    """

    def __init__(self, line_length: int = 88, multi_line_output: int = 3):
        """
        Initialize the CodeFormattingService.

        Args:
            line_length: Maximum line length for code formatting.
            multi_line_output: Import style for isort (3 is vertical).
        """
        self.configuration_provider = FormattingToolConfigurationProvider(
            line_length=line_length, multi_line_output=multi_line_output
        )
        self.command_execution_service = CommandExecutionService()
        self.file_discovery_service = PythonFileDiscoveryService()

    def format_single_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Format a single Python file using isort and black.

        Args:
            file_path: Path to the Python file to format.

        Returns:
            Tuple containing (success status, success or error message).
        """
        # Run isort for import sorting
        isort_command = self.configuration_provider.get_isort_command_arguments(
            file_path
        )
        isort_success, isort_output = self.command_execution_service.execute_command(
            isort_command
        )

        if not isort_success:
            return False, f"isort failed: {isort_output}"

        # Run black for code formatting
        black_command = self.configuration_provider.get_black_command_arguments(
            file_path
        )
        black_success, black_output = self.command_execution_service.execute_command(
            black_command
        )

        if not black_success:
            return False, f"black failed: {black_output}"

        return True, f"Successfully formatted {file_path}"

    def format_directory_recursively(
        self, directory_path: str
    ) -> FormattingResultTracker:
        """
        Format all Python files in a directory and its subdirectories.

        Args:
            directory_path: Path to the directory containing Python files.

        Returns:
            FormattingResultTracker containing the results of all formatting operations.
        """
        # Find all Python files in the directory
        python_file_paths = self.file_discovery_service.find_python_files_recursively(
            directory_path
        )

        # Create a result tracker
        result_tracker = FormattingResultTracker()

        # Format each file and track results
        for file_path in python_file_paths:
            success, message = self.format_single_file(file_path)
            result_tracker.add_result(file_path, success, message)

        return result_tracker


class ResultDisplayService:
    """
    Service for displaying formatting results.
    """

    @staticmethod
    def display_formatting_results(result_tracker: FormattingResultTracker) -> None:
        """
        Display the results of formatting operations.

        Args:
            result_tracker: Tracker containing formatting results.
        """
        # Display summary
        success_count = result_tracker.get_success_count()
        total_count = result_tracker.get_total_count()
        print(f"Formatted {success_count} of {total_count} files successfully.")

        # Display failures if any
        failures = result_tracker.get_failures()
        if failures:
            print("\nFailures:")
            for file_path, error_message in failures:
                print(f"  {file_path}: {error_message}")


class CommandLineArgumentParser:
    """
    Parser for command-line arguments.
    """

    @staticmethod
    def parse_command_line_arguments() -> Dict[str, Any]:
        """
        Parse command-line arguments for the code formatter.

        Returns:
            Dictionary containing parsed arguments.
        """
        import argparse

        parser = argparse.ArgumentParser(
            description="Format Python code using isort and black"
        )
        parser.add_argument(
            "directory",
            nargs="?",
            default=os.getcwd(),
            help="Directory containing Python files to format (default: current directory)",
        )
        parser.add_argument(
            "--line-length",
            type=int,
            default=88,
            help="Maximum line length (default: 88)",
        )

        args = parser.parse_args()

        return {"directory_path": args.directory, "line_length": args.line_length}


class CodeFormattingApplicationLauncher:
    """
    Launcher for the code formatting application.
    """

    @staticmethod
    def launch_application() -> None:
        """
        Launch the code formatting application.
        """
        # Parse command-line arguments
        arguments = CommandLineArgumentParser.parse_command_line_arguments()

        # Create formatting service
        formatting_service = CodeFormattingService(line_length=arguments["line_length"])

        # Format directory and get results
        result_tracker = formatting_service.format_directory_recursively(
            arguments["directory_path"]
        )

        # Display results
        ResultDisplayService.display_formatting_results(result_tracker)


def main() -> None:
    """
    Main entry point for the code formatter utility.
    """
    application_launcher = CodeFormattingApplicationLauncher()
    application_launcher.launch_application()


if __name__ == "__main__":
    main()
