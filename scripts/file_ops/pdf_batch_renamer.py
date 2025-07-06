"""
PDF Batch Renamer Module

This module provides tools for batch renaming PDF files in a directory or directory tree.
It supports customizable renaming patterns, preview/dry-run mode, and logging of changes.

Features:
- Batch renaming of PDF files
- Customizable renaming rules
- Dry-run mode for previewing changes
- Logging of all renaming operations
- Error handling for file conflicts

Example:
    >>> renamer = PDFBatchRenamer()
    >>> renamer.rename_all("/path/to/pdf/folder")
"""

import datetime
import logging
import os
import re
from multiprocessing import Pool, cpu_count
from typing import List, Optional, Set

from spellchecker import SpellChecker


class EnglishDictionary:
    """
    A class to manage and provide a set of common English words and custom terms.

    Methods:
    --------
    load_english_dictionary() -> Set[str]:
        Loads a dictionary of common English words, including additional words and Roman numerals.
    """

    def __init__(self):
        self.dictionary: Set[str] = self.load_english_dictionary()

    def load_english_dictionary(self) -> Set[str]:
        """
        Load a dictionary of common English words.

        Returns:
        --------
        Set[str]: A set containing common English words.
        """
        spell: SpellChecker = SpellChecker()
        english_dict: Set[str] = set(spell.word_frequency.keys())

        # Additional words to add to the dictionary
        additional_words = {
            "zkSNARKS",
            "SNARKS",
            "SNARGS",
            "STARKS",
            "TeX",
            "LaTeX",
            "ODE",
            "PDE",
            "CRC",
        }

        # Roman numerals from I to XIII
        roman_numerals = {
            "I",
            "II",
            "III",
            "IV",
            "V",
            "VI",
            "VII",
            "VIII",
            "IX",
            "X",
            "XI",
            "XII",
            "XIII",
        }

        # Convert additional words to title case and add them to the dictionary
        additional_words_title_case = set(word.title() for word in additional_words)

        # Add the words to the dictionary
        english_dict.update(additional_words_title_case)
        english_dict.update(roman_numerals)

        return english_dict


class FileRenamer:
    """
    A class to rename files by splitting concatenated words in filenames and converting them to a readable format.

    Attributes:
    -----------
    directory: str
        The directory containing files to rename.

    Methods:
    --------
    sanitize_filename(filename: str) -> str:
        Removes special characters from the filename using regular expressions.

    split_concatenated_words(filename: str, english_dictionary: Set[str]) -> str:
        Splits concatenated words in a filename based on certain rules using the provided English dictionary.

    rename_file(filename: str, english_dictionary: Set[str]) -> None:
        Renames a single file in the current directory by utilizing split_concatenated_words().

    rename_files() -> None:
        Renames files in the current directory using multiprocessing for improved performance.
    """

    def __init__(self, directory: Optional[str] = None):
        self.directory: str = directory or os.getcwd()
        self.english_dictionary = EnglishDictionary().dictionary
        self.setup_logging()

    def setup_logging(self) -> None:
        """
        Set up logging for the renaming process.
        """
        log_file = os.path.join(
            self.directory, f"rename_{datetime.datetime.now():%Y-%m-%d}.log"
        )
        logging.basicConfig(
            filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s"
        )

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Remove special characters from the filename.

        Args:
        ----
        filename (str): The filename to sanitize.

        Returns:
        -------
        str: The sanitized filename.
        """
        return re.sub(r'[\\/;:\'"`%$#@!*+=]', "", filename)

    def split_concatenated_words(self, filename: str) -> str:
        """
        Split concatenated words using the English dictionary and convert to title case.

        Args:
        ----
        filename (str): The filename to split.

        Returns:
        -------
        str: The sanitized filename.
        """
        if not filename:
            raise ValueError("Filename cannot be empty.")

        # Sanitize the filename
        filename = self.sanitize_filename(filename)

        # Replace "And" with "&"
        filename = filename.replace(" And ", " & ")

        # Split the filename and extension
        base_filename, extension = os.path.splitext(filename)

        # Use regex to split the base filename into words based on various patterns
        words: List[str] = re.findall(
            r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|[^\W_]+", base_filename
        )

        # Convert to title case, handling exceptions for articles, conjunctions, and prepositions
        conjunctions_prepositions = sorted(
            [
                "a",
                "an",
                "and",
                "as",
                "at",
                "but",
                "by",
                "for",
                "if",
                "in",
                "nor",
                "of",
                "on",
                "or",
                "so",
                "the",
                "to",
                "up",
                "yet",
                "with",
                "within",
                "aboard",
                "about",
                "above",
                "across",
                "after",
                "against",
                "along",
                "amid",
                "among",
                "around",
                "as",
                "at",
                "before",
                "behind",
                "below",
                "beneath",
                "beside",
                "between",
                "beyond",
                "but",
                "by",
                "concerning",
                "considering",
            ]
        )

        for i, word in enumerate(words):
            if i != 0 and word.lower() in conjunctions_prepositions:
                words[i] = word.lower()
            else:
                words[i] = word.title()

        # Ensure words not in the dictionary are added as title case
        for i, word in enumerate(words):
            if word.lower() not in self.english_dictionary:
                words[i] = word.title()

        # Join the words with underscores
        joined_filename = "_".join(words)

        # Combine the base filename and extension
        new_filename = f"{joined_filename}{extension}"

        return new_filename

    def rename_file(self, filename: str) -> None:
        """
        Rename a single file in the current directory.

        Args:
        ----
        filename (str): The filename to rename.
        """
        try:
            old_filename: str = os.path.join(self.directory, filename)
            new_filename: str = self.split_concatenated_words(filename)
            new_filepath = os.path.join(self.directory, new_filename)
            if old_filename != new_filepath:
                os.rename(old_filename, new_filepath)
                logging.info("Renamed '%s' to '%s'", filename, new_filename)
        except FileExistsError:
            logging.warning("Skipped renaming. File '%s' already exists.", filename)
        except FileNotFoundError as e:
            logging.error("File not found: %s", e)
        except PermissionError as e:
            logging.error("Permission denied: %s", e)
        except OSError as e:
            logging.error("OS error occurred: %s", e)

    def rename_files(self) -> None:
        """
        Rename files in the current directory using multiprocessing for improved performance.
        """
        try:
            # Get list of files to rename
            files_to_rename = [
                filename
                for filename in os.listdir(self.directory)
                if filename.endswith(".pdf")
            ]

            # Rename files in parallel using multiprocessing
            with Pool(cpu_count()) as pool:
                pool.map(self.rename_file, files_to_rename)
        except FileNotFoundError as e:
            logging.error("File not found: %s", e)
        except PermissionError as e:
            logging.error("Permission denied: %s", e)
        except OSError as e:
            logging.error("OS error occurred: %s", e)


if __name__ == "__main__":
    renamer = FileRenamer()
    renamer.rename_files()
