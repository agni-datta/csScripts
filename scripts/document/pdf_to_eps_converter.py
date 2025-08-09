#!/usr/bin/env python3
"""
PDF to EPS Converter Module.

This module provides a modular, object-oriented interface for converting PDF files to EPS format
using Ghostscript. It features colorized terminal output and a progress bar.

Author: Agni Datta
Date: 2024-07-12
Version: 2.2.0
"""

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class TerminalColor:
    """ANSI color codes for terminal output."""

    HEADER: str = "\033[95m"
    OKBLUE: str = "\033[94m"
    OKCYAN: str = "\033[96m"
    OKGREEN: str = "\033[92m"
    WARNING: str = "\033[93m"
    FAIL: str = "\033[91m"
    BOLD: str = "\033[1m"
    UNDERLINE: str = "\033[4m"
    ENDC: str = "\033[0m"
    GREY: str = "\033[90m"


def color_text(text: str, color_code: str) -> str:
    """Wraps text with ANSI color codes.

    Args:
        text (str): The text to colorize.
        color_code (str): The ANSI color code.

    Returns:
        str: Colorized text.
    """
    return f"{color_code}{text}{TerminalColor.ENDC}"


class FileConversionStatus(Enum):
    """Status of a file conversion."""

    SUCCESS: str = "success"
    FAILED: str = "failed"
    SKIPPED: str = "skipped"


@dataclass
class FileConversionResult:
    """Result of a single file conversion.

    Attributes:
        input_file_path (str): Path to the input PDF file.
        output_file_path (str): Path to the output EPS file.
        status (FileConversionStatus): Status of the conversion.
        error_message (Optional[str]): Error message if conversion failed.
        processing_time_seconds (float): Time taken for conversion in seconds.
    """

    input_file_path: str
    output_file_path: str
    status: FileConversionStatus
    error_message: Optional[str] = None
    processing_time_seconds: float = 0.0


class ProgressBar:
    """Simple progress bar for terminal output."""

    def __init__(self, total: int, bar_length: int = 40) -> None:
        """Initializes the progress bar.

        Args:
            total (int): Total number of steps.
            bar_length (int, optional): Length of the progress bar in characters. Defaults to 40.
        """
        self.total: int = total
        self.bar_length: int = bar_length
        self.current: int = 0

    def update(self, current: int, prefix: str = "") -> None:
        """Updates the progress bar.

        Args:
            current (int): Current progress count.
            prefix (str, optional): Optional prefix string. Defaults to "".
        """
        self.current = current
        percent: float = float(self.current) / self.total if self.total else 1.0
        filled_length: int = int(self.bar_length * percent)
        bar: str = color_text("█" * filled_length, TerminalColor.OKGREEN) + "-" * (
            self.bar_length - filled_length
        )
        percent_display: str = f"{percent * 100:5.1f}%"
        print(
            f"\r{prefix} |{bar}| {self.current}/{self.total} {percent_display}",
            end="",
            flush=True,
        )

    def finish(self) -> None:
        """Finishes the progress bar output."""
        print()


def detect_ghostscript_command() -> str:
    """Detects the Ghostscript command for the current platform.

    Returns:
        str: Ghostscript command.

    Raises:
        RuntimeError: If Ghostscript is not available.
    """
    gs_cmd: str = "gswin32c.exe" if os.name == "nt" else "gs"
    try:
        subprocess.run([gs_cmd, "--version"], capture_output=True, check=True)
        return gs_cmd
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError(
            f"Ghostscript not found. Please install Ghostscript and ensure '{gs_cmd}' is available in your PATH."
        )


def run_ghostscript_conversion(
    gs_cmd: str, pdf_path: Path, eps_output_path: Path
) -> None:
    """Runs Ghostscript to convert a PDF to EPS.

    Args:
        gs_cmd (str): Ghostscript command.
        pdf_path (Path): Path to the PDF file.
        eps_output_path (Path): Path to the output EPS file.

    Raises:
        subprocess.CalledProcessError: If Ghostscript fails.
    """
    command: List[str] = [
        gs_cmd,
        "-o",
        str(eps_output_path),
        "-sDEVICE=eps2write",
        str(pdf_path),
    ]
    subprocess.run(command, capture_output=True, text=True, check=True)


def find_pdf_files_in_directory(
    directory_path: str, supported_extensions: List[str]
) -> List[str]:
    """Finds all PDF files in the specified directory.

    Args:
        directory_path (str): Path to the directory.
        supported_extensions (List[str]): List of supported file extensions.

    Returns:
        List[str]: List of PDF file paths.

    Raises:
        ValueError: If the directory does not exist.
    """
    dir_path: Path = Path(directory_path)
    if not dir_path.is_dir():
        raise ValueError(f"Invalid directory path: {directory_path}")
    pdf_files: List[str] = [
        str(file_path)
        for file_path in dir_path.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions
    ]
    return sorted(pdf_files)


class PDFToEPSBatchConverter:
    """Batch PDF to EPS converter with color output and progress bar."""

    def __init__(self, verbose_output: bool = True, dry_run_mode: bool = False) -> None:
        """Initializes the batch converter.

        Args:
            verbose_output (bool, optional): Enable verbose output. Defaults to True.
            dry_run_mode (bool, optional): Perform a dry run without actual conversion. Defaults to False.
        """
        self.verbose_output: bool = verbose_output
        self.dry_run_mode: bool = dry_run_mode
        self.supported_file_extensions: List[str] = [".pdf"]
        self.ghostscript_command: str = detect_ghostscript_command()
        self.conversion_results: List[FileConversionResult] = []

    def _print(self, message: str, color: Optional[str] = None) -> None:
        """Prints a message to the terminal if verbose output is enabled.

        Args:
            message (str): The message to print.
            color (Optional[str], optional): The color code to use. Defaults to None.
        """
        if self.verbose_output:
            print(color_text(message, color) if color else message)

    def convert_single_pdf_to_eps(self, pdf_file_path: str) -> FileConversionResult:
        """Converts a single PDF file to EPS format.

        Args:
            pdf_file_path (str): Path to the PDF file.

        Returns:
            FileConversionResult: The result of the conversion.
        """
        start_time: float = time.time()
        pdf_path: Path = Path(pdf_file_path)
        eps_output_path: Path = pdf_path.with_suffix(".eps")

        if not pdf_path.exists():
            result: FileConversionResult = FileConversionResult(
                input_file_path=str(pdf_file_path),
                output_file_path=str(eps_output_path),
                status=FileConversionStatus.FAILED,
                error_message=f"Input file does not exist: {pdf_file_path}",
            )
            self.conversion_results.append(result)
            return result

        if eps_output_path.exists() and not self.dry_run_mode:
            result: FileConversionResult = FileConversionResult(
                input_file_path=str(pdf_file_path),
                output_file_path=str(eps_output_path),
                status=FileConversionStatus.SKIPPED,
                error_message=f"Output file already exists: {eps_output_path}",
            )
            self.conversion_results.append(result)
            return result

        if self.dry_run_mode:
            result: FileConversionResult = FileConversionResult(
                input_file_path=str(pdf_file_path),
                output_file_path=str(eps_output_path),
                status=FileConversionStatus.SUCCESS,
                processing_time_seconds=time.time() - start_time,
            )
            self.conversion_results.append(result)
            return result

        try:
            run_ghostscript_conversion(
                self.ghostscript_command, pdf_path, eps_output_path
            )
            result: FileConversionResult = FileConversionResult(
                input_file_path=str(pdf_file_path),
                output_file_path=str(eps_output_path),
                status=FileConversionStatus.SUCCESS,
                processing_time_seconds=time.time() - start_time,
            )
            self.conversion_results.append(result)
            return result
        except subprocess.CalledProcessError as e:
            error_msg: str = f"Ghostscript error: {e.stderr}" if e.stderr else str(e)
            result: FileConversionResult = FileConversionResult(
                input_file_path=str(pdf_file_path),
                output_file_path=str(eps_output_path),
                status=FileConversionStatus.FAILED,
                error_message=error_msg,
                processing_time_seconds=time.time() - start_time,
            )
            self.conversion_results.append(result)
            return result
        except Exception as e:
            result: FileConversionResult = FileConversionResult(
                input_file_path=str(pdf_file_path),
                output_file_path=str(eps_output_path),
                status=FileConversionStatus.FAILED,
                error_message=f"Unexpected error: {e}",
                processing_time_seconds=time.time() - start_time,
            )
            self.conversion_results.append(result)
            return result

    def convert_all_pdfs_in_directory(self, directory_path: str) -> Dict[str, Any]:
        """Converts all PDF files in a directory to EPS format.

        Args:
            directory_path (str): Path to the directory containing PDF files.

        Returns:
            Dict[str, Any]: Summary of the conversion operation.
        """
        self._print(f"Scanning directory: {directory_path}", TerminalColor.OKCYAN)
        try:
            pdf_file_paths: List[str] = find_pdf_files_in_directory(
                directory_path, self.supported_file_extensions
            )
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "files_processed": 0,
                "files_successful": 0,
                "files_failed": 0,
                "files_skipped": 0,
            }

        if not pdf_file_paths:
            return {
                "success": True,
                "message": "No PDF files found in the directory",
                "files_processed": 0,
                "files_successful": 0,
                "files_failed": 0,
                "files_skipped": 0,
            }

        self._print(
            f"Found {len(pdf_file_paths)} PDF file(s) to convert", TerminalColor.OKCYAN
        )
        if self.dry_run_mode:
            self._print(
                "DRY RUN MODE: No actual conversion will be performed",
                TerminalColor.WARNING,
            )

        progress_bar: ProgressBar = ProgressBar(total=len(pdf_file_paths))
        for idx, pdf_file_path in enumerate(pdf_file_paths, 1):
            progress_bar.update(idx, prefix="Progress")
            file_name: str = Path(pdf_file_path).name
            result: FileConversionResult = self.convert_single_pdf_to_eps(pdf_file_path)
            self._print_conversion_result(file_name, result)
        progress_bar.finish()

        return self._summarize_results()

    def _print_conversion_result(
        self, file_name: str, result: FileConversionResult
    ) -> None:
        """Prints the result of a single file conversion.

        Args:
            file_name (str): Name of the file.
            result (FileConversionResult): The conversion result.
        """
        if result.status == FileConversionStatus.SUCCESS:
            self._print(f"✓ Successfully converted: {file_name}", TerminalColor.OKGREEN)
        elif result.status == FileConversionStatus.SKIPPED:
            self._print(
                f"⚠ Skipped: {file_name} ({result.error_message})",
                TerminalColor.WARNING,
            )
        else:
            self._print(
                f"✗ Failed: {file_name} ({result.error_message})", TerminalColor.FAIL
            )

    def _summarize_results(self) -> Dict[str, Any]:
        """Summarizes the conversion results.

        Returns:
            Dict[str, Any]: Summary statistics.
        """
        successful: int = sum(
            1
            for r in self.conversion_results
            if r.status == FileConversionStatus.SUCCESS
        )
        failed: int = sum(
            1
            for r in self.conversion_results
            if r.status == FileConversionStatus.FAILED
        )
        skipped: int = sum(
            1
            for r in self.conversion_results
            if r.status == FileConversionStatus.SKIPPED
        )
        total_time: float = sum(
            r.processing_time_seconds for r in self.conversion_results
        )
        return {
            "success": True,
            "files_processed": len(self.conversion_results),
            "files_successful": successful,
            "files_failed": failed,
            "files_skipped": skipped,
            "total_time": total_time,
        }

    def get_conversion_summary(self) -> Dict[str, Any]:
        """Returns a summary of all conversion results.

        Returns:
            Dict[str, Any]: Summary statistics of all conversions.
        """
        if not self.conversion_results:
            return {"message": "No conversions performed"}
        successful: List[FileConversionResult] = [
            r
            for r in self.conversion_results
            if r.status == FileConversionStatus.SUCCESS
        ]
        failed: List[FileConversionResult] = [
            r
            for r in self.conversion_results
            if r.status == FileConversionStatus.FAILED
        ]
        skipped: List[FileConversionResult] = [
            r
            for r in self.conversion_results
            if r.status == FileConversionStatus.SKIPPED
        ]
        total_time: float = sum(
            r.processing_time_seconds for r in self.conversion_results
        )
        return {
            "total_files": len(self.conversion_results),
            "successful": len(successful),
            "failed": len(failed),
            "skipped": len(skipped),
            "success_rate": len(successful) / len(self.conversion_results) * 100,
            "total_time": total_time,
            "average_time": (
                (total_time / len(self.conversion_results))
                if self.conversion_results
                else 0
            ),
        }


class PDFToEPSApplication:
    """Interactive application for PDF to EPS conversion."""

    def __init__(self) -> None:
        """Initializes the PDFToEPSApplication."""
        self.converter: Optional[PDFToEPSBatchConverter] = None

    def run(self) -> None:
        """Runs the interactive application."""
        self._print_header()
        directory_path: str = self._prompt_directory_path()
        self._initialize_converter()
        result: Dict[str, Any] = self.converter.convert_all_pdfs_in_directory(
            directory_path
        )
        self._handle_result(result)

    def _print_header(self) -> None:
        """Prints the application header."""
        print(
            color_text(
                "PDF to EPS Converter", TerminalColor.HEADER + TerminalColor.BOLD
            )
        )
        print(color_text("=" * 50, TerminalColor.GREY))

    def _prompt_directory_path(self) -> str:
        """Prompts the user for the directory path.

        Returns:
            str: The directory path entered by the user.
        """
        return input(
            color_text(
                "Enter the directory path containing PDF files: ", TerminalColor.OKBLUE
            )
        ).strip()

    def _initialize_converter(self) -> None:
        """Initializes the batch converter, handling errors."""
        try:
            self.converter = PDFToEPSBatchConverter(verbose_output=True)
        except RuntimeError as e:
            print(color_text(f"Error: {e}", TerminalColor.FAIL))
            sys.exit(1)

    def _handle_result(self, result: Dict[str, Any]) -> None:
        """Handles and prints the result summary.

        Args:
            result (Dict[str, Any]): The result dictionary from the conversion.
        """
        if not result.get("success", False):
            print(
                color_text(
                    f"Error: {result.get('error', 'Unknown error')}", TerminalColor.FAIL
                )
            )
            sys.exit(1)

        print("\n" + color_text("=" * 50, TerminalColor.GREY))
        print(
            color_text("Conversion Summary:", TerminalColor.BOLD + TerminalColor.OKCYAN)
        )
        print(f"  Files processed: {result['files_processed']}")
        print(
            color_text(
                f"  Successful: {result['files_successful']}", TerminalColor.OKGREEN
            )
        )
        print(
            color_text(
                f"  Failed: {result['files_failed']}",
                TerminalColor.FAIL if result["files_failed"] else TerminalColor.OKGREEN,
            )
        )
        print(
            color_text(
                f"  Skipped: {result['files_skipped']}",
                (
                    TerminalColor.WARNING
                    if result["files_skipped"]
                    else TerminalColor.OKGREEN
                ),
            )
        )
        if result["files_processed"] > 0:
            print(f"  Total time: {result['total_time']:.2f} seconds")
            print(
                f"  Average time per file: {result['total_time'] / result['files_processed']:.2f} seconds"
            )


def main() -> None:
    """Main entrypoint for the application."""
    app: PDFToEPSApplication = PDFToEPSApplication()
    app.run()


if __name__ == "__main__":
    main()
