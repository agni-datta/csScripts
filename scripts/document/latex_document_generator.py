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
    >>> generator = LaTeXDocumentGenerator()
    >>> generator.create_document("output.tex")
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional


class LaTeXCompilationError(Exception):
    """Custom exception for LaTeX compilation errors."""


class DependencyChecker:
    """
    Class responsible for checking if required LaTeX tools are installed.
    """

    def check_dependencies(self) -> None:
        """
        Check if required LaTeX tools are installed.

        Raises:
            EnvironmentError: If any required tools are missing.
        """
        required_tools = ["latexmk", "biber", "makeglossaries", "makeindex"]
        missing_tools = [tool for tool in required_tools if not shutil.which(tool)]

        if missing_tools:
            raise EnvironmentError(
                f"Missing required tools: {', '.join(missing_tools)}"
            )


class Logger:
    """
    Class responsible for setting up and managing logging configuration.
    """

    def setup_logging(self, log_file: Path) -> None:
        """
        Set up logging configuration.

        Parameters:
            log_file (Path): Path to the log file.
        """
        logging.basicConfig(
            level=logging.DEBUG,
            filename=str(log_file),
            filemode="a",
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logging.getLogger().addHandler(console_handler)


class LaTeXCompiler:
    """
    Class for compiling LaTeX documents and handling auxiliary compilation tasks.
    """

    def compile_latex(self, input_file: Path) -> None:
        """
        Compile the LaTeX input file using latexmk with synctex enabled.

        Parameters:
            input_file (Path): Path to the input LaTeX file.

        Raises:
            LaTeXCompilationError: If the LaTeX compilation fails.
        """
        try:
            subprocess.run(
                ["latexmk", "-pdf", "-lualatex", "-synctex=1", str(input_file)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            logging.error("Compilation failed: %s", e)
            raise LaTeXCompilationError("Failed to compile LaTeX file.") from e

    def check_compilation_needs(self, input_file: Path) -> None:
        """
        Check whether auxiliary compilation tools (biber, makeglossaries, makeindex) need to be run and execute them if necessary.

        Parameters:
            input_file (Path): Path to the input LaTeX file.

        Raises:
            LaTeXCompilationError: If the auxiliary tool execution fails.
        """
        try:
            self._run_biber_if_needed(input_file)
            self._run_makeglossaries_if_needed(input_file)
            self._run_makeindex_if_needed(input_file)
        except subprocess.CalledProcessError as e:
            logging.error("Error in compilation needs checking: %s", e)
            raise LaTeXCompilationError("Failed to check compilation needs.") from e

    def clean_previous_compilation(self, input_file: Path) -> None:
        """
        Clean the previous compilation files using latexmk -C.

        Parameters:
            input_file (Path): Path to the input LaTeX file.

        Raises:
            LaTeXCompilationError: If cleaning the previous compilation files fails.
        """
        try:
            subprocess.run(
                ["latexmk", "-C", str(input_file)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            logging.info("Previous compilation files cleaned.")
        except subprocess.CalledProcessError as e:
            logging.error("Error cleaning previous compilation files: %s", e)
            raise LaTeXCompilationError(
                "Failed to clean previous compilation files."
            ) from e

    def _run_biber_if_needed(self, input_file: Path) -> None:
        """Run biber if the .bbl file does not exist."""
        bbl_file = input_file.with_suffix(".bbl")
        if not bbl_file.exists():
            logging.info("Running biber...")
            subprocess.run(
                ["biber", str(input_file.with_suffix(""))],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

    def _run_makeglossaries_if_needed(self, input_file: Path) -> None:
        """Run makeglossaries if .gls or .acn files do not exist."""
        glossary_files = [input_file.with_suffix(ext) for ext in [".gls", ".acn"]]
        if not any(file.exists() for file in glossary_files):
            logging.info("Running makeglossaries...")
            subprocess.run(
                ["makeglossaries", str(input_file.with_suffix(""))],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

    def _run_makeindex_if_needed(self, input_file: Path) -> None:
        """Run makeindex if the .idx file does not exist."""
        idx_file = input_file.with_suffix(".idx")
        if not idx_file.exists():
            logging.info("Running makeindex...")
            subprocess.run(
                ["makeindex", str(input_file.with_suffix(""))],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )


class LaTeXCompilerExecutor:
    """
    Class for executing LaTeX compilation and compilation needs checking tasks using multithreading.
    """

    def __init__(self, max_workers: int = 16):
        """
        Initialize the LaTeXCompilerExecutor.

        Parameters:
            max_workers (int): Maximum number of worker threads.
        """
        self.max_workers = max_workers

    def compile_with_threads(
        self, input_file: Path, clean_previous: bool = False
    ) -> None:
        """
        Compile LaTeX document and handle compilation needs checking using multithreading.

        Parameters:
            input_file (Path): Path to the input LaTeX file.
            clean_previous (bool): Whether to clean previous compilation files before compiling.

        Raises:
            LaTeXCompilationError: If an error occurs during multithreaded compilation.
        """
        compiler = LaTeXCompiler()

        try:
            if clean_previous:
                compiler.clean_previous_compilation(input_file)
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                compilation_task = executor.submit(compiler.compile_latex, input_file)
                compilation_needs_task = executor.submit(
                    compiler.check_compilation_needs, input_file
                )
                compilation_task.result()
                compilation_needs_task.result()
        except Exception as e:
            logging.exception("An error occurred during multithreaded compilation:")
            raise LaTeXCompilationError("Multithreaded compilation failed.") from e


class LaTeXCompilerUtility:
    """
    Main utility class to handle LaTeX compilation.
    """

    def __init__(self, input_file: Path, clean_previous: bool, max_workers: int):
        """
        Initialize the LaTeXCompilerUtility.

        Parameters:
            input_file (Path): Path to the LaTeX file.
            clean_previous (bool): Whether to clean previous compilation files before compiling.
            max_workers (int): Maximum number of worker threads.
        """
        self.input_file = input_file
        self.clean_previous = clean_previous
        self.max_workers = max_workers
        self.executor = LaTeXCompilerExecutor(max_workers=self.max_workers)
        self.logger = Logger()
        self.dependency_checker = DependencyChecker()

    def run(self) -> None:
        """
        Run the LaTeX compilation process.
        """
        try:
            self._validate_input_file()
            self._setup_logging()
            self._check_dependencies()

            logging.info("Starting compilation...")
            print("Starting compilation...")

            start_time = time.time()

            self.executor.compile_with_threads(self.input_file, self.clean_previous)

            end_time = time.time()
            logging.info(
                "Compilation completed successfully in %.2f seconds.",
                end_time - start_time,
            )
            print(
                f"Compilation completed successfully in {end_time - start_time:.2f} seconds."
            )
        except Exception as e:
            logging.exception("An error occurred during compilation:")
            print(f"An error occurred during compilation: {str(e)}")
            sys.exit(1)

    def _validate_input_file(self) -> None:
        """Validate that the input LaTeX file exists."""
        if not self.input_file.exists():
            raise FileNotFoundError(f"File '{self.input_file}' not found.")

    def _setup_logging(self) -> None:
        """Set up logging for the compilation process."""
        current_date = time.strftime("%Y-%m-%d", time.localtime())
        log_file = Path(f"latex_last_compiled_{current_date}.log")
        self.logger.setup_logging(log_file)

    def _check_dependencies(self) -> None:
        """Check for required LaTeX compilation dependencies."""
        self.dependency_checker.check_dependencies()


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description="LaTeX Compiler Utility")
    parser.add_argument("input_file", type=str, help="Path to the LaTeX file")
    parser.add_argument(
        "--clean", action="store_true", help="Clean previous compilation files"
    )
    parser.add_argument(
        "--max-workers", type=int, default=16, help="Maximum number of worker threads"
    )
    return parser.parse_args()


def main() -> None:
    """
    Main function to execute the script.
    """
    args = parse_arguments()
    input_file = Path(args.input_file)
    clean_previous = args.clean
    max_workers = args.max_workers

    utility = LaTeXCompilerUtility(
        input_file=input_file,
        clean_previous=clean_previous,
        max_workers=max_workers,
    )
    utility.run()


if __name__ == "__main__":
    main()
