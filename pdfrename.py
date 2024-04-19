import datetime
import logging
import os
import re
from multiprocessing import Pool, cpu_count
from typing import List, Set

from spellchecker import SpellChecker


def load_english_dictionary() -> Set[str]:
    """
    Load a dictionary of common English words.

    Returns:
        Set[str]: A set containing common English words.
    """
    spell: SpellChecker = SpellChecker()
    english_dict: Set[str] = set(spell.word_frequency.keys())  # Retain case of words

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

    # Convert additional words to APA title case before adding to the dictionary

    additional_words_title_case = set(word.title() for word in additional_words)

    # Add the words to the dictionary

    english_dict.update(additional_words_title_case)
    english_dict.update(roman_numerals)

    return english_dict


def sanitize_filename(filename: str) -> str:
    """
    Remove special characters from the filename.

    Args:
        filename (str): The filename to sanitize.

    Returns:
        str: The sanitized filename.
    """
    return re.sub(r'[\\/;:\'"`%$#@!*+=]', "", filename)


def split_concatenated_words(filename: str) -> str:
    """
    Split concatenated words using the English dictionary and convert to title case.

    Args:
        filename (str): The filename to split.
        english_dictionary (Set[str]): Set of common English words.

    Returns:
        str: The sanitized filename.
    """
    if not filename:
        raise ValueError("Filename cannot be empty.")
    # Sanitize the filename

    filename = sanitize_filename(filename)

    # Replace "And" with "&"

    filename = filename.replace(" And ", " & ")

    # Split the filename and extension

    base_filename, extension = os.path.splitext(filename)

    # Use regular expression to split the base filename into words based on spaces, underscores, and camelCase or PascalCase conventions

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
            "despite",
            "down",
            "during",
            "except",
            "excepting",
            "excluding",
            "following",
            "from",
            "in",
            "inside",
            "into",
            "like",
            "near",
            "off",
            "on",
            "onto",
            "out",
            "outside",
            "over",
            "past",
            "regarding",
            "round",
            "since",
            "through",
            "throughout",
            "till",
            "to",
            "toward",
            "towards",
            "under",
            "underneath",
            "unlike",
            "until",
            "unto",
            "up",
            "upon",
            "with",
            "within",
            "without",
        ]
    )

    for i, word in enumerate(words):
        if i != 0 and word.lower() in conjunctions_prepositions:
            words[i] = word.lower()
        else:
            words[i] = word.title()
    # Join the words with underscores

    joined_filename = "_".join(words)

    # Combine the base filename and extension

    new_filename = f"{joined_filename}{extension}"

    return new_filename


def rename_file(filename: str, english_dictionary: Set[str]) -> None:
    """
    Rename a single file in the current directory.

    Args:
        filename (str): The filename to rename.
        english_dictionary (Set[str]): Set of common English words.
    """
    try:
        current_directory: str = os.getcwd()
        old_filename: str = os.path.join(current_directory, filename)
        new_filename: str = split_concatenated_words(filename)
        new_filepath = os.path.join(current_directory, new_filename)
        if old_filename != new_filepath:
            # Rename the file if the new filename is different

            os.rename(old_filename, new_filepath)
            # Show changes to the user

            logging.info("Renamed '%s' to '%s'", filename, new_filename)
    except FileExistsError:
        logging.warning("Skipped renaming. File '%s' already exists.", new_filename)
    except FileNotFoundError as e:
        logging.error("File not found: %s", e)
    except PermissionError as e:
        logging.error("Permission denied: %s", e)
    except OSError as e:
        logging.error("OS error occurred: %s", e)


def rename_files_in_current_directory() -> None:
    """
    Rename files in the current directory using multiprocessing for improved performance.
    """
    try:
        current_directory: str = os.getcwd()
        english_dictionary: Set[str] = load_english_dictionary()

        # Setup logging

        log_file = os.path.join(
            current_directory, f"rename_{datetime.datetime.now():%Y-%m-%d}.log"
        )
        logging.basicConfig(
            filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s"
        )

        # Get list of files to rename

        files_to_rename = [
            filename
            for filename in os.listdir(current_directory)
            if filename.endswith(".pdf")
        ]

        # Rename files in parallel using multiprocessing

        with Pool(cpu_count()) as pool:
            pool.starmap(
                rename_file,
                [(filename, english_dictionary) for filename in files_to_rename],
            )
    except FileNotFoundError as e:
        logging.error("File not found: %s", e)
    except PermissionError as e:
        logging.error("Permission denied: %s", e)
    except OSError as e:
        logging.error("OS error occurred: %s", e)


if __name__ == "__main__":
    rename_files_in_current_directory()
