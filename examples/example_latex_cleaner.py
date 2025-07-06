"""
Example: LaTeX Auxiliary File Cleaner

This script demonstrates how to use the FileDeleter class to clean up LaTeX auxiliary files in a directory.
"""

from scripts.document.latex_cleaner import FileDeleter

if __name__ == "__main__":
    # Example: Clean LaTeX auxiliary files in the current directory
    cleaner = FileDeleter()
    cleaner.run(directory=".")
    print("LaTeX auxiliary file cleanup complete.")
