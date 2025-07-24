#!/usr/bin/env python3
"""
File Batch Renamer Module

This module provides tools for batch renaming files in a directory. It supports
customizable renaming patterns, dry-run mode, and logging of all changes.

Features:
- Batch renaming of files
- Customizable renaming rules
- Dry-run mode for previewing changes
- Logging of all renaming operations
- Error handling for file conflicts

Example:
    >>> renamer = FileBatchRenamingOrchestrator(file_extension=".txt")
    >>> renamer.execute_renaming_operation()
"""

import datetime
import os
from typing import Dict, List, Optional, Tuple


class FileSystemOperationsService:
    """
    Handles file system operations for the batch renamer.

    This class provides methods for interacting with the file system,
    including listing files and performing rename operations.
    """

    @staticmethod
    def retrieve_files_with_extension_from_directory(
        target_directory_path: str, target_file_extension: str
    ) -> List[str]:
        """
        Retrieve files with the specified extension from a directory.

        Args:
            target_directory_path: Path to the directory to search.
            target_file_extension: File extension to filter by (including dot).

        Returns:
            List of filenames with the specified extension, sorted alphabetically.
        """
        # Ensure extension starts with a dot
        normalized_file_extension = target_file_extension
        if not normalized_file_extension.startswith("."):
            normalized_file_extension = f".{normalized_file_extension}"

        # Get all files with the specified extension
        matching_file_list = [
            filename
            for filename in os.listdir(target_directory_path)
            if filename.endswith(normalized_file_extension)
        ]

        # Sort files alphabetically
        matching_file_list.sort()

        return matching_file_list

    @staticmethod
    def rename_file_with_error_handling(
        containing_directory_path: str, original_filename: str, target_filename: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Rename a file and handle potential errors.

        Args:
            containing_directory_path: Directory containing the file.
            original_filename: Current filename.
            target_filename: New filename.

        Returns:
            Tuple of (success, error_message).
        """
        original_file_path = os.path.join(containing_directory_path, original_filename)
        target_file_path = os.path.join(containing_directory_path, target_filename)

        try:
            os.rename(original_file_path, target_file_path)
            return True, None
        except FileNotFoundError:
            return False, f"File not found: {original_file_path}"
        except PermissionError:
            return False, f"Permission denied: {original_file_path}"
        except FileExistsError:
            return False, f"Destination file already exists: {target_file_path}"
        except OSError as operating_system_error:
            return False, f"OS error: {operating_system_error}"


class RenameOperationLoggingService:
    """
    Manages logging for file rename operations.

    This class handles creating and writing to log files to track
    all renaming operations performed by the batch renamer.
    """

    def __init__(self, log_directory_path: str):
        """
        Initialize the RenameOperationLoggingService.

        Args:
            log_directory_path: Directory where log files will be stored.
        """
        self.log_directory_path = log_directory_path
        self.log_file_path = self._generate_timestamped_log_file_path()

    def _generate_timestamped_log_file_path(self) -> str:
        """
        Generate a timestamped log file path.

        Returns:
            Path to the log file.
        """
        current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = f"file_rename_operations_{current_timestamp}.log"
        return os.path.join(self.log_directory_path, log_filename)

    def log_rename_operation_result(
        self,
        original_filename: str,
        new_filename: str,
        operation_success: bool,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Log a rename operation to the log file.

        Args:
            original_filename: Original filename.
            new_filename: New filename.
            operation_success: Whether the operation succeeded.
            error_message: Error message if the operation failed.
        """
        current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if operation_success:
            log_entry = f"{current_timestamp} - SUCCESS: Renamed '{original_filename}' to '{new_filename}'\n"
        else:
            log_entry = f"{current_timestamp} - FAILED: Could not rename '{original_filename}' to '{new_filename}'. Error: {error_message}\n"

        with open(self.log_file_path, "a") as log_file:
            log_file.write(log_entry)

    def log_operation_summary(
        self,
        total_processed_files: int,
        successful_rename_count: int,
        failed_rename_count: int,
    ) -> None:
        """
        Log a summary of the rename operations.

        Args:
            total_processed_files: Total number of files processed.
            successful_rename_count: Number of successful renames.
            failed_rename_count: Number of failed renames.
        """
        current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary_text = (
            f"\n{current_timestamp} - SUMMARY:\n"
            f"  Total files processed: {total_processed_files}\n"
            f"  Successful renames: {successful_rename_count}\n"
            f"  Failed renames: {failed_rename_count}\n"
        )

        with open(self.log_file_path, "a") as log_file:
            log_file.write(summary_text)


class FilenameGenerationService:
    """
    Service for generating new filenames based on specified patterns.
    """

    def __init__(self, file_extension: str):
        """
        Initialize the FilenameGenerationService.

        Args:
            file_extension: File extension to use for generated filenames.
        """
        # Normalize file extension to include dot
        self.file_extension = file_extension
        if not self.file_extension.startswith("."):
            self.file_extension = f".{self.file_extension}"

    def generate_sequential_filename(self, sequence_number: int) -> str:
        """
        Generate a new filename based on a sequential number.

        Args:
            sequence_number: Sequential number for the new filename.

        Returns:
            New filename with extension.
        """
        return f"{sequence_number}{self.file_extension}"


class FileBatchRenamingOrchestrator:
    """
    Main orchestrator for batch renaming files.

    This class orchestrates the renaming process, managing both file system
    operations and logging to provide a complete batch renaming solution.
    """

    def __init__(
        self,
        file_extension: str,
        target_directory_path: Optional[str] = None,
        dry_run_mode: bool = False,
    ):
        """
        Initialize the FileBatchRenamingOrchestrator.

        Args:
            file_extension: Extension of files to rename (with or without dot).
            target_directory_path: Directory containing files to rename.
                                  If None, uses the current directory.
            dry_run_mode: If True, simulates renaming without making changes.
        """
        # Set target directory
        self.target_directory_path = target_directory_path or os.getcwd()

        # Set dry run mode
        self.dry_run_mode = dry_run_mode

        # Initialize components
        self.filename_generation_service = FilenameGenerationService(file_extension)
        self.file_system_service = FileSystemOperationsService()
        self.operation_logging_service = RenameOperationLoggingService(
            self.target_directory_path
        )

    def _generate_rename_operation_plan(self) -> Dict[str, str]:
        """
        Generate a plan of rename operations without executing them.

        Returns:
            Dictionary mapping old filenames to new filenames.
        """
        files_to_rename_list = (
            self.file_system_service.retrieve_files_with_extension_from_directory(
                self.target_directory_path,
                self.filename_generation_service.file_extension,
            )
        )

        rename_operations_mapping = {}
        for file_index, original_filename in enumerate(files_to_rename_list, start=1):
            new_filename = (
                self.filename_generation_service.generate_sequential_filename(
                    file_index
                )
            )
            rename_operations_mapping[original_filename] = new_filename

        return rename_operations_mapping

    def execute_renaming_operation(self) -> Tuple[int, int, int]:
        """
        Execute the batch renaming operation.

        Returns:
            Tuple of (total_files, successful_renames, failed_renames).
        """
        # Get files to rename
        rename_operations_plan = self._generate_rename_operation_plan()

        # Track statistics
        total_file_count = len(rename_operations_plan)
        successful_rename_count = 0
        failed_rename_count = 0

        # Execute rename operations
        for original_filename, target_filename in rename_operations_plan.items():
            # Skip if old and new names are the same
            if original_filename == target_filename:
                continue

            # Perform rename operation (or simulate in dry run mode)
            if self.dry_run_mode:
                operation_success, error_message = True, None
                print(
                    f"[DRY RUN] Would rename '{original_filename}' to '{target_filename}'"
                )
            else:
                operation_success, error_message = (
                    self.file_system_service.rename_file_with_error_handling(
                        self.target_directory_path, original_filename, target_filename
                    )
                )

            # Log the operation
            self.operation_logging_service.log_rename_operation_result(
                original_filename, target_filename, operation_success, error_message
            )

            # Update statistics
            if operation_success:
                successful_rename_count += 1
            else:
                failed_rename_count += 1
                print(f"Error renaming '{original_filename}': {error_message}")

        # Log summary
        self.operation_logging_service.log_operation_summary(
            total_file_count, successful_rename_count, failed_rename_count
        )

        return total_file_count, successful_rename_count, failed_rename_count


class UserInteractionService:
    """
    Handles user interaction for the batch renamer application.
    """

    @staticmethod
    def display_application_header() -> None:
        """Display the application header."""
        print("File Batch Renamer")
        print("-----------------")

    @staticmethod
    def get_file_extension_from_user() -> str:
        """Get file extension from user input.

        Returns:
            File extension entered by the user.
        """
        return input("Enter the file extension (e.g., '.txt'): ").strip()

    @staticmethod
    def get_dry_run_preference_from_user() -> bool:
        """Get dry run preference from user input.

        Returns:
            True if dry run mode is requested, False otherwise.
        """
        dry_run_response = (
            input("Perform a dry run without making changes? (y/N): ").strip().lower()
        )
        return dry_run_response == "y"

    @staticmethod
    def display_operation_summary(
        total_files: int,
        successful_renames: int,
        failed_renames: int,
        log_file_path: str,
    ) -> None:
        """Display a summary of the rename operation.

        Args:
            total_files: Total number of files processed.
            successful_renames: Number of successful renames.
            failed_renames: Number of failed renames.
            log_file_path: Path to the log file.
        """
        print("\nRename Operation Summary:")
        print(f"  Total files processed: {total_files}")
        print(f"  Successful renames: {successful_renames}")
        print(f"  Failed renames: {failed_renames}")
        print(f"\nLog file created at: {log_file_path}")


class BatchRenamerApplicationLauncher:
    """
    Launches the batch renamer application.
    """

    def __init__(self):
        """Initialize the BatchRenamerApplicationLauncher."""
        self.user_interaction_service = UserInteractionService()

    def launch_application(self) -> None:
        """Launch the batch renamer application."""
        self.user_interaction_service.display_application_header()

        # Get user inputs
        file_extension = self.user_interaction_service.get_file_extension_from_user()
        dry_run_mode = self.user_interaction_service.get_dry_run_preference_from_user()

        # Create orchestrator and execute operation
        renaming_orchestrator = FileBatchRenamingOrchestrator(
            file_extension=file_extension, dry_run_mode=dry_run_mode
        )

        print(
            f"\nProcessing files with extension '{renaming_orchestrator.filename_generation_service.file_extension}'..."
        )
        total_files, successful_renames, failed_renames = (
            renaming_orchestrator.execute_renaming_operation()
        )

        # Display summary
        self.user_interaction_service.display_operation_summary(
            total_files,
            successful_renames,
            failed_renames,
            renaming_orchestrator.operation_logging_service.log_file_path,
        )


def main() -> None:
    """
    Main entry point for the file batch renamer script.

    This function creates a BatchRenamerApplicationLauncher and launches the application.
    """
    application_launcher = BatchRenamerApplicationLauncher()
    application_launcher.launch_application()


if __name__ == "__main__":
    main()
