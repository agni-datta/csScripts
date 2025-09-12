#!/usr/bin/env python3
"""Interactive File Extension Checker.

A tool to check if all files in a directory have proper extensions
and not malformed extensions like .ext.ext or other variations.
Supports any file extension and provides both interactive and batch modes.

Example usage:
    Interactive mode:
        python3 check_extensions.py

    Batch mode:
        python3 check_extensions.py mp3 /path/to/music
        python3 check_extensions.py --version
        python3 check_extensions.py --help
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Tuple

__version__ = "2.0.0"
__author__ = "File Extension Checker"


class ExtensionCheckResult:
    """Represents the result of an extension check operation.

    Attributes:
        success: Whether all files passed the extension check.
        proper_files: List of files with correct extensions.
        other_files: List of files with different extensions.
        issues: List of problematic files with malformed extensions.
        total_files: Total number of files processed.
    """

    def __init__(self):
        self.success = True
        self.proper_files = []
        self.other_files = []
        self.issues = []
        self.total_files = 0


class FileExtensionChecker:
    """A class to check file extensions in directories.

    This class provides functionality to scan directories for files with
    specific extensions and identify potential issues like double extensions
    or extensions in wrong positions.
    """

    SCRIPT_NAMES = ["check_extensions.py", "check_mp3_extensions.py"]
    MAX_DISPLAY_FILES = 10

    def __init__(self, extension: str, directory: str = "."):
        """Initialize the extension checker.

        Args:
            extension: The file extension to check (without leading dot).
            directory: The directory to scan (default: current directory).
        """
        self.extension = extension.lower().lstrip(".")
        self.directory = Path(directory)

    def check_extensions(self) -> ExtensionCheckResult:
        """Check all files in the directory for proper extensions.

        Returns:
            ExtensionCheckResult: Object containing the results of the check.

        Raises:
            PermissionError: If directory cannot be accessed.
            FileNotFoundError: If directory does not exist.
        """
        result = ExtensionCheckResult()

        try:
            files = [f for f in self.directory.iterdir() if f.is_file()]
        except PermissionError as e:
            raise PermissionError(
                f"Permission denied accessing directory: {self.directory}"
            ) from e
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Directory not found: {self.directory}") from e

        result.total_files = len(files)

        for file_path in sorted(files):
            self._classify_file(file_path.name, result)

        result.success = len(result.issues) == 0
        return result

    def _classify_file(self, filename: str, result: ExtensionCheckResult) -> None:
        """Classify a file based on its extension.

        Args:
            filename: The name of the file to classify.
            result: The result object to update.
        """
        # Skip the script itself
        if filename in self.SCRIPT_NAMES:
            return

        filename_lower = filename.lower()
        double_ext = f".{self.extension}.{self.extension}"
        ext_in_middle = f".{self.extension}."
        proper_ext = f".{self.extension}"

        if filename_lower.endswith(double_ext):
            result.issues.append(f"Double extension: {filename}")
        elif ext_in_middle in filename_lower and not filename_lower.endswith(
            proper_ext
        ):
            result.issues.append(
                f"{self.extension.upper()} extension in middle: {filename}"
            )
        elif filename_lower.endswith(proper_ext):
            result.proper_files.append(filename)
        else:
            result.other_files.append(filename)


class ExtensionCheckerUI:
    """User interface for the file extension checker.

    Handles both interactive and batch mode operations, including
    user input validation and result display.
    """

    def __init__(self):
        self.checker = None

    def run_interactive_mode(self) -> None:
        """Run the checker in interactive mode with user prompts."""
        self._print_header("Interactive File Extension Checker")
        print("[TIP] Type ':q' at any prompt to quit")

        while True:
            try:
                extension, directory = self._get_user_input()
                self._run_check(extension, directory)

                if not self._ask_continue():
                    print("Goodbye!")
                    break

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except SystemExit:
                # User entered ':q', already handled in the method that raised it
                break
            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                try:
                    if not self._ask_retry():
                        print("Goodbye!")
                        break
                except EOFError:
                    print("\nGoodbye!")
                    break

    def run_batch_mode(self, extension: str, directory: str = ".") -> bool:
        """Run the checker in batch mode.

        Args:
            extension: The file extension to check.
            directory: The directory to scan.

        Returns:
            True if no issues were found, False otherwise.
        """
        self._print_header(f"Batch Mode: Checking .{extension.lstrip('.')} files")
        return self._run_check(extension, directory)

    def _get_user_input(self) -> Tuple[str, str]:
        """Get extension and directory input from user.

        Returns:
            Tuple of (extension, directory).

        Raises:
            SystemExit: If user enters ':q' to quit.
            EOFError: If input stream ends unexpectedly.
        """
        while True:
            try:
                extension = input(
                    "Enter file extension to check (e.g., mp3, jpg, txt) or ':q' to quit: "
                ).strip()
                if extension == ":q":
                    print("Goodbye!")
                    raise SystemExit(0)
                if extension:
                    break
                print("Please enter a valid extension.")
            except EOFError:
                raise EOFError("Input stream ended unexpectedly")

        default_dir = os.getcwd()
        try:
            directory = input(
                f"Enter directory path (press Enter for current directory '{default_dir}') or ':q' to quit: "
            ).strip()
            if directory == ":q":
                print("Goodbye!")
                raise SystemExit(0)
            if not directory:
                directory = default_dir
        except EOFError:
            raise EOFError("Input stream ended unexpectedly")

        return extension, directory

    def _run_check(self, extension: str, directory: str) -> bool:
        """Run the extension check and display results.

        Args:
            extension: The file extension to check.
            directory: The directory to scan.

        Returns:
            True if no issues were found, False otherwise.
        """
        try:
            self.checker = FileExtensionChecker(extension, directory)
            result = self.checker.check_extensions()
            self._display_results(result, extension, directory)
            return result.success
        except (PermissionError, FileNotFoundError) as e:
            print(f"Error: {e}")
            return False

    def _display_results(
        self, result: ExtensionCheckResult, extension: str, directory: str
    ) -> None:
        """Display the results of the extension check.

        Args:
            result: The check result to display.
            extension: The extension that was checked.
            directory: The directory that was scanned.
        """
        ext = extension.lstrip(".")
        abs_path = Path(directory).absolute()

        print(f"\nChecking .{ext} files in: {abs_path}")
        print("-" * 60)

        if result.total_files == 0:
            print("No files found in directory.")
            return

        # Display proper files
        print(f"[OK] Proper .{ext} files: {len(result.proper_files)}")
        self._display_file_list(result.proper_files)

        # Display other files
        if result.other_files:
            print(f"\n[INFO] Non-.{ext} files: {len(result.other_files)}")
            self._display_file_list(result.other_files)

        # Display issues
        if result.issues:
            print(f"\n[ERROR] Issues found: {len(result.issues)}")
            for issue in result.issues:
                print(f"   {issue}")
        else:
            print(f"\n[OK] All .{ext} files have proper extensions!")

        # Display summary
        print("\n" + "=" * 60)
        if result.success:
            print("RESULT: [OK] No extension issues found!")
        else:
            print("RESULT: [ERROR] Extension issues detected!")
            print(f"Found {len(result.issues)} problem(s) that need attention.")

    def _display_file_list(self, files: List[str]) -> None:
        """Display a list of files, truncating if too long.

        Args:
            files: List of filenames to display.
        """
        if not files:
            return

        display_files = files[: FileExtensionChecker.MAX_DISPLAY_FILES]
        for file in display_files:
            print(f"   {file}")

        if len(files) > FileExtensionChecker.MAX_DISPLAY_FILES:
            remaining = len(files) - FileExtensionChecker.MAX_DISPLAY_FILES
            print(f"   ... and {remaining} more files")

    def _ask_continue(self) -> bool:
        """Ask user if they want to check another extension/directory.

        Returns:
            True if user wants to continue, False otherwise.

        Raises:
            SystemExit: If user enters ':q' to quit.
            EOFError: If input stream ends unexpectedly.
        """
        print("\n" + "-" * 40)
        try:
            response = (
                input("Check another extension/directory? (y/N) or ':q' to quit: ")
                .strip()
                .lower()
            )
            if response == ":q":
                print("Goodbye!")
                raise SystemExit(0)
            return response in ["y", "yes"]
        except EOFError:
            raise EOFError("Input stream ended unexpectedly")

    def _ask_retry(self) -> bool:
        """Ask user if they want to retry after an error.

        Returns:
            True if user wants to retry, False otherwise.

        Raises:
            SystemExit: If user enters ':q' to quit.
            EOFError: If input stream ends unexpectedly.
        """
        try:
            response = input("Try again? (y/N) or ':q' to quit: ").strip().lower()
            if response == ":q":
                print("Goodbye!")
                raise SystemExit(0)
            return response in ["y", "yes"]
        except EOFError:
            raise EOFError("Input stream ended unexpectedly")

    def _print_header(self, title: str) -> None:
        """Print a formatted header.

        Args:
            title: The title to display.
        """
        print(title)
        print("=" * len(title))


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Check file extensions in directories for consistency and correctness.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Interactive mode
  %(prog)s mp3               # Check MP3 files in current directory
  %(prog)s jpg /Pictures     # Check JPG files in Pictures directory
  %(prog)s --version         # Show version information
""",
    )

    parser.add_argument(
        "extension", nargs="?", help="File extension to check (without leading dot)"
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)",
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    return parser


def main() -> None:
    """Main entry point for the application."""
    parser = create_argument_parser()
    args = parser.parse_args()

    ui = ExtensionCheckerUI()

    if args.extension:
        # Batch mode
        success = ui.run_batch_mode(args.extension, args.directory)
        sys.exit(0 if success else 1)
    else:
        # Interactive mode
        ui.run_interactive_mode()


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
