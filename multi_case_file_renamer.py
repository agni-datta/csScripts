import logging
import os
import sys
from datetime import datetime
from typing import List, Union

from titlecase import titlecase


class UpperCaseFileHandler:
    """Handler for transforming filenames to uppercase."""

    @staticmethod
    def process_file(filename: str) -> str:
        """Convert the provided filename to uppercase.

        Args:
            filename (str): The name of the file to convert.

        Returns:
            str: The filename transformed to uppercase.
        """
        name, ext = os.path.splitext(filename)
        return f"{name.upper()}{ext}"


class LowerCaseFileHandler:
    """Handler for transforming filenames to lowercase."""

    @staticmethod
    def process_file(filename: str) -> str:
        """Convert the provided filename to lowercase.

        Args:
            filename (str): The name of the file to convert.

        Returns:
            str: The filename transformed to lowercase.
        """
        name, ext = os.path.splitext(filename)
        return f"{name.lower()}{ext}"


class TitleCaseFileHandler:
    """Handler for transforming filenames to title case."""

    @staticmethod
    def process_file(filename: str) -> str:
        """Convert the provided filename to title case.

        Args:
            filename (str): The name of the file to convert.

        Returns:
            str: The filename transformed to title case.
        """
        name, ext = os.path.splitext(filename)
        title_cased_name = titlecase(name)
        return f"{title_cased_name}{ext}"


class UnderscoreFileHandler:
    """Handler for replacing spaces in filenames with underscores."""

    @staticmethod
    def process_file(filename: str) -> str:
        """Replace spaces with underscores in the provided filename.

        Args:
            filename (str): The name of the file to convert.

        Returns:
            str: The filename with spaces replaced by underscores.
        """
        name, ext = os.path.splitext(filename)
        return f"{name.replace(' ', '_')}{ext}"


class SpaceFileHandler:
    """Handler for replacing underscores in filenames with spaces."""

    @staticmethod
    def process_file(filename: str) -> str:
        """Replace underscores with spaces in the provided filename.

        Args:
            filename (str): The name of the file to convert.

        Returns:
            str: The filename with underscores replaced by spaces.
        """
        name, ext = os.path.splitext(filename)
        return f"{name.replace('_', ' ')}{ext}"


class UserInput:
    """Class for handling user input for filename transformations."""

    @staticmethod
    def get_user_choice() -> str:
        """Prompt the user to select a filename transformation option.

        This method validates the user's input and ensures it matches one of the
        accepted options ('l', 'u', 't', 'e', or 's').

        Returns:
            str: The chosen transformation option.

        Raises:
            SystemExit: If the user provides no input or an invalid option.
        """
        valid_choices = ["l", "u", "t", "e", "s"]
        choice: str = (
            input(
                "Enter 'l' for lowercase, 'u' for uppercase, 't' for title case, "
                "'e' for underscores, or 's' for spaces: "
            )
            .strip()
            .lower()
        )

        if choice not in valid_choices:
            print(f"Invalid input. Please enter one of {', '.join(valid_choices)}.")
            sys.exit("Exiting the program due to invalid input.")

        return choice

    @staticmethod
    def get_file_extensions() -> List[str]:
        """Prompt the user to enter file extensions for renaming.

        This method collects file extensions from the user and ensures that at
        least one extension is provided.

        Returns:
            List[str]: A list of file extensions to rename.

        Raises:
            SystemExit: If no file extensions are provided by the user.
        """
        extensions: str = input(
            "Enter file extensions to rename (comma-separated, e.g., .txt,.md): "
        ).strip()

        if not extensions:
            sys.exit("No file extensions provided. Exiting the program.")

        return [ext.strip() for ext in extensions.split(",")]


def configure_logging() -> None:
    """Set up logging for the application.

    This function configures the logging system to write to a log file named
    with the current date, capturing the time of each rename operation.
    """
    logging.basicConfig(
        filename=f"{datetime.now().strftime('%Y-%m-%d')}.log",
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
    )


class FileNameConverter:
    """Class for converting filenames in a specified directory."""

    def __init__(self, directory: str, handler: str, extensions: List[str]):
        """Initialize the FileNameConverter with directory, handler, and extensions.

        Args:
            directory (str): The path of the directory containing the files.
            handler (str): The type of handler for file processing ('upper', 'lower', 'title', 'underscore', or 'space').
            extensions (List[str]): A list of file extensions to rename.
        """
        self.directory: str = directory
        self.handler = self.get_handler(handler)
        self.extensions = extensions

    def get_handler(self, handler_type: str) -> Union[
        UpperCaseFileHandler,
        LowerCaseFileHandler,
        TitleCaseFileHandler,
        UnderscoreFileHandler,
        SpaceFileHandler,
    ]:
        """Retrieve the appropriate file handler based on user choice.

        Args:
            handler_type (str): The type of handler ('upper', 'lower', 'title', 'underscore', or 'space').

        Returns:
            Union[UpperCaseFileHandler, LowerCaseFileHandler, TitleCaseFileHandler, UnderscoreFileHandler, SpaceFileHandler]: The corresponding handler instance.

        Raises:
            ValueError: If the handler type is unknown.
        """
        if handler_type == "upper":
            return UpperCaseFileHandler()
        elif handler_type == "lower":
            return LowerCaseFileHandler()
        elif handler_type == "title":
            return TitleCaseFileHandler()
        elif handler_type == "underscore":
            return UnderscoreFileHandler()
        elif handler_type == "space":
            return SpaceFileHandler()
        else:
            raise ValueError(f"Unknown handler type: {handler_type}")

    def convert_filenames(self) -> None:
        """Convert the filenames in the specified directory.

        This method iterates through each file in the directory, applies the selected
        handler to process the filename, and renames the file if applicable.

        Raises:
            Exception: If an error occurs during file processing.
        """
        print(f"Converting filenames in directory: {self.directory}")
        try:
            for filename in os.listdir(self.directory):
                print(f"Found file: {filename}")
                if not any(filename.endswith(ext) for ext in self.extensions):
                    print(f"Skipping file: {filename} (not in specified extensions)")
                    continue

                new_filename: str = self.handler.process_file(filename)
                print(f"Renaming '{filename}' to '{new_filename}'")
                self.rename_file(filename, new_filename)
        except Exception as e:
            print(f"Error during filename conversion: {e}")
            logging.error(f"Error during filename conversion: {e}")

    def rename_file(self, old_name: str, new_name: str) -> None:
        """Rename a file and log the renaming action.

        Args:
            old_name (str): The original filename.
            new_name (str): The new filename after transformation.

        Raises:
            FileNotFoundError: If the original file does not exist.
            FileExistsError: If the new filename already exists.
        """
        old_path: str = os.path.join(self.directory, old_name)
        new_path: str = os.path.join(self.directory, new_name)

        try:
            # Rename the file and log the change
            os.rename(old_path, new_path)
            logging.info(f"Renamed '{old_name}' to '{new_name}'")
        except FileNotFoundError:
            print(f"Error: The file '{old_name}' does not exist.")
            logging.error(f"File not found: '{old_name}'")
        except FileExistsError:
            print(f"Error: The file '{new_name}' already exists.")
            logging.error(f"File already exists: '{new_name}'")
        except Exception as e:
            print(f"Error renaming file '{old_name}' to '{new_name}': {e}")
            logging.error(f"Error renaming file '{old_name}' to '{new_name}': {e}")


class Application:
    """Main application class to facilitate the file renaming process."""

    def __init__(self):
        """Initialize the application and configure logging."""
        self.directory: str = os.getcwd()  # Use the current working directory
        configure_logging()

    def run(self) -> None:
        """Execute the main logic of the application.

        This method gathers user input, initializes the file converter, and
        executes the filename conversion process.

        Raises:
            Exception: If an unexpected error occurs during the execution.
        """
        try:
            choice: str = UserInput.get_user_choice()
            handler_type: str

            if choice == "l":
                handler_type = "lower"
            elif choice == "u":
                handler_type = "upper"
            elif choice == "t":
                handler_type = "title"
            elif choice == "e":
                handler_type = "underscore"
            elif choice == "s":
                handler_type = "space"  # For the new option 's'
            else:
                sys.exit("Unexpected error in handler type selection.")

            extensions: List[str] = UserInput.get_file_extensions()
            converter: FileNameConverter = FileNameConverter(
                self.directory, handler_type, extensions
            )
            converter.convert_filenames()
        except Exception as e:
            print(f"An error occurred while running the application: {e}")
            logging.error(f"An error occurred while running the application: {e}")


if __name__ == "__main__":
    app = Application()
    app.run()
