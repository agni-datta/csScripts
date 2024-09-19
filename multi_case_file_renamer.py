import logging
import os
from datetime import datetime

from titlecase import titlecase


class UpperCaseFileHandler:
    """Handler for converting filenames to uppercase."""

    @staticmethod
    def process_file(filename: str) -> str:
        """Convert the filename to uppercase.

        Args:
            filename (str): The name of the file to convert.

        Returns:
            str: The new filename in uppercase.
        """
        name, ext = os.path.splitext(filename)
        return f"{name.upper()}{ext}"


class LowerCaseFileHandler:
    """Handler for converting filenames to lowercase."""

    @staticmethod
    def process_file(filename: str) -> str:
        """Convert the filename to lowercase.

        Args:
            filename (str): The name of the file to convert.

        Returns:
            str: The new filename in lowercase.
        """
        name, ext = os.path.splitext(filename)
        return f"{name.lower()}{ext}"


class TitleCaseFileHandler:
    """Handler for converting filenames to title case using the titlecase library."""

    @staticmethod
    def process_file(filename: str) -> str:
        """Convert the filename to title case.

        Args:
            filename (str): The name of the file to convert.

        Returns:
            str: The new filename in title case.
        """
        name, ext = os.path.splitext(filename)
        title_cased_name = titlecase(name)
        return f"{title_cased_name}{ext}"


class UnderscoreFileHandler:
    """Handler for replacing spaces in filenames with underscores."""

    @staticmethod
    def process_file(filename: str) -> str:
        """Replace spaces with underscores in the filename.

        Args:
            filename (str): The name of the file to convert.

        Returns:
            str: The new filename with spaces replaced by underscores.
        """
        name, ext = os.path.splitext(filename)
        return f"{name.replace(' ', '_')}{ext}"


class UserInput:
    """Class to handle user input."""

    @staticmethod
    def get_user_choice() -> str:
        """Prompt the user to choose between various filename transformations.

        Returns:
            str: 'l' for lowercase, 'u' for uppercase, 't' for title case, or 'e' for underscores.
        """
        while True:
            choice: str = (
                input(
                    "Enter 'l' for lowercase, 'u' for uppercase, 't' for title case, or 'e' for underscores: "
                )
                .strip()
                .lower()
            )
            if choice in ["l", "u", "t", "e"]:
                return choice
            else:
                print("Invalid input. Please enter 'l', 'u', 't', or 'e'.")

    @staticmethod
    def get_file_extensions() -> list:
        """Prompt the user to enter file extensions for renaming.

        Returns:
            list: A list of file extensions to rename.
        """
        extensions: str = input(
            "Enter file extensions to rename (comma-separated, e.g., .txt,.md): "
        )
        return [ext.strip() for ext in extensions.split(",")]


def configure_logging() -> None:
    """Configure logging for the application.

    This method sets up logging to write to a log file named with
    the current date, logging the time of each rename operation.
    """
    logging.basicConfig(
        filename=f"{datetime.now().strftime('%Y-%m-%d')}.log",
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
    )


class FileNameConverter:
    """Class to convert filenames in a specified directory."""

    def __init__(self, directory: str, handler: str, extensions: list):
        """Initialize FileNameConverter.

        Args:
            directory (str): The directory containing the files.
            handler (str): The type of handler for file processing ('upper', 'lower', 'title', or 'underscore').
            extensions (list): List of file extensions to rename.
        """
        self.directory: str = directory
        self.handler = self.get_handler(handler)
        self.extensions = extensions

    def get_handler(self, handler_type: str):
        """Get the appropriate handler based on user choice.

        Args:
            handler_type (str): The type of handler ('upper', 'lower', 'title', or 'underscore').

        Returns:
            Union[UpperCaseFileHandler, LowerCaseFileHandler, TitleCaseFileHandler, UnderscoreFileHandler]: The appropriate handler.
        """
        if handler_type == "upper":
            return UpperCaseFileHandler()
        elif handler_type == "lower":
            return LowerCaseFileHandler()
        elif handler_type == "title":
            return TitleCaseFileHandler()
        return UnderscoreFileHandler()

    def convert_filenames(self) -> None:
        """Convert the filenames in the specified directory."""
        print(f"Converting filenames in directory: {self.directory}")
        for filename in os.listdir(self.directory):
            print(f"Found file: {filename}")
            # Check if the file has one of the specified extensions
            if not any(filename.endswith(ext) for ext in self.extensions):
                print(f"Skipping file: {filename} (not in specified extensions)")
                continue

            new_filename: str = self.handler.process_file(filename)
            print(f"Renaming '{filename}' to '{new_filename}'")
            self.rename_file(filename, new_filename)

    def rename_file(self, old_name: str, new_name: str) -> None:
        """Rename a file and log the changes.

        Args:
            old_name (str): The current filename.
            new_name (str): The new filename.
        """
        old_path: str = os.path.join(self.directory, old_name)
        new_path: str = os.path.join(self.directory, new_name)

        # Rename the file
        os.rename(old_path, new_path)
        logging.info(f"Renamed '{old_name}' to '{new_name}'")


class Application:
    """Main application class to run the file renaming process."""

    def __init__(self):
        """Initialize Application and configure logging."""
        self.directory: str = os.getcwd()  # Use the current working directory
        configure_logging()

    def run(self) -> None:
        """Main execution method for the application."""
        choice: str = UserInput.get_user_choice()
        handler_type: str = (
            "lower"
            if choice == "l"
            else (
                "upper" if choice == "u" else "title" if choice == "t" else "underscore"
            )
        )
        extensions: list = UserInput.get_file_extensions()
        converter: FileNameConverter = FileNameConverter(
            self.directory, handler_type, extensions
        )
        converter.convert_filenames()


if __name__ == "__main__":
    app = Application()
    app.run()
