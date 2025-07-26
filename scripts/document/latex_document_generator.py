"""
LaTeX Document Generator Module

This module provides tools for generating LaTeX documents programmatically. It supports
template-based document creation, section and content management, and batch file output.

Features:
- Automated LaTeX document generation
- Template and section management
- Batch file creation
- Customizable document structure
- Command-line and library usage

Example:
    >>> service = LatexDocumentCompilationService()
    >>> service.compile_document("output.tex")
"""

import argparse
import logging
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional


class LatexCompilationError(Exception):
    """Custom exception for LaTeX compilation errors."""

    pass


class LatexDependencyVerificationService:
    """
    Service for verifying that required LaTeX tools are installed.
    """

    @staticmethod
    def verify_required_tools_installed() -> List[str]:
        """
        Verify that all required LaTeX tools are installed on the system.

        Returns:
            List of missing tools, empty if all tools are installed.

        Raises:
            EnvironmentError: If any required tools are missing.
        """
        required_tool_list = ["latexmk", "biber", "makeglossaries", "makeindex"]
        missing_tool_list = [
            tool for tool in required_tool_list if not shutil.which(tool)
        ]

        if missing_tool_list:
            raise EnvironmentError(
                f"Missing required LaTeX tools: {', '.join(missing_tool_list)}"
            )

        return missing_tool_list


class LoggingConfigurationService:
    """
    Service for configuring and managing logging operations.
    """

    @staticmethod
    def configure_logging_system(log_file_path: Path) -> None:
        """
        Configure the logging system for the application.

        Args:
            log_file_path: Path to the log file.
        """
        # Configure file logging
        logging.basicConfig(
            level=logging.DEBUG,
            filename=str(log_file_path),
            filemode="a",
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

        # Add console handler for INFO level and above
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logging.getLogger().addHandler(console_handler)


class LatexCompilationToolService:
    """
    Service for executing LaTeX compilation tools.
    """

    def compile_latex_document(self, input_file_path: Path) -> None:
        """
        Compile a LaTeX document using latexmk with synctex enabled.

        Args:
            input_file_path: Path to the input LaTeX file.

        Raises:
            LatexCompilationError: If the LaTeX compilation fails.
        """
        try:
            subprocess.run(
                ["latexmk", "-pdf", "-lualatex", "-synctex=1", str(input_file_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as compilation_error:
            logging.error("LaTeX compilation failed: %s", compilation_error)
            raise LatexCompilationError(
                "Failed to compile LaTeX file."
            ) from compilation_error

    def execute_auxiliary_tools_if_needed(self, input_file_path: Path) -> None:
        """
        Execute auxiliary LaTeX tools if needed (biber, makeglossaries, makeindex).

        Args:
            input_file_path: Path to the input LaTeX file.

        Raises:
            LatexCompilationError: If the auxiliary tool execution fails.
        """
        try:
            self._execute_biber_if_needed(input_file_path)
            self._execute_makeglossaries_if_needed(input_file_path)
            self._execute_makeindex_if_needed(input_file_path)
        except subprocess.CalledProcessError as tool_error:
            logging.error("Error executing auxiliary LaTeX tools: %s", tool_error)
            raise LatexCompilationError(
                "Failed to execute auxiliary LaTeX tools."
            ) from tool_error

    def clean_compilation_artifacts(self, input_file_path: Path) -> None:
        """
        Clean previous compilation artifacts using latexmk -C.

        Args:
            input_file_path: Path to the input LaTeX file.

        Raises:
            LatexCompilationError: If cleaning the compilation artifacts fails.
        """
        try:
            subprocess.run(
                ["latexmk", "-C", str(input_file_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            logging.info("Previous compilation artifacts cleaned successfully.")
        except subprocess.CalledProcessError as cleaning_error:
            logging.error("Error cleaning compilation artifacts: %s", cleaning_error)
            raise LatexCompilationError(
                "Failed to clean compilation artifacts."
            ) from cleaning_error

    def _execute_biber_if_needed(self, input_file_path: Path) -> None:
        """Execute biber if the .bbl file does not exist."""
        bibliography_file_path = input_file_path.with_suffix(".bbl")
        if not bibliography_file_path.exists():
            logging.info("Running biber for bibliography processing...")
            subprocess.run(
                ["biber", str(input_file_path.with_suffix(""))],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

    def _execute_makeglossaries_if_needed(self, input_file_path: Path) -> None:
        """Execute makeglossaries if .gls or .acn files do not exist."""
        glossary_file_paths = [
            input_file_path.with_suffix(ext) for ext in [".gls", ".acn"]
        ]
        if not any(file_path.exists() for file_path in glossary_file_paths):
            logging.info("Running makeglossaries for glossary processing...")
            subprocess.run(
                ["makeglossaries", str(input_file_path.with_suffix(""))],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

    def _execute_makeindex_if_needed(self, input_file_path: Path) -> None:
        """Execute makeindex if the .idx file does not exist."""
        index_file_path = input_file_path.with_suffix(".idx")
        if not index_file_path.exists():
            logging.info("Running makeindex for index processing...")
            subprocess.run(
                ["makeindex", str(input_file_path.with_suffix(""))],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )


class ParallelCompilationService:
    """
    Service for executing LaTeX compilation tasks in parallel.
    """

    def __init__(self, maximum_worker_threads: int = 16):
        """
        Initialize the ParallelCompilationService.

        Args:
            maximum_worker_threads: Maximum number of worker threads to use.
        """
        self.maximum_worker_threads = maximum_worker_threads
        self.compilation_tool_service = LatexCompilationToolService()

    def execute_compilation_tasks_in_parallel(
        self, input_file_path: Path, clean_previous_artifacts: bool = False
    ) -> None:
        """
        Execute LaTeX compilation tasks in parallel using multithreading.

        Args:
            input_file_path: Path to the input LaTeX file.
            clean_previous_artifacts: Whether to clean previous compilation artifacts.

        Raises:
            LatexCompilationError: If an error occurs during parallel compilation.
        """
        try:
            # Clean previous artifacts if requested
            if clean_previous_artifacts:
                self.compilation_tool_service.clean_compilation_artifacts(
                    input_file_path
                )

            # Execute compilation and auxiliary tool tasks in parallel
            with ThreadPoolExecutor(
                max_workers=self.maximum_worker_threads
            ) as thread_executor:
                main_compilation_task = thread_executor.submit(
                    self.compilation_tool_service.compile_latex_document,
                    input_file_path,
                )
                auxiliary_tools_task = thread_executor.submit(
                    self.compilation_tool_service.execute_auxiliary_tools_if_needed,
                    input_file_path,
                )

                # Wait for both tasks to complete
                main_compilation_task.result()
                auxiliary_tools_task.result()

        except Exception as parallel_error:
            logging.exception("Error during parallel compilation:")
            raise LatexCompilationError(
                "Parallel compilation failed."
            ) from parallel_error


class LatexDocumentCompilationService:
    """
    Service for compiling LaTeX documents with comprehensive error handling.
    """

    def __init__(
        self,
        input_file_path: Optional[Path] = None,
        clean_previous_artifacts: bool = False,
        maximum_worker_threads: int = 16,
    ):
        """
        Initialize the LatexDocumentCompilationService.

        Args:
            input_file_path: Path to the LaTeX file to compile.
            clean_previous_artifacts: Whether to clean previous compilation artifacts.
            maximum_worker_threads: Maximum number of worker threads to use.
        """
        self.input_file_path = input_file_path
        self.clean_previous_artifacts = clean_previous_artifacts
        self.maximum_worker_threads = maximum_worker_threads

        # Initialize component services
        self.parallel_compilation_service = ParallelCompilationService(
            maximum_worker_threads
        )
        self.dependency_verification_service = LatexDependencyVerificationService()
        self.logging_service = LoggingConfigurationService()

    def compile_document(self, input_file_path: Optional[Path] = None) -> bool:
        """
        Compile a LaTeX document with comprehensive error handling.

        Args:
            input_file_path: Path to the LaTeX file to compile.
                           If None, uses the path provided during initialization.

        Returns:
            True if compilation was successful, False otherwise.
        """
        # Use provided input file path or the one from initialization
        effective_input_file_path = input_file_path or self.input_file_path

        if not effective_input_file_path:
            logging.error("No input file path provided.")
            return False

        try:
            # Validate input file exists
            self._validate_input_file_exists(effective_input_file_path)

            # Set up logging
            self._configure_logging_system()

            # Check dependencies
            self._verify_required_tools_installed()

            # Log start of compilation
            logging.info("Starting LaTeX document compilation...")
            print("Starting LaTeX document compilation...")

            # Track compilation time
            start_time = time.time()

            # Execute compilation tasks in parallel
            self.parallel_compilation_service.execute_compilation_tasks_in_parallel(
                effective_input_file_path, self.clean_previous_artifacts
            )

            # Calculate and log completion time
            end_time = time.time()
            compilation_duration = end_time - start_time

            logging.info(
                "Compilation completed successfully in %.2f seconds.",
                compilation_duration,
            )
            print(
                f"Compilation completed successfully in {compilation_duration:.2f} seconds."
            )

            return True

        except Exception as compilation_error:
            logging.exception("An error occurred during compilation:")
            print(f"An error occurred during compilation: {str(compilation_error)}")
            return False

    def _validate_input_file_exists(self, input_file_path: Path) -> None:
        """Validate that the input LaTeX file exists."""
        if not input_file_path.exists():
            raise FileNotFoundError(f"LaTeX file '{input_file_path}' not found.")

    def _configure_logging_system(self) -> None:
        """Configure the logging system for the compilation process."""
        current_date = time.strftime("%Y-%m-%d", time.localtime())
        log_file_path = Path(f"latex_compilation_{current_date}.log")
        self.logging_service.configure_logging_system(log_file_path)

    def _verify_required_tools_installed(self) -> None:
        """Verify that all required LaTeX tools are installed."""
        self.dependency_verification_service.verify_required_tools_installed()


class CommandLineArgumentParser:
    """
    Parser for command-line arguments.
    """

    @staticmethod
    def parse_command_line_arguments() -> argparse.Namespace:
        """
        Parse command-line arguments for the LaTeX document compiler.

        Returns:
            Parsed command-line arguments.
        """
        parser = argparse.ArgumentParser(description="LaTeX Document Compiler")
        parser.add_argument(
            "input_file", type=str, help="Path to the LaTeX file to compile"
        )
        parser.add_argument(
            "--clean", action="store_true", help="Clean previous compilation artifacts"
        )
        parser.add_argument(
            "--max-workers",
            type=int,
            default=16,
            help="Maximum number of worker threads",
        )
        return parser.parse_args()


class LatexDocumentCompilationApplicationLauncher:
    """
    Launcher for the LaTeX document compilation application.
    """

    @staticmethod
    def launch_application() -> int:
        """
        Launch the LaTeX document compilation application.

        Returns:
            Exit code: 0 for success, 1 for failure.
        """
        # Parse command-line arguments
        args = CommandLineArgumentParser.parse_command_line_arguments()
        input_file_path = Path(args.input_file)
        clean_previous_artifacts = args.clean
        maximum_worker_threads = args.max_workers

        # Create and run the compilation service
        compilation_service = LatexDocumentCompilationService(
            input_file_path=input_file_path,
            clean_previous_artifacts=clean_previous_artifacts,
            maximum_worker_threads=maximum_worker_threads,
        )

        # Execute compilation and return appropriate exit code
        compilation_successful = compilation_service.compile_document()
        return 0 if compilation_successful else 1


def main() -> None:
    """
    Main entry point for the LaTeX document generator script.
    """
    exit_code = LatexDocumentCompilationApplicationLauncher.launch_application()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
