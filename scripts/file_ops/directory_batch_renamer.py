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
    >>> renamer = DirectoryBatchRenamer()
    >>> renamer.rename_directories("/path/to/root")
"""

import logging
import os
from pathlib import Path
from typing import Set


class FolderRenamer:
    """
    A class that renames folders by moving articles ('A', 'An', 'The') from the start
    of the folder name to the end and logs the changes.

    Attributes:
    ----------
    articles : Set[str]
        A set of articles to be moved to the end of folder names.
    directory : Path
        The directory where the script is located and where the renaming occurs.
    log_file : Path
        The log file to record the renaming operations.
    """

    def __init__(self) -> None:
        """
        Initialize the FolderRenamer with the directory path and articles set.
        """
        self.articles: Set[str] = {"A", "An", "The"}
        self.directory: Path = Path(__file__).parent.resolve()
        self.log_file: Path = self.setup_logging()

    def setup_logging(self) -> Path:
        """
        Set up logging configuration for the renaming process.

        Returns:
        -------
        Path
            The path to the log file where operations are recorded.
        """
        log_file: Path = self.directory / f"{self.directory.name}.log"
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        return log_file

    def rename_folder(self, folder_name: str) -> None:
        """
        Rename a single folder if its name starts with an article.

        Args:
        ----
        folder_name : str
            The current name of the folder to be renamed.
        """
        full_path: Path = self.directory / folder_name
        words: list[str] = folder_name.split()

        if words[0] in self.articles:
            new_folder_name: str = f"{' '.join(words[1:])}, {words[0]}"
            new_full_path: Path = self.directory / new_folder_name

            full_path.rename(new_full_path)
            logging.info(f"Renamed '{folder_name}' to '{new_folder_name}'")
        else:
            logging.info(f"No change for '{folder_name}'")

    def rename_folders_in_directory(self) -> None:
        """
        Rename all folders in the directory by applying the article-moving rule.
        """
        logging.info("Starting folder renaming process.")
        for folder_name in os.listdir(self.directory):
            full_path: Path = self.directory / folder_name

            if full_path.is_dir():
                self.rename_folder(folder_name)
            else:
                logging.info(f"'{folder_name}' is not a directory, skipping.")
        logging.info("Folder renaming process completed.")

    def run(self) -> None:
        """
        Execute the folder renaming process.
        """
        self.rename_folders_in_directory()


if __name__ == "__main__":
    renamer = FolderRenamer()
    renamer.run()
