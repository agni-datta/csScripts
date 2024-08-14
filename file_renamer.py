import os
from typing import List


class FileRenamer:
    def __init__(self, file_extension: str):
        """
        Initializes the FileRenamer instance.

        Parameters:
        ----------
        file_extension : str
            The extension of the files to be renamed. This should include the dot (e.g., '.txt').
        """
        self.file_extension = file_extension
        self.current_directory = os.path.dirname(os.path.realpath(__file__))
        self.log_file_path = os.path.join(self.current_directory, "rename_log.txt")

    def get_files_with_extension(self) -> List[str]:
        """
        Retrieves a list of files with the specified extension from the current directory.

        Returns:
        -------
        List[str]
            A list of filenames in the directory with the specified extension. The list is sorted alphabetically.
        """
        if not self.file_extension.startswith("."):
            self.file_extension = f".{self.file_extension}"

        files = [
            f
            for f in os.listdir(self.current_directory)
            if f.endswith(self.file_extension)
        ]
        files.sort()

        return files

    def log_renaming_action(self, old_name: str, new_name: str) -> None:
        """
        Logs the renaming action to a log file.

        Parameters:
        ----------
        old_name : str
            The original filename before renaming.
        new_name : str
            The new filename after renaming.

        Returns:
        -------
        None
        """
        with open(self.log_file_path, "a") as log_file:
            log_file.write(f"Renamed: {old_name} -> {new_name}\n")

    def rename_files(self) -> None:
        """
        Renames files with the specified extension in the current directory and logs the actions.

        This method retrieves all files with the specified extension, renames them sequentially, and logs each renaming action
        to the log file.

        Returns:
        -------
        None
        """
        files = self.get_files_with_extension()
        for i, filename in enumerate(files, start=1):
            new_name = f"{i}{self.file_extension}"
            old_file = os.path.join(self.current_directory, filename)
            new_file = os.path.join(self.current_directory, new_name)
            os.rename(old_file, new_file)
            self.log_renaming_action(filename, new_name)

    def run(self) -> None:
        """
        Executes the file renaming process.

        This method initiates the renaming operation by calling the `rename_files` method.

        Returns:
        -------
        None
        """
        self.rename_files()


if __name__ == "__main__":
    # Prompt the user to enter the file extension
    file_extension = input("Enter the file extension (e.g., '.txt'): ").strip()

    # Create an instance of FileRenamer and execute the renaming process
    renamer = FileRenamer(file_extension)
    renamer.run()
