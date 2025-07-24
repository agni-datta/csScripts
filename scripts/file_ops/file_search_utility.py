"""
File Search Utility Module

This module provides a command-line utility for searching files and directories based on
user-specified criteria. It implements a flexible search system that can find both files
and folders matching a given pattern.

Features:
- Case-insensitive search
- Recursive directory traversal
- Separate results for files and folders
- Interactive command-line interface
- Regular expression support

The module is organized into several main classes:
- FileSearchCriteria: Encapsulates search parameters
- FileSystemSearchService: Performs the actual search operation
- SearchResultDisplayService: Handles displaying search results
- UserInputCollectionService: Collects user input for search parameters
- FileSearchApplicationLauncher: Coordinates the search process

Example:
    >>> launcher = FileSearchApplicationLauncher()
    >>> launcher.execute_search_process()
    Enter the root directory to search: /path/to/search
    Enter the string to search for: example
"""

import os
import re
from typing import Dict, List, NamedTuple


class SearchResultCollection(NamedTuple):
    """
    A named tuple to store search results categorized by type.
    """

    matching_folders: List[str]
    matching_files: List[str]


class FileSearchCriteria:
    """
    Encapsulates search criteria for file and directory searches.

    This class stores the parameters needed for a file system search operation,
    including the starting directory and the pattern to match against file
    and directory names.
    """

    def __init__(self, target_directory_path: str, search_pattern_text: str) -> None:
        """
        Initialize the FileSearchCriteria with search parameters.

        Args:
            target_directory_path: The root directory to start the search from.
            search_pattern_text: The string pattern to search for in file and folder names.
        """
        self.target_directory_path: str = target_directory_path
        self.compiled_search_pattern: re.Pattern = re.compile(
            re.escape(search_pattern_text), re.IGNORECASE
        )


class FileSystemSearchService:
    """
    Service for searching files and directories in the file system.

    This service performs recursive searches through the file system to find
    files and directories that match specified search criteria.
    """

    def execute_search_operation(
        self, search_criteria: FileSearchCriteria
    ) -> SearchResultCollection:
        """
        Search for files and directories matching the given criteria.

        Args:
            search_criteria: The criteria to use for the search operation.

        Returns:
            SearchResultCollection: Collection of matching files and folders.
        """
        matching_file_paths: List[str] = []
        matching_folder_paths: List[str] = []

        for current_directory_path, subdirectory_names, file_names in os.walk(
            search_criteria.target_directory_path
        ):
            # Find matching directories
            for subdirectory_name in subdirectory_names:
                if search_criteria.compiled_search_pattern.search(subdirectory_name):
                    matching_folder_paths.append(
                        os.path.join(current_directory_path, subdirectory_name)
                    )

            # Find matching files
            for file_name in file_names:
                if search_criteria.compiled_search_pattern.search(file_name):
                    matching_file_paths.append(
                        os.path.join(current_directory_path, file_name)
                    )

        return SearchResultCollection(
            matching_folders=matching_folder_paths, matching_files=matching_file_paths
        )


class SearchResultDisplayService:
    """
    Service for displaying search results to the user.

    This service formats and presents search results in a user-friendly way,
    categorizing them by type (files vs. folders).
    """

    def display_formatted_search_results(
        self, search_results: SearchResultCollection
    ) -> None:
        """
        Display search results in a formatted, categorized manner.

        Args:
            search_results: The search results to display.
        """
        print("\n--- Search Results ---")

        # Display folder results
        print("\nFolders:")
        if search_results.matching_folders:
            for folder_path in search_results.matching_folders:
                print(folder_path)
        else:
            print("No matching folders found.")

        # Display file results
        print("\nFiles:")
        if search_results.matching_files:
            for file_path in search_results.matching_files:
                print(file_path)
        else:
            print("No matching files found.")

        # Display summary
        print(
            f"\nFound {len(search_results.matching_folders)} folders and "
            f"{len(search_results.matching_files)} files matching the search criteria."
        )


class UserInputCollectionService:
    """
    Service for collecting user input for search operations.

    This service handles prompting the user for search parameters and
    validating the input.
    """

    def collect_search_parameters(self) -> FileSearchCriteria:
        """
        Collect search parameters from the user.

        Returns:
            FileSearchCriteria: The search criteria based on user input.
        """
        target_directory_path: str = self._prompt_for_directory_path()
        search_pattern_text: str = self._prompt_for_search_pattern()

        return FileSearchCriteria(target_directory_path, search_pattern_text)

    def _prompt_for_directory_path(self) -> str:
        """
        Prompt the user for a directory path to search.

        Returns:
            str: The directory path entered by the user.
        """
        while True:
            directory_path = input("Enter the root directory to search: ").strip()
            if os.path.isdir(directory_path):
                return directory_path
            print(
                f"Error: '{directory_path}' is not a valid directory. Please try again."
            )

    def _prompt_for_search_pattern(self) -> str:
        """
        Prompt the user for a search pattern.

        Returns:
            str: The search pattern entered by the user.
        """
        return input("Enter the string to search for: ").strip()


class FileSearchApplicationLauncher:
    """
    Coordinates the file search application process.

    This class orchestrates the entire search process, from collecting user input
    to displaying search results.
    """

    def __init__(self) -> None:
        """
        Initialize the FileSearchApplicationLauncher with required services.
        """
        self.input_collection_service: UserInputCollectionService = (
            UserInputCollectionService()
        )
        self.search_service: FileSystemSearchService = FileSystemSearchService()
        self.display_service: SearchResultDisplayService = SearchResultDisplayService()

    def execute_search_process(self) -> None:
        """
        Execute the complete search process.
        """
        # Collect search parameters from the user
        search_criteria: FileSearchCriteria = (
            self.input_collection_service.collect_search_parameters()
        )

        # Perform the search operation
        search_results: SearchResultCollection = (
            self.search_service.execute_search_operation(search_criteria)
        )

        # Display the search results
        self.display_service.display_formatted_search_results(search_results)


def main() -> None:
    """
    Main entry point for the file search utility.
    """
    application_launcher: FileSearchApplicationLauncher = (
        FileSearchApplicationLauncher()
    )
    application_launcher.execute_search_process()


if __name__ == "__main__":
    main()
