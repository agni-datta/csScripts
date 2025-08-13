#!/usr/bin/env python3
"""
PostScript to PDF Converter Module

This module provides functionality to convert PostScript (.ps) files to PDF format.
It uses Ghostscript (gs) as the underlying conversion engine and includes features for:
- Batch conversion of multiple files
- Quality and compression settings
- Output directory management
- Progress tracking
- Error handling and logging

The converter can be used both as a command-line tool and as a library in other Python
projects. It's particularly useful for converting legacy PostScript documents to
the more widely supported PDF format.

Dependencies:
    - Ghostscript (gs): External command-line tool for PostScript processing
    - Python standard library: os, subprocess

Example:
    >>> service = PostscriptToPdfConversionService()
    >>> service.convert_single_file("input.ps", "output.pdf")
"""

import logging
from pathlib import Path
from subprocess import CalledProcessError, run
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
            # Execute Ghostscript with high-quality settings for PDF conversion
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

        # Initialize services
        self.logging_service = LoggingConfigurationService()
        self.conversion_service = GhostscriptConversionService()
        self.file_system_service = FileSystemOperationService()

        # Configure logging
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
        # Ensure output directory exists
        self.file_system_service.ensure_directory_exists(output_file_path.parent)

        # Perform conversion
        return self.conversion_service.convert_postscript_to_pdf(
            input_file_path, output_file_path
        )

    def convert_all_files_in_directory(self) -> None:
        """Convert all PostScript files in the source directory to PDF files in the output directory."""
        # Ensure output directory exists
        self.file_system_service.ensure_directory_exists(self.output_directory_path)

        # Find all PostScript files
        postscript_files = self.file_system_service.find_postscript_files(
            self.source_directory_path
        )

        if not postscript_files:
            logging.info(f"No PostScript files found in {self.source_directory_path}")
            return

        logging.info(f"Found {len(postscript_files)} PostScript files to convert")

        # Convert each file
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

        # Log summary
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
