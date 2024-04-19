import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime


def configure_logging(log_filename):
    """
    Configure logging settings.

    Args:
        log_filename (str): The filename for the log file.
    """
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def delete_file(file_path, directory):
    """
    Delete a single file.

    Args:
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


def delete_files_in_directory(directory, extensions):
    """
    Recursively delete files with specified extensions in a directory.

    Args:
        directory (str): The directory to start the search from.
        extensions (list): List of file extensions to delete.
    """
    with ThreadPoolExecutor(
        max_workers=18
    ) as executor:  # Limiting max_workers to control resource usage
        for root, files in os.walk(directory):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    executor.submit(delete_file, file_path, root)


def main():
    """
    Main function to execute the file deletion process.
    """
    # Get the directory of the script

    script_directory = os.path.dirname(__file__)
    # Configure logging

    log_filename = os.path.join(
        script_directory, f"deleted_files_{datetime.now().strftime('%Y-%m-%d')}.log"
    )
    configure_logging(log_filename)

    # Extensions to delete

    file_extensions_to_delete = [
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

    # Perform file deletion in the script directory

    delete_files_in_directory(script_directory, file_extensions_to_delete)

    # Delete files in the current directory (excluding the script directory)

    current_directory = os.getcwd()
    if current_directory != script_directory:
        delete_files_in_directory(current_directory, file_extensions_to_delete)


if __name__ == "__main__":
    main()
