import os
import re
from typing import Dict, List


class SearchCriteria:
    """
    A class to encapsulate the search criteria, including the root directory
    and the search string pattern for matching file and folder names.

    Attributes:
        root_directory (str): The root directory to start the search from.
        pattern (re.Pattern): The compiled regular expression pattern used for matching.
    """

    def __init__(self, root_directory: str, search_string: str) -> None:
        """
        Initializes the SearchCriteria with a root directory and a search string.

        Args:
            root_directory (str): The root directory to start the search from.
            search_string (str): The string to search for in file and folder names.
        """
        self.root_directory: str = root_directory
        self.pattern: re.Pattern = re.compile(re.escape(search_string), re.IGNORECASE)


class FileSearcher:
    """
    A class to search for files and directories based on a given SearchCriteria.

    Methods:
        search(criteria: SearchCriteria) -> Dict[str, List[str]]:
            Searches for files and directories matching the given criteria.
            Returns a dictionary with 'folders' and 'files' as keys, each containing
            a list of matching paths.
    """

    def search(self, criteria: SearchCriteria) -> Dict[str, List[str]]:
        """
        Searches for files and directories matching the given criteria.

        Args:
            criteria (SearchCriteria): The criteria to search with, including
                                       the root directory and the search string pattern.

        Returns:
            Dict[str, List[str]]: A dictionary with 'folders' and 'files' as keys,
                                  each containing a list of matching paths.
        """
        matching_files: List[str] = []
        matching_folders: List[str] = []

        for root, dirs, files in os.walk(criteria.root_directory):
            matching_folders.extend(
                os.path.join(root, d) for d in dirs if criteria.pattern.search(d)
            )
            matching_files.extend(
                os.path.join(root, f) for f in files if criteria.pattern.search(f)
            )

        return {"folders": matching_folders, "files": matching_files}


class CommandLineSearchUtility:
    """
    A command-line utility to search for files and folders based on a user-provided string.

    Methods:
        run() -> None:
            Runs the command-line utility, prompts the user for input, and displays
            the search results.
    """

    def __init__(self) -> None:
        """
        Initializes the CommandLineSearchUtility with a FileSearcher instance.
        """
        self.file_searcher: FileSearcher = FileSearcher()

    def run(self) -> None:
        """
        Runs the command-line utility, prompts the user for input, and displays
        the search results.
        """
        root_directory: str = input("Enter the root directory to search: ")
        search_string: str = input("Enter the string to search for: ")

        criteria: SearchCriteria = SearchCriteria(root_directory, search_string)
        results: Dict[str, List[str]] = self.file_searcher.search(criteria)

        self.display_results(results)

    def display_results(self, results: Dict[str, List[str]]) -> None:
        """
        Displays the search results in a grouped format.

        Args:
            results (Dict[str, List[str]]): The search results to display, grouped by 'folders' and 'files'.
        """
        print("\n--- Search Results ---")
        print("\nFolders:")
        for folder in results["folders"]:
            print(folder)

        print("\nFiles:")
        for file in results["files"]:
            print(file)


if __name__ == "__main__":
    cli_search_utility: CommandLineSearchUtility = CommandLineSearchUtility()
    cli_search_utility.run()
