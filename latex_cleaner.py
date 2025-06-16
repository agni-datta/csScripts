import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Optional


class FileDeleter:
    """
    A class to recursively delete files with specified extensions in a directory.

    Methods:
    --------
    configure_logging(log_filename: str) -> None:
        Configures logging settings for file deletion activities.

    delete_file(file_path: str, directory: str) -> None:
        Deletes a single file and logs the deletion.

    delete_files_in_directory(directory: str, extensions: List[str]) -> None:
        Recursively deletes files with specified extensions in a directory.

    run(directory: Optional[str] = None, extensions: Optional[List[str]] = None) -> None:
        Main method to execute the file deletion process.
    """

    def __init__(self, log_directory: Optional[str] = None):
        """
        Initialize the FileDeleter with an optional log directory.

        Args:
        ----
        log_directory (Optional[str]): Directory where the log file will be stored.
                                        If None, logs will be stored in the script's directory.
        """
        self.log_directory = log_directory or os.path.dirname(__file__)
        self.log_filename = os.path.join(
            self.log_directory,
            f"deleted_files_{datetime.now().strftime('%Y-%m-%d')}.log",
        )
        self.configure_logging(self.log_filename)

    def configure_logging(self, log_filename: str) -> None:
        """
        Configure logging settings.

        Args:
        ----
        log_filename (str): The filename for the log file.
        """
        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            format="%(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def delete_file(self, file_path: str, directory: str) -> None:
        """
        Delete a single file.

        Args:
        ----
        file_path (str): Path to the file to be deleted.
        directory (str): Path to the directory from which the file is deleted.
        """
        try:
            os.remove(file_path)
            logging.info("Deleted: %s (from directory: %s)", file_path, directory)
        except FileNotFoundError as e:
            logging.error("Error deleting file %s: %s", file_path, e)
        except PermissionError as e:
            logging.error("Error deleting file %s: %s", file_path, e)
        except OSError as e:
            logging.error("Error deleting file %s: %s", file_path, e)

    def delete_files_in_directory(self, directory: str, extensions: List[str]) -> None:
        """
        Recursively delete files with specified extensions in a directory.

        Args:
        ----
        directory (str): The directory to start the search from.
        extensions (List[str]): List of file extensions to delete.
        """
        with ThreadPoolExecutor(
            max_workers=18
        ) as executor:  # Limiting max_workers to control resource usage
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in extensions):
                        file_path = os.path.join(root, file)
                        executor.submit(self.delete_file, file_path, root)

    def run(
        self, directory: Optional[str] = None, extensions: Optional[List[str]] = None
    ) -> None:
        """
        Main method to execute the file deletion process.

        Args:
        ----
        directory (Optional[str]): Directory where the file deletion will be performed. Defaults to current directory.
        extensions (Optional[List[str]]): List of file extensions to delete. Defaults to a standard list of extensions.
        """
        if directory is None:
            directory = os.getcwd()

        if extensions is None:
            extensions = [
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

        # Perform file deletion in the specified directory
        self.delete_files_in_directory(directory, extensions)

        # If the script directory is different from the current directory, delete in the script directory too
        script_directory = os.path.dirname(__file__)
        if directory != script_directory:
            self.delete_files_in_directory(script_directory, extensions)


if __name__ == "__main__":
    deleter = FileDeleter()
    deleter.run()
