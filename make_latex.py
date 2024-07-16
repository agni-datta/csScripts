import argparse
import logging
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional


class LaTeXCompilationError(Exception):
    """Custom exception for LaTeX compilation errors."""


class LaTeXCompiler:
    """
    Class for compiling LaTeX documents and handling auxiliary compilation tasks.
    """

    def compile_latex(self, input_file: Path) -> None:
        """
        Compile the LaTeX input file using latexmk with synctex enabled.

        Parameters:
        input_file (Path): Path to the input LaTeX file.
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
        Check whether auxiliary compilation tools (biber, makeglossaries, makeindex)
        need to be run and execute them if necessary.

        Parameters:
        input_file (Path): Path to the input LaTeX file.
        """
        try:
            # Check if .bbl file exists (for bibliography)
            bbl_file = input_file.with_suffix(".bbl")
            if not bbl_file.exists():
                logging.info("Running biber...")
                subprocess.run(
                    ["biber", str(input_file.with_suffix(""))],
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )

            # Check if .gls or .acn file exists (for glossary)
            glossary_files = [input_file.with_suffix(ext) for ext in [".gls", ".acn"]]
            if not any(file.exists() for file in glossary_files):
                logging.info("Running makeglossaries...")
                subprocess.run(
                    ["makeglossaries", str(input_file.with_suffix(""))],
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )

            # Check if .idx file exists (for index)
            idx_file = input_file.with_suffix(".idx")
            if not idx_file.exists():
                logging.info("Running makeindex...")
                subprocess.run(
                    ["makeindex", str(input_file.with_suffix(""))],
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
        except subprocess.CalledProcessError as e:
            logging.error("Error in compilation needs checking: %s", e)
            raise LaTeXCompilationError("Failed to check compilation needs.") from e

    def clean_previous_compilation(self, input_file: Path) -> None:
        """
        Clean the previous compilation files using latexmk -C.

        Parameters:
        input_file (Path): Path to the input LaTeX file.
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


class LaTeXCompilerExecutor:
    """
    Class for executing LaTeX compilation and compilation needs checking tasks using multithreading.
    """

    def __init__(self, max_workers: int = 16):
        self.max_workers = max_workers

    def compile_with_threads(
        self, input_file: Path, clean_previous: bool = False
    ) -> None:
        """
        Compile LaTeX document and handle compilation needs checking using multithreading.

        Parameters:
        input_file (Path): Path to the input LaTeX file.
        clean_previous (bool): Whether to clean previous compilation files before compiling.
        """
        compiler = LaTeXCompiler()

        try:
            if clean_previous:
                compiler.clean_previous_compilation(input_file)
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit compilation and compilation needs checking tasks to executor
                compilation_task = executor.submit(compiler.compile_latex, input_file)
                compilation_needs_task = executor.submit(
                    compiler.check_compilation_needs, input_file
                )

                # Wait for tasks to complete
                compilation_task.result()
                compilation_needs_task.result()
        except Exception as e:
            logging.exception("An error occurred during multithreaded compilation:")
            raise LaTeXCompilationError("Multithreaded compilation failed.") from e


def check_dependencies() -> None:
    """Check if required LaTeX tools are installed."""
    required_tools = ["latexmk", "biber", "makeglossaries", "makeindex"]
    missing_tools = []

    for tool in required_tools:
        if not shutil.which(tool):
            missing_tools.append(tool)

    if missing_tools:
        raise EnvironmentError(f"Missing required tools: {', '.join(missing_tools)}")


def setup_logging(log_file: Path) -> None:
    """Set up logging configuration."""
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


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
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
    try:
        args = parse_arguments()
        input_file = Path(args.input_file)
        clean_previous = args.clean
        max_workers = args.max_workers

        if not input_file.exists():
            raise FileNotFoundError(f"File '{input_file}' not found.")

        current_date = time.strftime("%Y-%m-%d", time.localtime())
        log_file = Path(f"latex_last_compiled_{current_date}.log")
        setup_logging(log_file)

        check_dependencies()

        logging.info("Starting compilation...")
        print("Starting compilation...")

        start_time: float = time.time()

        executor = LaTeXCompilerExecutor(max_workers=max_workers)
        executor.compile_with_threads(input_file, clean_previous)

        end_time: float = time.time()
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


if __name__ == "__main__":
    main()
