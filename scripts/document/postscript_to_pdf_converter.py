#!/usr/bin/env python3
"""Convert PostScript (``.ps``) files to PDF using Ghostscript.

Finds all ``.ps`` files in the current working directory and converts them to
PDF with high-quality prepress settings (embedded fonts, subsetting,
compression).  Output PDFs are written to a ``pdf_output/`` subdirectory by
default.

Usage::

    # Convert all .ps files in the current directory
    python -m scripts.document.postscript_to_pdf_converter

    # Library usage with a custom output directory
    >>> from pathlib import Path
    >>> from scripts.document.postscript_to_pdf_converter import (
    ...     PostscriptToPdfConversionService
    ... )
    >>> PostscriptToPdfConversionService(Path("out")).convert_all_files_in_directory()

Dependencies:
    ``gs`` (Ghostscript) must be on ``$PATH``.  Install with
    ``brew install ghostscript`` or ``sudo apt install ghostscript``.

Example::

    $ cd ~/papers && python -m scripts.document.postscript_to_pdf_converter
    INFO - Found 2 PostScript files to convert
    INFO - Successfully converted draft.ps to pdf_output/draft.pdf
    INFO - Conversion complete: 2 successful, 0 failed
"""

import logging
from pathlib import Path
from subprocess import CalledProcessError
from subprocess import run
from typing import List, Optional


class LoggingConfigurationService:
    """
    Service for configuring and managing logging operations.
    """

    @staticmethod
    def configure_logging_system() -> None:
        """Configure the logging system for the application.

        Sets up logging with appropriate format and handlers to provide
        feedback during execution.
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )


class GhostscriptConversionService:
    """
    Service for converting PostScript files to PDF using Ghostscript.
    """

    @staticmethod
    def convert_postscript_to_pdf(
        input_file_path: Path, output_file_path: Path
    ) -> bool:
        """Convert a single PostScript file to PDF using Ghostscript.

        Args:
            input_file_path: Path to the input PostScript file.
            output_file_path: Path where the output PDF file will be saved.

        Returns:
            True if conversion was successful, False otherwise.
        """
        logging.info(f"Starting conversion of {input_file_path} to {output_file_path}")

        try:
            run(
                [
                    "gs",
                    "-dPDFSETTINGS=/prepress",  # High-quality output for prepress
                    "-dEmbedAllFonts=true",  # Embed all fonts in the PDF
                    "-dSubsetFonts=true",  # Use font subsetting for smaller files
                    "-dCompressFonts=true",  # Compress embedded fonts
                    "-sDEVICE=pdfwrite",  # Use PDF writer device
                    "-o",  # Output file flag
                    str(output_file_path),  # Output file path
                    str(input_file_path),  # Input file path
                ],
                check=True,  # Raise exception on error
                capture_output=True,  # Capture output for logging
            )

            logging.info(
                f"Successfully converted {input_file_path} to {output_file_path}"
            )
            return True

        except CalledProcessError as conversion_error:
            logging.error(
                f"Conversion failed for {input_file_path}: {conversion_error}"
            )
            return False


class FileSystemOperationService:
    """
    Service for performing file system operations.
    """

    @staticmethod
    def ensure_directory_exists(directory_path: Path) -> None:
        """Ensure that a directory exists, creating it if necessary.

        Args:
            directory_path: Path to the directory to ensure exists.
        """
        if not directory_path.exists():
            directory_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created directory: {directory_path}")

    @staticmethod
    def find_postscript_files(directory_path: Path) -> List[Path]:
        """Find all PostScript files in a directory.

        Args:
            directory_path: Path to the directory to search.

        Returns:
            List of paths to PostScript files found.
        """
        return list(directory_path.glob("*.ps"))


class PostscriptToPdfConversionService:
    """
    Service for converting PostScript files to PDF format.
    """

    def __init__(self, output_directory_path: Optional[Path] = None):
        """
        Initialize the PostscriptToPdfConversionService.

        Args:
            output_directory_path: Path to the directory where PDF files will be saved.
                                  If None, uses "pdf_output" in the current directory.
        """
        self.source_directory_path = Path.cwd()
        self.output_directory_path = output_directory_path or Path("pdf_output")

        self.logging_service = LoggingConfigurationService()
        self.conversion_service = GhostscriptConversionService()
        self.file_system_service = FileSystemOperationService()

        self.logging_service.configure_logging_system()

    def convert_single_file(
        self, input_file_path: Path, output_file_path: Path
    ) -> bool:
        """Convert a single PostScript file to PDF.

        Args:
            input_file_path: Path to the input PostScript file.
            output_file_path: Path where the output PDF file will be saved.

        Returns:
            True if conversion was successful, False otherwise.
        """
        self.file_system_service.ensure_directory_exists(output_file_path.parent)

        return self.conversion_service.convert_postscript_to_pdf(
            input_file_path, output_file_path
        )

    def convert_all_files_in_directory(self) -> None:
        """Convert all PostScript files in the source directory to PDF files in the output directory."""
        self.file_system_service.ensure_directory_exists(self.output_directory_path)

        postscript_files = self.file_system_service.find_postscript_files(
            self.source_directory_path
        )

        if not postscript_files:
            logging.info(f"No PostScript files found in {self.source_directory_path}")
            return

        logging.info(f"Found {len(postscript_files)} PostScript files to convert")

        successful_conversions = 0
        failed_conversions = 0

        for postscript_file_path in postscript_files:
            pdf_file_path = (
                self.output_directory_path / f"{postscript_file_path.stem}.pdf"
            )

            if self.convert_single_file(postscript_file_path, pdf_file_path):
                successful_conversions += 1
            else:
                failed_conversions += 1

        logging.info(
            f"Conversion complete: {successful_conversions} successful, {failed_conversions} failed"
        )


class PostscriptToPdfConversionApplicationLauncher:
    """
    Launcher for the PostScript to PDF conversion application.
    """

    @staticmethod
    def launch_application(output_directory_path: Optional[Path] = None) -> None:
        """Launch the PostScript to PDF conversion application.

        Args:
            output_directory_path: Path to the directory where PDF files will be saved.
                                  If None, uses "pdf_output" in the current directory.
        """
        conversion_service = PostscriptToPdfConversionService(output_directory_path)
        conversion_service.convert_all_files_in_directory()


def main() -> None:
    """
    Main entry point for the PostScript to PDF converter script.
    """
    output_directory_path = Path("pdf_output")  # Default output directory
    application_launcher = PostscriptToPdfConversionApplicationLauncher()
    application_launcher.launch_application(output_directory_path)


if __name__ == "__main__":
    main()
