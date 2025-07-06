"""
PDF Linearizer Module

This module provides functionality to optimize PDF files for web viewing by linearizing them.
It recursively processes PDF files in a directory structure, making them more efficient for
web delivery and faster initial page loading.

The module uses qpdf to perform the linearization and includes features for:
- Recursive directory scanning
- Dry-run mode for testing
- File filtering capabilities
- Detailed logging of changes
- User confirmation before processing

Dependencies:
    - qpdf: External command-line tool for PDF processing
    - Python standard library: os, subprocess, datetime

Example:
    >>> linearizer = PDFLinearizer(dry_run=True)
    >>> linearizer.run()
"""

import os
import subprocess
from datetime import datetime
from typing import Callable, Optional


class PDFLinearizer:
    """
    Recursively finds and linearizes all PDF files in a directory subtree using qpdf.
    Logs file changes (size and timestamp) to 'fastviewpdf.log'. Supports dry-run mode and file filtering.
    """

    def __init__(
        self,
        root_dir: Optional[str] = None,
        log_file: str = "fastviewpdf.log",
        dry_run: bool = False,
        file_filter: Optional[Callable[[str], bool]] = None,
    ):
        """
        Initialize the PDFLinearizer.

        Parameters:
            root_dir (str): Directory to scan. Defaults to current working directory.
            log_file (str): Name of the log file. Defaults to 'fastviewpdf.log'.
            dry_run (bool): If True, simulate changes without modifying any files.
            file_filter (Callable): Optional predicate function to filter PDFs.
        """
        self.root_dir = root_dir if root_dir else os.getcwd()
        self.log_path = os.path.join(self.root_dir, log_file)
        self.dry_run = dry_run
        self.file_filter = file_filter
        self.pdf_files = []

    def collect_pdfs(self):
        """
        Recursively collect all .pdf files under root_dir,
        applying the optional file_filter predicate if provided.
        """
        for dirpath, _, filenames in os.walk(self.root_dir):
            for filename in filenames:
                if filename.lower().endswith(".pdf"):
                    full_path = os.path.join(dirpath, filename)
                    if self.file_filter is None or self.file_filter(full_path):
                        self.pdf_files.append(full_path)

    def get_metadata(self, path: str):
        """
        Get file size and modification time of the file.

        Parameters:
            path (str): Path to the file.

        Returns:
            dict: Dictionary with 'size' and 'mtime' keys.
        """
        stat = os.stat(path)
        return {
            "size": stat.st_size,
            "mtime": stat.st_mtime,
        }

    def log_change(self, path: str, before: dict, after: dict):
        """
        Append the change in metadata of the file to the log file.

        Parameters:
            path (str): File path.
            before (dict): Metadata before change.
            after (dict): Metadata after change.
        """
        with open(self.log_path, "a") as log:
            log.write(f"File: {path}\n")
            log.write(
                f"Before - Size: {before['size']} bytes, Modified: {datetime.fromtimestamp(before['mtime'])}\n"
            )
            log.write(
                f"After  - Size: {after['size']} bytes, Modified: {datetime.fromtimestamp(after['mtime'])}\n"
            )
            log.write("-" * 60 + "\n")

    def log_dry_run(self, path: str, before: dict):
        """
        Log the dry-run action for a file.

        Parameters:
            path (str): File path.
            before (dict): File metadata.
        """
        with open(self.log_path, "a") as log:
            log.write(f"[DRY RUN] File: {path}\n")
            log.write(
                f"Simulated linearization. Current Size: {before['size']} bytes, "
                f"Modified: {datetime.fromtimestamp(before['mtime'])}\n"
            )
            log.write("-" * 60 + "\n")

    def linearize(self, path: str):
        """
        Run qpdf to linearize the PDF and replace it in-place, or simulate if dry_run is True.

        Parameters:
            path (str): Path to the PDF file.
        """
        before = self.get_metadata(path)

        if self.dry_run:
            self.log_dry_run(path, before)
            return

        try:
            subprocess.run(["qpdf", "--linearize", "--replace-input", path], check=True)
            after = self.get_metadata(path)
            self.log_change(path, before, after)
        except subprocess.CalledProcessError as e:
            with open(self.log_path, "a") as log:
                log.write(f"Failed to process {path}: {e}\n")
                log.write("-" * 60 + "\n")

    def confirm(self) -> bool:
        """
        Ask the user for confirmation before proceeding.

        Returns:
            bool: True if user confirms, else False.
        """
        print(f"Found {len(self.pdf_files)} PDF files under {self.root_dir}.")
        if self.dry_run:
            print("Dry run mode is enabled. No files will be modified.")
        response = input("Are you sure you want to proceed? [y/N]: ").strip().lower()
        return response == "y"

    def run(self):
        """
        Execute the full linearization or dry-run process.
        """
        self.collect_pdfs()

        if not self.pdf_files:
            print("No PDF files found.")
            return

        if not self.confirm():
            print("Aborted.")
            return

        for path in self.pdf_files:
            self.linearize(path)


if __name__ == "__main__":
    # Example: Filter only PDFs greater than 100KB
    # def size_filter(path): return os.path.getsize(path) > 100 * 1024

    linearizer = PDFLinearizer(
        dry_run=False, file_filter=None  # Replace with size_filter or other predicate
    )
    linearizer.run()
