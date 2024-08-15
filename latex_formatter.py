import argparse
import glob
import os
import subprocess
from typing import List


class TexProcessor:
    """
    A class to process .tex files by breaking text into columns of specified width and formatting them with latexindent.

    Methods:
    --------
    break_text_to_columns(text: str, column_width: int) -> str:
        Breaks the given text into lines based on the specified column width while preserving blank lines.

    format_with_latexindent(input_file: str, output_file: str) -> None:
        Formats a .tex file using latexindent.

    process_tex_file(file_path: str, column_width: int) -> None:
        Processes a .tex file by breaking its content into columns, creating a backup, and formatting it with latexindent.

    process_all_tex_files(directory: str, column_width: int) -> None:
        Processes all .tex files in the specified directory and its subdirectories.

    run(file_path: str, process_all: bool, column_width: int) -> None:
        Runs the processing based on the provided arguments.
    """

    @staticmethod
    def break_text_to_columns(text: str, column_width: int) -> str:
        """
        Breaks a given text into lines based on a specified column width while preserving blank lines and existing spacing.

        Args:
        ----
        text (str): The input text to be broken into columns.
        column_width (int): The maximum number of characters per line.

        Returns:
        -------
        str: The text broken into lines of specified column width.
        """
        lines = text.splitlines()
        broken_lines = []

        for line in lines:
            if not line.strip():  # Preserve blank lines
                broken_lines.append("")
                continue

            words = line.split()
            current_line = ""

            for word in words:
                if len(current_line) + len(word) + 1 <= column_width:
                    if current_line:
                        current_line += " "
                    current_line += word
                else:
                    broken_lines.append(current_line)
                    current_line = word

            if current_line:
                broken_lines.append(current_line)

        return "\n".join(broken_lines)

    @staticmethod
    def format_with_latexindent(input_file: str, output_file: str) -> None:
        """
        Formats a .tex file using latexindent.

        Args:
        ----
        input_file (str): The path to the input .tex file.
        output_file (str): The path to the output .tex file.

        Raises:
        ------
        FileNotFoundError: If the specified input .tex file does not exist.
        subprocess.CalledProcessError: If latexindent fails to run.
        """
        if not os.path.isfile(input_file):
            raise FileNotFoundError(f"The file {input_file} does not exist.")

        try:
            subprocess.run(
                ["latexindent", "--outputfile=" + output_file, input_file], check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"latexindent failed: {e}")

    @staticmethod
    def process_tex_file(file_path: str, column_width: int) -> None:
        """
        Processes a .tex file by breaking its content into columns, creating a backup,
        and formatting it with latexindent.

        Args:
        ----
        file_path (str): The path to the .tex file.
        column_width (int): The maximum number of characters per line.

        Raises:
        ------
        FileNotFoundError: If the specified .tex file does not exist.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")

        backup_file_path = f"{file_path}.bak"
        os.rename(file_path, backup_file_path)

        with open(backup_file_path, "r") as file:
            content = file.read()

        broken_text = TexProcessor.break_text_to_columns(content, column_width)

        with open(file_path, "w") as file:
            file.write(broken_text)

        TexProcessor.format_with_latexindent(file_path, file_path)

    @staticmethod
    def process_all_tex_files(directory: str, column_width: int) -> None:
        """
        Processes all .tex files in the specified directory and its subdirectories.

        Args:
        ----
        directory (str): The directory to search for .tex files.
        column_width (int): The maximum number of characters per line.
        """
        tex_files = glob.glob(os.path.join(directory, "**", "*.tex"), recursive=True)
        for tex_file in tex_files:
            try:
                TexProcessor.process_tex_file(tex_file, column_width)
                print(f"Processed {tex_file} successfully.")
            except Exception as e:
                print(f"An error occurred while processing {tex_file}: {e}")

    @staticmethod
    def run(
        file_path: str = None, process_all: bool = False, column_width: int = 80
    ) -> None:
        """
        Runs the processing of .tex files based on the provided arguments.

        Args:
        ----
        file_path (str, optional): Path to a single .tex file to process. Defaults to None.
        process_all (bool, optional): Flag to process all .tex files in the current directory and subdirectories. Defaults to False.
        column_width (int, optional): Maximum number of characters per line. Defaults to 80.
        """
        if process_all:
            TexProcessor.process_all_tex_files(".", column_width)
        elif file_path:
            try:
                TexProcessor.process_tex_file(file_path, column_width)
                print(
                    f"File processed successfully. A backup has been saved as {file_path}.bak"
                )
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            print(
                "Please specify either --file to process a single file or --all to process all .tex files in the directory."
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process .tex files by breaking text into columns and formatting with latexindent."
    )
    parser.add_argument("--file", help="Path to the .tex file to process.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all .tex files in the current directory and subdirectories.",
    )
    parser.add_argument(
        "--column-width",
        type=int,
        default=80,
        help="Maximum number of characters per line.",
    )
    args = parser.parse_args()

    TexProcessor.run(
        file_path=args.file, process_all=args.all, column_width=args.column_width
    )
