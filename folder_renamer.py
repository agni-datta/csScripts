"""
This script renames folders in the directory where the script is located by moving articles 
("A", "An", "The") from the start of the folder name to the end, and logs the changes to a log file.

For example:
- Folder "A Beautiful Mind" would be renamed to "Beautiful Mind, A".
- Folder "The Matrix" would be renamed to "Matrix, The".
- Folder "An Unexpected Journey" would be renamed to "Unexpected Journey, An".

A log file named <root folder>.log is created in the root folder to record the operations.

Usage:
- Place this script in the directory you want to process and run it.
"""

import logging
import os
from pathlib import Path


def setup_logging(directory):
    # Define the log file name based on the root folder name

    log_file = directory / f"{directory.name}.log"

    # Set up the logging configuration

    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return log_file


def rename_folders_in_directory():
    # Define articles that should be moved to the end

    articles = {"A", "An", "The"}

    # Get the directory where the script is located

    directory = Path(__file__).parent.resolve()

    # Setup logging

    log_file = setup_logging(directory)
    logging.info("Starting folder renaming process.")

    # Iterate through all items in the directory

    for folder_name in os.listdir(directory):
        full_path = directory / folder_name

        # Ensure the item is a directory

        if full_path.is_dir():
            words = folder_name.split()

            # Check if the first word is an article

            if words[0] in articles:
                # Create the new folder name by moving the article to the end

                new_folder_name = f"{' '.join(words[1:])}, {words[0]}"
                new_full_path = directory / new_folder_name

                # Rename the folder

                full_path.rename(new_full_path)
                logging.info(f"Renamed '{folder_name}' to '{new_folder_name}'")
            else:
                logging.info(f"No change for '{folder_name}'")
        else:
            logging.info(f"'{folder_name}' is not a directory, skipping.")
    logging.info("Folder renaming process completed.")


# Run the function

if __name__ == "__main__":
    rename_folders_in_directory()
