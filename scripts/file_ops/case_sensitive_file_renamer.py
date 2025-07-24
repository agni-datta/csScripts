"""
Case-Sensitive File Renamer Module

This module provides advanced batch renaming capabilities for files, with special handling
for case sensitivity. It is useful for renaming files in bulk where case changes matter
(e.g., on case-sensitive filesystems or for codebase normalization).

Features:
- Batch renaming with case sensitivity
- Customizable renaming patterns
- Dry-run and preview support
- Logging of renaming operations
- Conflict and error handling

Example:
    >>> service = FilenameCaseTransformationService()
    >>> service.execute_transformation_process()
"""

import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Protocol, Type

from titlecase import titlecase


class FilenameTransformationStrategy(Protocol):
    """Protocol defining the interface for filename transformation strategies."""

    @staticmethod
    def transform_filename(filename: str) -> str:
        """Transform a filename according to the strategy."""
        ...


class UppercaseTransformationStrategy:
    """Strategy for transforming filenames to uppercase."""

    @staticmethod
    def transform_filename(filename: str) -> str:
        """Transform the provided filename to uppercase.

        Args:
            filename: The name of the file to transform.

        Returns:
            The filename transformed to uppercase.
        """
        name_part, extension_part = os.path.splitext(filename)
        return f"{name_part.upper()}{extension_part}"


class LowercaseTransformationStrategy:
    """Strategy for transforming filenames to lowercase."""

    @staticmethod
    def transform_filename(filename: str) -> str:
        """Transform the provided filename to lowercase.

        Args:
            filename: The name of the file to transform.

        Returns:
            The filename transformed to lowercase.
        """
        name_part, extension_part = os.path.splitext(filename)
        return f"{name_part.lower()}{extension_part}"


class TitlecaseTransformationStrategy:
    """Strategy for transforming filenames to title case."""

    @staticmethod
    def transform_filename(filename: str) -> str:
        """Transform the provided filename to title case.

        Args:
            filename: The name of the file to transform.

        Returns:
            The filename transformed to title case.
        """
        name_part, extension_part = os.path.splitext(filename)
        title_cased_name_part = titlecase(name_part)
        return f"{title_cased_name_part}{extension_part}"


class UnderscoreTransformationStrategy:
    """Strategy for replacing spaces in filenames with underscores."""

    @staticmethod
    def transform_filename(filename: str) -> str:
        """Replace spaces with underscores in the provided filename.

        Args:
            filename: The name of the file to transform.

        Returns:
            The filename with spaces replaced by underscores.
        """
        name_part, extension_part = os.path.splitext(filename)
        return f"{name_part.replace(' ', '_')}{extension_part}"


class SpaceTransformationStrategy:
    """Strategy for replacing underscores in filenames with spaces."""

    @staticmethod
    def transform_filename(filename: str) -> str:
        """Replace underscores with spaces in the provided filename.

        Args:
            filename: The name of the file to transform.

        Returns:
            The filename with underscores replaced by spaces.
        """
        name_part, extension_part = os.path.splitext(filename)
        return f"{name_part.replace('_', ' ')}{extension_part}"


class LoggingConfigurationService:
    """Service for configuring and managing logging operations."""

    @staticmethod
    def configure_logging_system() -> None:
        """Configure the logging system for the application.

        This method sets up logging to write to a date-stamped log file,
        capturing the time of each rename operation.
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_filename = f"{current_date}.log"

        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            format="%(asctime)s - %(message)s",
        )


class UserInputCollectionService:
    """Service for collecting and validating user input."""

    @staticmethod
    def collect_transformation_choice() -> str:
        """Collect the user's choice of filename transformation.

        Returns:
            The chosen transformation option code.

        Raises:
            SystemExit: If the user provides invalid input.
        """
        valid_choice_options = ["l", "u", "t", "e", "s"]
        choice_prompt = (
            "Enter 'l' for lowercase, 'u' for uppercase, 't' for title case, "
            "'e' for underscores, or 's' for spaces: "
        )

        user_choice = input(choice_prompt).strip().lower()

        if user_choice not in valid_choice_options:
            print(
                f"Invalid input. Please enter one of {', '.join(valid_choice_options)}."
            )
            sys.exit("Exiting the program due to invalid input.")

        return user_choice

    @staticmethod
    def collect_file_extensions() -> List[str]:
        """Collect file extensions to be processed.

        Returns:
            A list of file extensions to process.

        Raises:
            SystemExit: If no file extensions are provided.
        """
        extensions_prompt = (
            "Enter file extensions to rename (comma-separated, e.g., .txt,.md): "
        )
        extensions_input = input(extensions_prompt).strip()

        if not extensions_input:
            sys.exit("No file extensions provided. Exiting the program.")

        return [extension.strip() for extension in extensions_input.split(",")]


class TransformationStrategyFactory:
    """Factory for creating filename transformation strategies."""

    _strategy_mapping: Dict[str, Type[FilenameTransformationStrategy]] = {
        "lower": LowercaseTransformationStrategy,
        "upper": UppercaseTransformationStrategy,
        "title": TitlecaseTransformationStrategy,
        "underscore": UnderscoreTransformationStrategy,
        "space": SpaceTransformationStrategy,
    }

    @classmethod
    def create_strategy_from_choice(
        cls, choice_code: str
    ) -> FilenameTransformationStrategy:
        """Create a transformation strategy based on the user's choice code.

        Args:
            choice_code: The code representing the user's choice ('l', 'u', 't', 'e', 's').

        Returns:
            The appropriate transformation strategy.

        Raises:
            ValueError: If the choice code is invalid.
        """
        strategy_type_mapping = {
            "l": "lower",
            "u": "upper",
            "t": "title",
            "e": "underscore",
            "s": "space",
        }

        if choice_code not in strategy_type_mapping:
            raise ValueError(f"Invalid choice code: {choice_code}")

        strategy_type = strategy_type_mapping[choice_code]
        strategy_class = cls._strategy_mapping[strategy_type]

        return strategy_class()


class FileOperationService:
    """Service for performing file operations."""

    @staticmethod
    def rename_file_with_logging(
        directory_path: str, original_filename: str, new_filename: str
    ) -> bool:
        """Rename a file and log the operation.

        Args:
            directory_path: The directory containing the file.
            original_filename: The original filename.
            new_filename: The new filename.

        Returns:
            True if the rename was successful, False otherwise.
        """
        original_file_path = os.path.join(directory_path, original_filename)
        new_file_path = os.path.join(directory_path, new_filename)

        try:
            # Rename the file and log the change
            os.rename(original_file_path, new_file_path)
            logging.info(f"Renamed '{original_filename}' to '{new_filename}'")
            return True

        except FileNotFoundError:
            print(f"Error: The file '{original_filename}' does not exist.")
            logging.error(f"File not found: '{original_filename}'")
            return False

        except FileExistsError:
            print(f"Error: The file '{new_filename}' already exists.")
            logging.error(f"File already exists: '{new_filename}'")
            return False

        except Exception as error:
            print(
                f"Error renaming file '{original_filename}' to '{new_filename}': {error}"
            )
            logging.error(
                f"Error renaming file '{original_filename}' to '{new_filename}': {error}"
            )
            return False


class FilenameCaseTransformationService:
    """Service for transforming filenames according to case and format rules."""

    def __init__(self, target_directory_path: str = None):
        """Initialize the FilenameCaseTransformationService.

        Args:
            target_directory_path: The directory containing files to transform.
                                  If None, uses the current working directory.
        """
        self.target_directory_path = target_directory_path or os.getcwd()
        self.logging_service = LoggingConfigurationService()
        self.input_service = UserInputCollectionService()
        self.file_operation_service = FileOperationService()
        self.logging_service.configure_logging_system()

    def execute_transformation_process(self) -> None:
        """Execute the complete filename transformation process."""
        try:
            # Collect user input
            transformation_choice = self.input_service.collect_transformation_choice()
            target_file_extensions = self.input_service.collect_file_extensions()

            # Create transformation strategy
            transformation_strategy = (
                TransformationStrategyFactory.create_strategy_from_choice(
                    transformation_choice
                )
            )

            # Process files
            self._process_files_in_directory(
                transformation_strategy, target_file_extensions
            )

        except Exception as error:
            print(f"An error occurred while running the application: {error}")
            logging.error(f"An error occurred while running the application: {error}")

    def _process_files_in_directory(
        self,
        transformation_strategy: FilenameTransformationStrategy,
        target_extensions: List[str],
    ) -> None:
        """Process all matching files in the directory.

        Args:
            transformation_strategy: The strategy to apply to filenames.
            target_extensions: List of file extensions to process.
        """
        print(f"Transforming filenames in directory: {self.target_directory_path}")

        try:
            for filename in os.listdir(self.target_directory_path):
                print(f"Found file: {filename}")

                # Skip files that don't match target extensions
                if not any(filename.endswith(ext) for ext in target_extensions):
                    print(f"Skipping file: {filename} (not in specified extensions)")
                    continue

                # Transform the filename
                transformed_filename = transformation_strategy.transform_filename(
                    filename
                )

                # Skip if no change
                if transformed_filename == filename:
                    print(f"Skipping file: {filename} (no change needed)")
                    continue

                # Rename the file
                print(f"Renaming '{filename}' to '{transformed_filename}'")
                self.file_operation_service.rename_file_with_logging(
                    self.target_directory_path, filename, transformed_filename
                )

        except Exception as error:
            print(f"Error during filename transformation: {error}")
            logging.error(f"Error during filename transformation: {error}")


class FilenameCaseTransformationApplicationLauncher:
    """Launcher for the filename case transformation application."""

    @staticmethod
    def launch_application() -> None:
        """Launch the filename case transformation application."""
        transformation_service = FilenameCaseTransformationService()
        transformation_service.execute_transformation_process()


def main() -> None:
    """Main entry point for the case-sensitive file renamer script."""
    application_launcher = FilenameCaseTransformationApplicationLauncher()
    application_launcher.launch_application()


if __name__ == "__main__":
    main()
