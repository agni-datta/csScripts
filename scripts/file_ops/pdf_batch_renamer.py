#!/usr/bin/env python3
"""Batch-rename PDF files by splitting camelCase tokens into readable words.

Parses each PDF filename, splits camelCase and acronym sequences into
individual words, validates each word against an English dictionary (powered
by ``pyspellchecker``), and reassembles a clean, human-readable filename.
Processing runs in parallel across CPU cores for large batches.

Usage::

    # Interactive (processes current directory)
    cs-pdf-renamer

    # Library usage
    >>> from scripts.file_ops.pdf_batch_renamer import PdfBatchRenamingService
    >>> PdfBatchRenamingService().execute_renaming_process()

Dependencies:
    pyspellchecker >= 0.7  (``pip install pyspellchecker``)

Example::

    $ cs-pdf-renamer
    Processing /path/to/docs ...
    Renamed: zkSNARKsAndBlockchain.pdf -> zk SNARKs And Blockchain.pdf
    ...
"""

import datetime
import logging
from multiprocessing import cpu_count
from multiprocessing import Pool
import os
import re
from typing import List, Optional, Set

from spellchecker import SpellChecker


class EnglishDictionaryProvider:
    """
    Provider for English dictionary words and specialized terms.
    """

    def __init__(self):
        """
        Initialize the EnglishDictionaryProvider with a loaded dictionary.
        """
        self.english_word_collection: Set[str] = (
            self._load_comprehensive_english_dictionary()
        )

    def _load_comprehensive_english_dictionary(self) -> Set[str]:
        """
        Load a comprehensive dictionary of English words including specialized terms.

        Returns:
            Set of English words and specialized terms.
        """
        spell_checker: SpellChecker = SpellChecker()
        english_word_collection: Set[str] = set(spell_checker.word_frequency.keys())

        technical_terms = {
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

        technical_terms_title_case = set(term.title() for term in technical_terms)

        english_word_collection.update(technical_terms_title_case)
        english_word_collection.update(roman_numerals)

        return english_word_collection


class LoggingConfigurationService:
    """
    Service for configuring and managing logging operations.
    """

    @staticmethod
    def configure_logging_system(log_file_path: str) -> None:
        """
        Configure the logging system for the application.

        Args:
            log_file_path: Path to the log file.
        """
        logging.basicConfig(
            filename=log_file_path,
            level=logging.INFO,
            format="%(asctime)s - %(message)s",
        )


class FilenameTransformationService:
    """
    Service for transforming filenames according to specified rules.
    """

    def __init__(self, english_dictionary_provider: EnglishDictionaryProvider):
        """
        Initialize the FilenameTransformationService.

        Args:
            english_dictionary_provider: Provider of English dictionary words.
        """
        self.english_word_collection = (
            english_dictionary_provider.english_word_collection
        )
        self.non_capitalized_words = self._get_non_capitalized_words()

    def _get_non_capitalized_words(self) -> Set[str]:
        """
        Get a set of words that should not be capitalized in titles.

        Returns:
            Set of words that should remain lowercase in titles (except at the beginning).
        """
        return set(
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
                "before",
                "behind",
                "below",
                "beneath",
                "beside",
                "between",
                "beyond",
                "concerning",
                "considering",
            ]
        )

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Remove special characters from a filename.

        Args:
            filename: The filename to sanitize.

        Returns:
            Sanitized filename without special characters.
        """
        return re.sub(r'[\\/;:\'"`%$#@!*+=]', "", filename)

    def transform_filename(self, original_filename: str) -> str:
        """
        Transform a filename by splitting concatenated words and applying proper formatting.

        Args:
            original_filename: The original filename to transform.

        Returns:
            Transformed filename.

        Raises:
            ValueError: If the filename is empty.
        """
        if not original_filename:
            raise ValueError("Filename cannot be empty.")

        sanitized_filename = self.sanitize_filename(original_filename)

        sanitized_filename = sanitized_filename.replace(" And ", " & ")

        base_filename, file_extension = os.path.splitext(sanitized_filename)

        extracted_words: List[str] = re.findall(
            r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|[^\W_]+", base_filename
        )

        for word_index, word in enumerate(extracted_words):
            if word_index == 0:
                extracted_words[word_index] = word.title()
            elif word.lower() in self.non_capitalized_words:
                extracted_words[word_index] = word.lower()
            elif word.lower() not in self.english_word_collection:
                extracted_words[word_index] = word.title()
            else:
                extracted_words[word_index] = word.title()

        transformed_base_filename = "_".join(extracted_words)

        transformed_filename = f"{transformed_base_filename}{file_extension}"

        return transformed_filename


class FileSystemOperationService:
    """
    Service for performing file system operations.
    """

    @staticmethod
    def rename_file(
        directory_path: str, original_filename: str, new_filename: str
    ) -> bool:
        """
        Rename a file and handle potential errors.

        Args:
            directory_path: Directory containing the file.
            original_filename: Current filename.
            new_filename: New filename.

        Returns:
            True if renaming was successful, False otherwise.
        """
        try:
            original_file_path = os.path.join(directory_path, original_filename)
            new_file_path = os.path.join(directory_path, new_filename)

            if original_file_path == new_file_path:
                return False

            os.rename(original_file_path, new_file_path)
            logging.info("Renamed '%s' to '%s'", original_filename, new_filename)
            return True

        except FileExistsError:
            logging.warning("Skipped renaming. File '%s' already exists.", new_filename)
            return False
        except FileNotFoundError as error:
            logging.error("File not found: %s", error)
            return False
        except PermissionError as error:
            logging.error("Permission denied: %s", error)
            return False
        except OSError as error:
            logging.error("OS error occurred: %s", error)
            return False

    @staticmethod
    def find_pdf_files_in_directory(directory_path: str) -> List[str]:
        """
        Find all PDF files in a directory.

        Args:
            directory_path: Directory to search for PDF files.

        Returns:
            List of PDF filenames found in the directory.
        """
        try:
            return [
                filename
                for filename in os.listdir(directory_path)
                if filename.endswith(".pdf")
            ]
        except FileNotFoundError as error:
            logging.error("Directory not found: %s", error)
            return []
        except PermissionError as error:
            logging.error("Permission denied when accessing directory: %s", error)
            return []
        except OSError as error:
            logging.error("OS error when accessing directory: %s", error)
            return []


class ParallelProcessingService:
    """
    Service for executing operations in parallel using multiprocessing.
    """

    @staticmethod
    def process_files_in_parallel(processing_function, file_list: List[str]) -> None:
        """
        Process a list of files in parallel using multiprocessing.

        Args:
            processing_function: Function to apply to each file.
            file_list: List of files to process.
        """
        with Pool(cpu_count()) as process_pool:
            process_pool.map(processing_function, file_list)


class PdfBatchRenamingService:
    """
    Service for batch renaming PDF files according to specified rules.
    """

    def __init__(self, target_directory_path: Optional[str] = None):
        """
        Initialize the PdfBatchRenamingService.

        Args:
            target_directory_path: Directory containing PDF files to rename.
                                  If None, uses the current working directory.
        """
        self.target_directory_path = target_directory_path or os.getcwd()

        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.log_file_path = os.path.join(
            self.target_directory_path, f"rename_{current_date}.log"
        )

        self.dictionary_provider = EnglishDictionaryProvider()
        self.logging_service = LoggingConfigurationService()
        self.transformation_service = FilenameTransformationService(
            self.dictionary_provider
        )
        self.file_system_service = FileSystemOperationService()
        self.parallel_processing_service = ParallelProcessingService()

        self.logging_service.configure_logging_system(self.log_file_path)

    def _rename_single_file(self, filename: str) -> None:
        """
        Rename a single PDF file.

        Args:
            filename: Name of the file to rename.
        """
        try:
            transformed_filename = self.transformation_service.transform_filename(
                filename
            )
            self.file_system_service.rename_file(
                self.target_directory_path, filename, transformed_filename
            )
        except Exception as error:
            logging.error("Error processing file '%s': %s", filename, error)

    def execute_renaming_process(self) -> None:
        """
        Execute the PDF batch renaming process.
        """
        try:
            pdf_files = self.file_system_service.find_pdf_files_in_directory(
                self.target_directory_path
            )

            if not pdf_files:
                logging.info("No PDF files found in %s", self.target_directory_path)
                return

            logging.info("Found %d PDF files to process", len(pdf_files))

            self.parallel_processing_service.process_files_in_parallel(
                self._rename_single_file, pdf_files
            )

            logging.info("PDF batch renaming process completed")

        except Exception as error:
            logging.error("Error during batch renaming process: %s", error)


class PdfBatchRenamingApplicationLauncher:
    """
    Launcher for the PDF batch renaming application.
    """

    @staticmethod
    def launch_application(target_directory_path: Optional[str] = None) -> None:
        """
        Launch the PDF batch renaming application.

        Args:
            target_directory_path: Directory containing PDF files to rename.
                                  If None, uses the current working directory.
        """
        renaming_service = PdfBatchRenamingService(target_directory_path)
        renaming_service.execute_renaming_process()


def main() -> None:
    """
    Main entry point for the PDF batch renamer script.
    """
    application_launcher = PdfBatchRenamingApplicationLauncher()
    application_launcher.launch_application()


if __name__ == "__main__":
    main()
