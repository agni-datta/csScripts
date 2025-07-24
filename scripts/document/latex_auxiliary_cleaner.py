#!/usr/bin/env python3
"""
LaTeX Auxiliary File Cleaner Module

This module provides functionality to clean up LaTeX auxiliary files that are
generated during the compilation process. It can recursively search directories
and delete files with specified extensions.

Example:
    >>> cleaner = LatexAuxiliaryFileCleaningService()
    >>> cleaner.execute_cleaning_process("/path/to/latex/project")
"""

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Optional


class LoggingConfigurationService:
    """
    Manages logging configuration and operations for the LaTeX cleaner.

    This class handles setting up logging, writing log messages, and
    maintaining the log file for tracking file deletion operations.
    """

    def __init__(self, log_directory_path: Optional[str] = None):
        """
        Initialize the LoggingConfigurationService with a log directory.

        Args:
            log_directory_path: Directory where log files will be stored.
                               If None, logs will be stored in the script's directory.
        """
        self.log_directory_path = log_directory_path or os.path.dirname(__file__)
        self.log_file_path = self._generate_timestamped_log_file_path()
        self._configure_logging_system()

    def _generate_timestamped_log_file_path(self) -> str:
        """
        Generate a timestamped log file path.

        Returns:
            Path to the log file with timestamp.
        """
        current_timestamp = datetime.now().strftime("%Y-%m-%d")
        log_filename = f"latex_auxiliary_files_deleted_{current_timestamp}.log"
        return os.path.join(self.log_directory_path, log_filename)

    def _configure_logging_system(self) -> None:
        """
        Configure the logging system with appropriate format and level.
        """
        logging.basicConfig(
            filename=self.log_file_path,
            level=logging.INFO,
            format="%(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def log_successful_file_deletion(
        self, deleted_file_path: str, containing_directory_path: str
    ) -> None:
        """
        Log a successful file deletion.

        Args:
            deleted_file_path: Path to the deleted file.
            containing_directory_path: Directory containing the deleted file.
        """
        logging.info(
            "Deleted: %s (from directory: %s)",
            deleted_file_path,
            containing_directory_path,
        )

    def log_file_deletion_error(
        self, problematic_file_path: str, encountered_error: Exception
    ) -> None:
        """
        Log an error that occurred during file deletion.

        Args:
            problematic_file_path: Path to the file that could not be deleted.
            encountered_error: Exception that occurred during deletion.
        """
        logging.error(
            "Error deleting file %s: %s", problematic_file_path, encountered_error
        )


class FileOperationsService:
    """
    Manages file operations for the LaTeX cleaner.

    This class handles file deletion operations and directory traversal.
    """

    def __init__(self, logging_service: LoggingConfigurationService):
        """
        Initialize the FileOperationsService with a logging service.

        Args:
            logging_service: Service for logging operations.
        """
        self.logging_service = logging_service

    def delete_individual_file(
        self, target_file_path: str, containing_directory_path: str
    ) -> None:
        """
        Delete a single file and log the result.

        Args:
            target_file_path: Path to the file to delete.
            containing_directory_path: Directory containing the file.
        """
        try:
            os.remove(target_file_path)
            self.logging_service.log_successful_file_deletion(
                target_file_path, containing_directory_path
            )
        except FileNotFoundError as file_not_found_error:
            self.logging_service.log_file_deletion_error(
                target_file_path, file_not_found_error
            )
        except PermissionError as permission_error:
            self.logging_service.log_file_deletion_error(
                target_file_path, permission_error
            )
        except OSError as os_error:
            self.logging_service.log_file_deletion_error(target_file_path, os_error)

    def delete_matching_files_recursively(
        self, target_directory_path: str, target_file_extensions: List[str]
    ) -> None:
        """
        Recursively delete files with specified extensions in a directory.

        Args:
            target_directory_path: Directory to search for files.
            target_file_extensions: List of file extensions to delete.
        """
        # Use ThreadPoolExecutor for parallel file deletion
        with ThreadPoolExecutor(max_workers=18) as parallel_executor:
            for current_directory_path, _, file_names_list in os.walk(
                target_directory_path
            ):
                for current_file_name in file_names_list:
                    if any(
                        current_file_name.endswith(extension)
                        for extension in target_file_extensions
                    ):
                        complete_file_path = os.path.join(
                            current_directory_path, current_file_name
                        )
                        parallel_executor.submit(
                            self.delete_individual_file,
                            complete_file_path,
                            current_directory_path,
                        )


class LatexExtensionProvider:
    """
    Provides the list of LaTeX auxiliary file extensions.
    """

    @staticmethod
    def get_default_latex_auxiliary_extensions() -> List[str]:
        """
        Get the default list of LaTeX auxiliary file extensions.

        Returns:
            List of common LaTeX auxiliary file extensions.
        """
        return [
            ".4ct",
            ".4tc",
            ".acn",
            ".acr",
            ".alg",
            ".aux",
            ".auxlock",
            ".backup",
            ".backup1",
            ".backup2",
            ".bak",
            ".bbl",
            ".bcf",
            ".bit",
            ".blg",
            ".brf",
            ".cb",
            ".cb2",
            ".def",
            ".dep",
            ".drv",
            ".dvi",
            ".enc",
            ".fdb_latexmk",
            ".fls",
            ".fmt",
            ".fot",
            ".glg",
            ".glo",
            ".gls",
            ".glsdefs",
            ".glx",
            ".gxg",
            ".gxs",
            ".htf",
            ".idv",
            ".idx",
            ".ilg",
            ".ind",
            ".ist",
            ".lg",
            ".loa",
            ".lof",
            ".lot",
            ".ltx",
            ".md5",
            ".mkii",
            ".mkiv",
            ".mkvi",
            ".mp",
            ".mpx",
            ".nav",
            ".out",
            ".pag",
            ".phps",
            ".pictex",
            ".plt",
            ".prv",
            ".ptc",
            ".run",
            ".run.xml",
            ".sav",
            ".snm",
            ".svn",
            ".swp",
            ".synctex(busy)",
            ".synctex(busy)+",
            ".synctex.gz",
            ".synctex.gz(busy)",
            ".synctex.gz(busy)+",
            ".tct",
            ".temp",
            ".tmp",
            ".toc",
            ".tui",
            ".tyi",
            ".upa",
            ".upb",
            ".url",
            ".vrb",
            ".xdv",
            ".xdy",
            ".xml",
            "main.synctex.gz",
        ]


class LatexAuxiliaryFileCleaningService:
    """
    Main service for cleaning LaTeX auxiliary files.

    This class orchestrates the cleaning process, managing both logging
    and file operations to remove LaTeX auxiliary files from directories.
    """

    def __init__(self, log_directory_path: Optional[str] = None):
        """
        Initialize the LatexAuxiliaryFileCleaningService.

        Args:
            log_directory_path: Directory for storing log files.
                               If None, logs will be stored in the script's directory.
        """
        self.logging_service = LoggingConfigurationService(log_directory_path)
        self.file_operations_service = FileOperationsService(self.logging_service)
        self.extension_provider = LatexExtensionProvider()

    def execute_cleaning_process(
        self,
        target_directory_path: Optional[str] = None,
        file_extensions_to_delete: Optional[List[str]] = None,
    ) -> None:
        """
        Execute the LaTeX auxiliary file cleaning process.

        Args:
            target_directory_path: Directory to clean. If None, uses current directory.
            file_extensions_to_delete: File extensions to delete. If None, uses defaults.
        """
        # Use current directory if none specified
        effective_target_directory = target_directory_path or os.getcwd()

        # Use default extensions if none specified
        effective_file_extensions = (
            file_extensions_to_delete
            or self.extension_provider.get_default_latex_auxiliary_extensions()
        )

        # Clean the specified directory
        self.file_operations_service.delete_matching_files_recursively(
            effective_target_directory, effective_file_extensions
        )

        # Also clean the script directory if different from target
        script_directory_path = os.path.dirname(__file__)
        if effective_target_directory != script_directory_path:
            self.file_operations_service.delete_matching_files_recursively(
                script_directory_path, effective_file_extensions
            )


class CleaningApplicationLauncher:
    """
    Launches the LaTeX auxiliary file cleaning application.
    """

    @staticmethod
    def display_start_message() -> None:
        """Display the start message for the cleaning process."""
        print("Starting LaTeX auxiliary file cleaning process...")

    @staticmethod
    def display_completion_message(log_file_path: str) -> None:
        """Display the completion message for the cleaning process.

        Args:
            log_file_path: Path to the log file.
        """
        print("LaTeX auxiliary file cleaning process completed.")
        print(f"Log file created at: {log_file_path}")

    def launch_cleaning_application(self) -> None:
        """Launch the LaTeX auxiliary file cleaning application."""
        self.display_start_message()

        cleaning_service = LatexAuxiliaryFileCleaningService()
        cleaning_service.execute_cleaning_process()

        self.display_completion_message(cleaning_service.logging_service.log_file_path)


def main() -> None:
    """
    Main entry point for the LaTeX auxiliary file cleaner.

    This function creates a CleaningApplicationLauncher and launches the application.
    """
    application_launcher = CleaningApplicationLauncher()
    application_launcher.launch_cleaning_application()


if __name__ == "__main__":
    main()
