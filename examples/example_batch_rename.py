"""
Example: Batch File Renaming

This script demonstrates how to use the FileBatchRenamer class to rename files in a directory.
"""

from scripts.file_ops.file_batch_renamer import FileRenamer

if __name__ == "__main__":
    # Example: Rename all .txt files in the current directory
    renamer = FileRenamer(".txt")
    renamer.run()
    print("Batch renaming complete.")
