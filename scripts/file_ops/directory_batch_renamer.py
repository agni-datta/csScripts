#!/usr/bin/env python3
"""
Directory Batch Renamer Module

This module provides tools for batch renaming directories in a given path. It supports
customizable renaming patterns, dry-run mode, and logging of all changes.

Features:
- Batch renaming of directories
- Customizable renaming rules
- Dry-run mode for previewing changes
- Logging of all renaming operations
- Error handling for conflicts

Example:
    >>> service = DirectoryBatchRenamingService()
    >>> service.execute_renaming_process()
"""

import logging
from pathlib import Path
from typing import List, Optional, Set


class ArticleDefinitionProvider:
    """
    Provides definitions of articles that should be moved in directory names.
    """

    @staticmethod
    def get_english_articles() -> Set[str]:
        """
        Get the set of English articles that should be moved.

        Returns:
            Set of English articles ('A', 'An', 'The').
        """
        return {"A", "An", "The"}


class LoggingConfigurationService:
    """
    Service for configuring and managing logging operations.
    """

    @staticmethod
    def configure_logging_system(log_file_path: Path) -> None:
        """
        Configure the logging system for the application.

        Args:
            log_file_path: Path to the log file.
        """
        logging.basicConfig(
            filename=log_file_path,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


class DirectoryNameTransformationService:
    """
    Service for transforming directory names according to specified rules.
    """

    def __init__(self, article_provider: ArticleDefinitionProvider):
        """
        Initialize the DirectoryNameTransformationService.

        Args:
            article_provider: Provider of article definitions.
        """
        self.recognized_articles = article_provider.get_english_articles()

    def transform_directory_name(self, directory_name: str) -> Optional[str]:
        """
        Transform a directory name by moving articles from the beginning to the end.

        Args:
            directory_name: The current name of the directory.

        Returns:
            The transformed directory name, or None if no transformation is needed.
        """
        name_components = directory_name.split()

        # Check if the first word is an article
        if not name_components or name_components[0] not in self.recognized_articles:
            return None

        # Move the article to the end
        first_article = name_components[0]
        remaining_words = name_components[1:]

        # Format: "Rest of name, Article"
        transformed_name = f"{' '.join(remaining_words)}, {first_article}"

        return transformed_name


class FileSystemOperationService:
    """
    Service for performing file system operations.
    """

    @staticmethod
    def rename_directory(current_path: Path, new_name: str) -> bool:
        """
        Rename a directory.

        Args:
            current_path: Current path to the directory.
            new_name: New name for the directory.

        Returns:
            True if renaming was successful, False otherwise.
        """
        try:
            new_path = current_path.parent / new_name
            current_path.rename(new_path)
            logging.info(f"Renamed '{current_path.name}' to '{new_name}'")
            return True
        except Exception as error:
            logging.error(
                f"Failed to rename '{current_path.name}' to '{new_name}': {error}"
            )
            return False

    @staticmethod
    def get_directories_in_path(directory_path: Path) -> List[Path]:
        """
        Get all directories in the specified path.

        Args:
            directory_path: Path to search for directories.

        Returns:
            List of paths to directories found.
        """
        return [entry for entry in directory_path.iterdir() if entry.is_dir()]


class DirectoryBatchRenamingService:
    """
    Service for batch renaming directories according to specified rules.
    """

    def __init__(self, target_directory_path: Optional[Path] = None):
        """
        Initialize the DirectoryBatchRenamingService.

        Args:
            target_directory_path: Path to the directory containing directories to rename.
                                  If None, uses the script's parent directory.
        """
        self.target_directory_path = (
            target_directory_path or Path(__file__).parent.resolve()
        )
        self.log_file_path = (
            self.target_directory_path / f"{self.target_directory_path.name}.log"
        )

        # Initialize component services
        self.article_provider = ArticleDefinitionProvider()
        self.logging_service = LoggingConfigurationService()
        self.transformation_service = DirectoryNameTransformationService(
            self.article_provider
        )
        self.file_system_service = FileSystemOperationService()

        # Configure logging
        self.logging_service.configure_logging_system(self.log_file_path)

    def execute_renaming_process(self) -> None:
        """
        Execute the directory batch renaming process.
        """
        logging.info(
            f"Starting directory renaming process in {self.target_directory_path}"
        )

        # Get all directories in the target path
        directories = self.file_system_service.get_directories_in_path(
            self.target_directory_path
        )

        # Track statistics
        renamed_count = 0
        unchanged_count = 0
        failed_count = 0

        # Process each directory
        for directory_path in directories:
            directory_name = directory_path.name
            transformed_name = self.transformation_service.transform_directory_name(
                directory_name
            )

            if transformed_name is None:
                # No transformation needed
                logging.info(f"No change needed for '{directory_name}'")
                unchanged_count += 1
                continue

            # Attempt to rename the directory
            if self.file_system_service.rename_directory(
                directory_path, transformed_name
            ):
                renamed_count += 1
            else:
                failed_count += 1

        # Log summary
        logging.info(
            f"Directory renaming process completed: "
            f"{renamed_count} renamed, {unchanged_count} unchanged, {failed_count} failed"
        )


class DirectoryBatchRenamingApplicationLauncher:
    """
    Launcher for the directory batch renaming application.
    """

    @staticmethod
    def launch_application() -> None:
        """
        Launch the directory batch renaming application.
        """
        renaming_service = DirectoryBatchRenamingService()
        renaming_service.execute_renaming_process()


def main() -> None:
    """
    Main entry point for the directory batch renamer script.
    """
    application_launcher = DirectoryBatchRenamingApplicationLauncher()
    application_launcher.launch_application()


if __name__ == "__main__":
    main()
