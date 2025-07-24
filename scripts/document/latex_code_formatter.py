"""
LaTeX Code Formatter Module

This module provides functionality to format LaTeX source code for improved readability
and consistency. It includes features for:
- Indentation and whitespace normalization
- Section and environment alignment
- Comment formatting
- Batch processing of multiple files

The formatter can be used as a command-line tool or as a library in other Python projects.

Example:
    >>> formatter = LatexFormattingService()
    >>> formatter.format_single_file("input.tex")
"""

import argparse
import glob
import os
import subprocess
from typing import List, Optional, Tuple


class TextColumnFormattingService:
    """
    Service for formatting text into columns of specified width.
    """

    @staticmethod
    def format_text_into_columns(input_text: str, maximum_column_width: int) -> str:
        """
        Format text into lines based on a specified column width while preserving blank lines.

        Args:
            input_text: The input text to be broken into columns.
            maximum_column_width: The maximum number of characters per line.

        Returns:
            The text formatted into lines of specified column width.
        """
        text_lines = input_text.splitlines()
        formatted_lines = []

        for current_line in text_lines:
            if not current_line.strip():  # Preserve blank lines
                formatted_lines.append("")
                continue

            words_in_line = current_line.split()
            current_output_line = ""

            for word in words_in_line:
                # Check if adding the word would exceed the column width
                if len(current_output_line) + len(word) + 1 <= maximum_column_width:
                    if current_output_line:  # Add space if not the first word
                        current_output_line += " "
                    current_output_line += word
                else:
                    # Line would be too long, start a new line
                    formatted_lines.append(current_output_line)
                    current_output_line = word

            # Add the last line if there's content
            if current_output_line:
                formatted_lines.append(current_output_line)

        return "\n".join(formatted_lines)


class LatexIndentToolService:
    """
    Service for formatting LaTeX files using the latexindent tool.
    """

    @staticmethod
    def apply_latexindent_formatting(
        input_file_path: str, output_file_path: str
    ) -> None:
        """
        Format a LaTeX file using the latexindent tool.

        Args:
            input_file_path: The path to the input LaTeX file.
            output_file_path: The path to the output LaTeX file.

        Raises:
            FileNotFoundError: If the specified input LaTeX file does not exist.
            RuntimeError: If latexindent fails to run.
        """
        if not os.path.isfile(input_file_path):
            raise FileNotFoundError(f"The file {input_file_path} does not exist.")

        try:
            subprocess.run(
                ["latexindent", f"--outputfile={output_file_path}", input_file_path],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as command_error:
            raise RuntimeError(f"latexindent failed: {command_error}")


class FileBackupService:
    """
    Service for creating backups of files before modification.
    """

    @staticmethod
    def create_backup_file(file_path: str) -> str:
        """
        Create a backup of a file before modifying it.

        Args:
            file_path: The path to the file to back up.

        Returns:
            The path to the backup file.

        Raises:
            FileNotFoundError: If the specified file does not exist.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")

        backup_file_path = f"{file_path}.bak"
        os.rename(file_path, backup_file_path)
        return backup_file_path


class LatexFileProcessingService:
    """
    Service for processing LaTeX files by formatting text and applying indentation.
    """

    def __init__(self):
        """
        Initialize the LatexFileProcessingService with required services.
        """
        self.text_formatting_service = TextColumnFormattingService()
        self.indent_tool_service = LatexIndentToolService()
        self.backup_service = FileBackupService()

    def process_single_latex_file(self, file_path: str, column_width: int) -> None:
        """
        Process a single LaTeX file by formatting text and applying indentation.

        Args:
            file_path: The path to the LaTeX file.
            column_width: The maximum number of characters per line.

        Raises:
            FileNotFoundError: If the specified LaTeX file does not exist.
        """
        # Create backup
        backup_file_path = self.backup_service.create_backup_file(file_path)

        # Read content from backup
        with open(backup_file_path, "r") as file:
            file_content = file.read()

        # Format text into columns
        formatted_text = self.text_formatting_service.format_text_into_columns(
            file_content, column_width
        )

        # Write formatted text back to original file
        with open(file_path, "w") as file:
            file.write(formatted_text)

        # Apply latexindent formatting
        self.indent_tool_service.apply_latexindent_formatting(file_path, file_path)


class LatexBatchProcessingService:
    """
    Service for batch processing multiple LaTeX files.
    """

    def __init__(self, file_processing_service: LatexFileProcessingService):
        """
        Initialize the LatexBatchProcessingService.

        Args:
            file_processing_service: Service for processing individual LaTeX files.
        """
        self.file_processing_service = file_processing_service

    def process_all_latex_files_in_directory(
        self, directory_path: str, column_width: int
    ) -> Tuple[int, int]:
        """
        Process all LaTeX files in the specified directory and its subdirectories.

        Args:
            directory_path: The directory to search for LaTeX files.
            column_width: The maximum number of characters per line.

        Returns:
            A tuple containing (successful_count, failed_count).
        """
        latex_file_paths = glob.glob(
            os.path.join(directory_path, "**", "*.tex"), recursive=True
        )
        successful_count = 0
        failed_count = 0

        for latex_file_path in latex_file_paths:
            try:
                self.file_processing_service.process_single_latex_file(
                    latex_file_path, column_width
                )
                print(f"Processed {latex_file_path} successfully.")
                successful_count += 1
            except Exception as processing_error:
                print(
                    f"An error occurred while processing {latex_file_path}: {processing_error}"
                )
                failed_count += 1

        return successful_count, failed_count


class LatexFormattingService:
    """
    Main service for formatting LaTeX files.
    """

    def __init__(self):
        """
        Initialize the LatexFormattingService with required services.
        """
        self.file_processing_service = LatexFileProcessingService()
        self.batch_processing_service = LatexBatchProcessingService(
            self.file_processing_service
        )

    def format_single_file(self, file_path: str, column_width: int = 80) -> bool:
        """
        Format a single LaTeX file.

        Args:
            file_path: Path to the LaTeX file to format.
            column_width: Maximum number of characters per line.

        Returns:
            True if formatting was successful, False otherwise.
        """
        try:
            self.file_processing_service.process_single_latex_file(
                file_path, column_width
            )
            print(
                f"File processed successfully. A backup has been saved as {file_path}.bak"
            )
            return True
        except Exception as formatting_error:
            print(f"An error occurred: {formatting_error}")
            return False

    def format_all_files_in_directory(
        self, directory_path: str, column_width: int = 80
    ) -> Tuple[int, int]:
        """
        Format all LaTeX files in a directory.

        Args:
            directory_path: Path to the directory containing LaTeX files.
            column_width: Maximum number of characters per line.

        Returns:
            A tuple containing (successful_count, failed_count).
        """
        return self.batch_processing_service.process_all_latex_files_in_directory(
            directory_path, column_width
        )

    def execute_formatting_operation(
        self,
        file_path: Optional[str] = None,
        process_all: bool = False,
        column_width: int = 80,
    ) -> None:
        """
        Execute LaTeX formatting based on the provided arguments.

        Args:
            file_path: Path to a single LaTeX file to process.
            process_all: Flag to process all LaTeX files in the current directory and subdirectories.
            column_width: Maximum number of characters per line.
        """
        if process_all:
            successful, failed = self.format_all_files_in_directory(".", column_width)
            print(
                f"\nProcessing complete: {successful} files successful, {failed} files failed."
            )
        elif file_path:
            self.format_single_file(file_path, column_width)
        else:
            print(
                "Please specify either --file to process a single file or --all to process all .tex files in the directory."
            )


class CommandLineArgumentParser:
    """
    Parser for command-line arguments.
    """

    @staticmethod
    def parse_command_line_arguments():
        """
        Parse command-line arguments for the LaTeX formatter.

        Returns:
            The parsed command-line arguments.
        """
        parser = argparse.ArgumentParser(
            description="Process LaTeX files by formatting text into columns and applying indentation."
        )
        parser.add_argument("--file", help="Path to the LaTeX file to process.")
        parser.add_argument(
            "--all",
            action="store_true",
            help="Process all LaTeX files in the current directory and subdirectories.",
        )
        parser.add_argument(
            "--column-width",
            type=int,
            default=80,
            help="Maximum number of characters per line.",
        )
        return parser.parse_args()


class LatexFormattingApplicationLauncher:
    """
    Launcher for the LaTeX formatting application.
    """

    @staticmethod
    def launch_application() -> None:
        """
        Launch the LaTeX formatting application.
        """
        # Parse command-line arguments
        args = CommandLineArgumentParser.parse_command_line_arguments()

        # Create formatting service and execute operation
        formatting_service = LatexFormattingService()
        formatting_service.execute_formatting_operation(
            file_path=args.file, process_all=args.all, column_width=args.column_width
        )


def main() -> None:
    """
    Main entry point for the LaTeX code formatter script.
    """
    application_launcher = LatexFormattingApplicationLauncher()
    application_launcher.launch_application()


if __name__ == "__main__":
    main()
