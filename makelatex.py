import os
import subprocess
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List

class LaTeXCompiler:
    """
    Class for compiling LaTeX documents and handling auxiliary compilation tasks.
    """

    def compile_latex(self, input_file: str) -> None:
        """
        Compile the LaTeX input file using latexmk with synctex enabled.

        Parameters:
        input_file (str): Path to the input LaTeX file.
        """
        try:
            subprocess.run(['latexmk', '-pdf', '-lualatex', '-synctex=1', input_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logging.error(f"Compilation failed: {e}")
            raise RuntimeError("Failed to compile LaTeX file.") from e

    def check_compilation_needs(self, input_file: str) -> None:
        """
        Check whether auxiliary compilation tools (biber, makeglossaries, makeindex) need to be run and execute them if necessary.

        Parameters:
        input_file (str): Path to the input LaTeX file.
        """
        try:
            # Check if .bbl file exists (for bibliography)
            bbl_file = os.path.splitext(input_file)[0] + '.bbl'
            if not os.path.exists(bbl_file):
                logging.info("Running biber...")
                subprocess.run(['biber', os.path.splitext(input_file)[0]], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            # Check if .gls or .acn file exists (for glossary)
            glossary_files = [os.path.splitext(input_file)[0] + ext for ext in ['.gls', '.acn']]
            for glossary_file in glossary_files:
                if not os.path.exists(glossary_file):
                    logging.info("Running makeglossaries...")
                    subprocess.run(['makeglossaries', os.path.splitext(input_file)[0]], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            # Check if .idx file exists (for index)
            idx_file = os.path.splitext(input_file)[0] + '.idx'
            if not os.path.exists(idx_file):
                logging.info("Running makeindex...")
                subprocess.run(['makeindex', os.path.splitext(input_file)[0]], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logging.error(f"Error in compilation needs checking: {e}")
            raise RuntimeError("Failed to check compilation needs.") from e

    def clean_previous_compilation(self, input_file: str) -> None:
        """
        Clean the previous compilation files using latexmk -C.

        Parameters:
        input_file (str): Path to the input LaTeX file.
        """
        try:
            subprocess.run(['latexmk', '-C', input_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            logging.info("Previous compilation files cleaned.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error cleaning previous compilation files: {e}")
            raise RuntimeError("Failed to clean previous compilation files.") from e

class LaTeXCompilerExecutor:
    """
    Class for executing LaTeX compilation and compilation needs checking tasks using multithreading.
    """

    def __init__(self, max_workers: int = 16):
        self.max_workers = max_workers

    def compile_with_threads(self, input_file: str, clean_previous: bool = False) -> None:
        """
        Compile LaTeX document and handle compilation needs checking using multithreading.

        Parameters:
        input_file (str): Path to the input LaTeX file.
        clean_previous (bool): Whether to clean previous compilation files before compiling.
        """
        compiler = LaTeXCompiler()

        try:
            if clean_previous:
                compiler.clean_previous_compilation(input_file)

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit compilation and compilation needs checking tasks to executor
                compilation_task = executor.submit(compiler.compile_latex, input_file)
                compilation_needs_task = executor.submit(compiler.check_compilation_needs, input_file)
                
                # Wait for tasks to complete
                compilation_task.result()
                compilation_needs_task.result()
        except Exception as e:
            logging.exception("An error occurred during multithreaded compilation:")
            raise

def main() -> None:
    """
    Main function to execute the script.
    """
    try:
        current_date = time.strftime("%Y-%m-%d", time.localtime())
        log_file = f'latex_last_compiled_{current_date}.log'
        logging.basicConfig(level=logging.DEBUG, filename=log_file, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(console_handler)

        input_file: str = input("Enter the path to the LaTeX file: ")

        if not os.path.exists(input_file):
            raise FileNotFoundError(f"File '{input_file}' not found.")

        clean_previous: bool = input("Clean previous compilation files? (y/n): ").lower() == 'y'

        logging.info("Starting compilation...")
        print("Starting compilation...")

        start_time: float = time.time()

        executor = LaTeXCompilerExecutor()
        executor.compile_with_threads(input_file, clean_previous)

        end_time: float = time.time()
        logging.info(f"Compilation completed successfully in {end_time - start_time:.2f} seconds.")
        print(f"Compilation completed successfully in {end_time - start_time:.2f} seconds.")

    except Exception as e:
        logging.exception("An error occurred during compilation:")
        print("An error occurred during compilation:")
        raise

if __name__ == "__main__":
    main()
