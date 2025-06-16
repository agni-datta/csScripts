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
    >>> converter = PS2PDFConverter()
    >>> converter.convert_file("input.ps", "output.pdf")
"""

import logging
import os
from pathlib import Path
from subprocess import CalledProcessError, run


class PSConverter:
    """
    A class to handle the conversion of PostScript (.ps) files to PDF, including TeX font embedding.

    Attributes
    ----------
    input_directory : Path
        Path to the directory containing PostScript (.ps) files.
    output_directory : Path
        Path to the directory where the output PDF files will be saved.

    Methods
    -------
    convert_all():
        Converts all .ps files in the input directory to .pdf files in the output directory.
    """

    def __init__(self, output_directory: Path):
        """
        Initializes the PSConverter with the output directory path.

        Parameters
        ----------
        output_directory : Path
            The path to the directory where PDF files will be saved.
        """
        self.input_directory = Path.cwd()
        self.output_directory = output_directory
        self._setup_logging()

    def _setup_logging(self):
        """Sets up logging to provide feedback during execution."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )

    def _convert_file(self, input_file: Path, output_file: Path):
        """
        Converts a single .ps file to .pdf.

        Parameters
        ----------
        input_file : Path
            The path to the input PostScript (.ps) file.
        output_file : Path
            The path to the output PDF file.
        """
        logging.info(f"Starting conversion of {input_file} to {output_file}")

        try:
            run(
                [
                    "gs",
                    "-dPDFSETTINGS=/prepress",
                    "-dEmbedAllFonts=true",
                    "-dSubsetFonts=true",
                    "-dCompressFonts=true",
                    "-sDEVICE=pdfwrite",
                    "-o",
                    str(output_file),
                    str(input_file),
                ],
                check=True,
            )

            logging.info(f"Successfully converted {input_file} to {output_file}.")

        except CalledProcessError as e:
            logging.error(f"Conversion failed for {input_file}: {e}")
            raise e

    def convert_all(self):
        """Converts all .ps files in the input directory to .pdf files in the output directory."""
        if not self.output_directory.exists():
            self.output_directory.mkdir(parents=True, exist_ok=True)

        for ps_file in self.input_directory.glob("*.ps"):
            pdf_file = self.output_directory / f"{ps_file.stem}.pdf"
            self._convert_file(ps_file, pdf_file)


def main():
    """
    Main function to convert all .ps files in the current directory to .pdf files in a specified directory.
    """
    output_directory = Path("pdf_output")  # Specify your output directory here
    converter = PSConverter(output_directory)
    converter.convert_all()


if __name__ == "__main__":
    main()
