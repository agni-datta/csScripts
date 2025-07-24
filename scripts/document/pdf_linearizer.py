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
    >>> service = PDFLinearizationService(simulation_mode=True)
    >>> service.execute_linearization_process()
"""

import os
import subprocess
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


class FileMetadata:
    """
    Represents metadata for a file, including size and modification time.
    """

    @staticmethod
    def extract_file_metadata(file_path: str) -> Dict[str, Any]:
        """
        Extract size and modification time metadata from a file.

        Args:
            file_path: Path to the file.

        Returns:
            Dictionary with 'size' and 'mtime' keys.
        """
        file_stats = os.stat(file_path)
        return {
            "size": file_stats.st_size,
            "mtime": file_stats.st_mtime,
        }


class PDFFileDiscoveryService:
    """
    Service for discovering PDF files in a directory structure.
    """

    def discover_pdf_files(
        self,
        root_directory_path: str,
        file_filter: Optional[Callable[[str], bool]] = None,
    ) -> List[str]:
        """
        Recursively discover PDF files under the specified root directory.

        Args:
            root_directory_path: The root directory to start searching.
            file_filter: Optional function to filter PDF files.

        Returns:
            List of paths to discovered PDF files.
        """
        discovered_pdf_files: List[str] = []

        for current_directory_path, _, file_names in os.walk(root_directory_path):
            for file_name in file_names:
                if file_name.lower().endswith(".pdf"):
                    complete_file_path = os.path.join(current_directory_path, file_name)
                    if file_filter is None or file_filter(complete_file_path):
                        discovered_pdf_files.append(complete_file_path)

        return discovered_pdf_files


class OperationLoggingService:
    """
    Service for logging PDF linearization operations.
    """

    def __init__(self, log_file_path: str):
        """
        Initialize the OperationLoggingService.

        Args:
            log_file_path: Path to the log file.
        """
        self.log_file_path = log_file_path

    def log_file_transformation(
        self,
        file_path: str,
        before_metadata: Dict[str, Any],
        after_metadata: Dict[str, Any],
    ) -> None:
        """
        Log the transformation of a file, including before and after metadata.

        Args:
            file_path: Path to the transformed file.
            before_metadata: Metadata before transformation.
            after_metadata: Metadata after transformation.
        """
        with open(self.log_file_path, "a") as log_file:
            log_file.write(f"File: {file_path}\n")
            log_file.write(
                f"Before - Size: {before_metadata['size']} bytes, "
                f"Modified: {datetime.fromtimestamp(before_metadata['mtime'])}\n"
            )
            log_file.write(
                f"After  - Size: {after_metadata['size']} bytes, "
                f"Modified: {datetime.fromtimestamp(after_metadata['mtime'])}\n"
            )
            log_file.write("-" * 60 + "\n")

    def log_simulated_transformation(
        self, file_path: str, file_metadata: Dict[str, Any]
    ) -> None:
        """
        Log a simulated transformation (dry run).

        Args:
            file_path: Path to the file.
            file_metadata: Current file metadata.
        """
        with open(self.log_file_path, "a") as log_file:
            log_file.write(f"[DRY RUN] File: {file_path}\n")
            log_file.write(
                f"Simulated linearization. Current Size: {file_metadata['size']} bytes, "
                f"Modified: {datetime.fromtimestamp(file_metadata['mtime'])}\n"
            )
            log_file.write("-" * 60 + "\n")

    def log_processing_error(self, file_path: str, error_message: str) -> None:
        """
        Log an error that occurred during file processing.

        Args:
            file_path: Path to the file that caused the error.
            error_message: Description of the error.
        """
        with open(self.log_file_path, "a") as log_file:
            log_file.write(f"Failed to process {file_path}: {error_message}\n")
            log_file.write("-" * 60 + "\n")


class PDFLinearizationToolService:
    """
    Service for linearizing PDF files using external tools.
    """

    def __init__(
        self, logging_service: OperationLoggingService, simulation_mode: bool = False
    ):
        """
        Initialize the PDFLinearizationToolService.

        Args:
            logging_service: Service for logging operations.
            simulation_mode: If True, simulate linearization without modifying files.
        """
        self.logging_service = logging_service
        self.simulation_mode = simulation_mode

    def linearize_pdf_file(self, pdf_file_path: str) -> bool:
        """
        Linearize a PDF file using qpdf.

        Args:
            pdf_file_path: Path to the PDF file to linearize.

        Returns:
            True if linearization was successful or simulated, False otherwise.
        """
        # Get file metadata before linearization
        before_metadata = FileMetadata.extract_file_metadata(pdf_file_path)

        # If in simulation mode, just log and return
        if self.simulation_mode:
            self.logging_service.log_simulated_transformation(
                pdf_file_path, before_metadata
            )
            return True

        # Perform actual linearization
        try:
            subprocess.run(
                ["qpdf", "--linearize", "--replace-input", pdf_file_path],
                check=True,
                capture_output=True,
            )

            # Get file metadata after linearization
            after_metadata = FileMetadata.extract_file_metadata(pdf_file_path)

            # Log the transformation
            self.logging_service.log_file_transformation(
                pdf_file_path, before_metadata, after_metadata
            )

            return True

        except subprocess.CalledProcessError as command_error:
            self.logging_service.log_processing_error(pdf_file_path, str(command_error))
            return False


class UserInteractionService:
    """
    Service for handling user interactions.
    """

    @staticmethod
    def request_user_confirmation(message: str) -> bool:
        """
        Request confirmation from the user.

        Args:
            message: The message to display to the user.

        Returns:
            True if user confirms, False otherwise.
        """
        response = input(f"{message} [y/N]: ").strip().lower()
        return response == "y"

    @staticmethod
    def display_information_message(message: str) -> None:
        """
        Display an information message to the user.

        Args:
            message: The message to display.
        """
        print(message)


class PDFLinearizationService:
    """
    Main service for PDF linearization operations.
    """

    def __init__(
        self,
        target_directory_path: Optional[str] = None,
        log_file_name: str = "fastviewpdf.log",
        simulation_mode: bool = False,
        file_filter: Optional[Callable[[str], bool]] = None,
    ):
        """
        Initialize the PDFLinearizationService.

        Args:
            target_directory_path: Directory to scan for PDF files.
            log_file_name: Name of the log file.
            simulation_mode: If True, simulate linearization without modifying files.
            file_filter: Optional function to filter PDF files.
        """
        self.target_directory_path = target_directory_path or os.getcwd()
        self.log_file_path = os.path.join(self.target_directory_path, log_file_name)
        self.simulation_mode = simulation_mode
        self.file_filter = file_filter

        # Initialize services
        self.discovery_service = PDFFileDiscoveryService()
        self.logging_service = OperationLoggingService(self.log_file_path)
        self.linearization_tool_service = PDFLinearizationToolService(
            self.logging_service, self.simulation_mode
        )
        self.user_interaction_service = UserInteractionService()

    def execute_linearization_process(self) -> None:
        """
        Execute the complete PDF linearization process.
        """
        # Discover PDF files
        discovered_pdf_files = self.discovery_service.discover_pdf_files(
            self.target_directory_path, self.file_filter
        )

        # Check if any files were found
        if not discovered_pdf_files:
            self.user_interaction_service.display_information_message(
                "No PDF files found."
            )
            return

        # Display information and request confirmation
        self.user_interaction_service.display_information_message(
            f"Found {len(discovered_pdf_files)} PDF files under {self.target_directory_path}."
        )

        if self.simulation_mode:
            self.user_interaction_service.display_information_message(
                "Simulation mode is enabled. No files will be modified."
            )

        if not self.user_interaction_service.request_user_confirmation(
            "Are you sure you want to proceed?"
        ):
            self.user_interaction_service.display_information_message(
                "Operation aborted."
            )
            return

        # Process each PDF file
        successful_count = 0
        failed_count = 0

        for pdf_file_path in discovered_pdf_files:
            if self.linearization_tool_service.linearize_pdf_file(pdf_file_path):
                successful_count += 1
            else:
                failed_count += 1

        # Display summary
        self.user_interaction_service.display_information_message(
            f"\nLinearization complete: {successful_count} files processed successfully, "
            f"{failed_count} files failed."
        )


class PDFLinearizationApplicationLauncher:
    """
    Launcher for the PDF linearization application.
    """

    @staticmethod
    def launch_application(
        simulation_mode: bool = False,
        file_filter: Optional[Callable[[str], bool]] = None,
    ) -> None:
        """
        Launch the PDF linearization application.

        Args:
            simulation_mode: If True, simulate linearization without modifying files.
            file_filter: Optional function to filter PDF files.
        """
        linearization_service = PDFLinearizationService(
            simulation_mode=simulation_mode, file_filter=file_filter
        )
        linearization_service.execute_linearization_process()


def main() -> None:
    """
    Main entry point for the PDF linearizer script.
    """
    # Example: Filter only PDFs greater than 100KB
    # def size_filter(path): return os.path.getsize(path) > 100 * 1024

    application_launcher = PDFLinearizationApplicationLauncher()
    application_launcher.launch_application(
        simulation_mode=False,
        file_filter=None,  # Replace with size_filter or other predicate if needed
    )


if __name__ == "__main__":
    main()
