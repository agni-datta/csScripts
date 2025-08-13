#!/usr/bin/env python3
"""
Directory Indexer Module

This module provides functionality to recursively index a directory and all its subdirectories,
generating a comprehensive JSON index file with detailed metadata for every file and folder.

Features:
- Recursive directory traversal
- Comprehensive metadata extraction
- Structured index generation
- JSON output formatting
- Progress reporting

The module is designed with a service-oriented architecture for easy extension and maintenance.

Usage:
    python3 update_index.py

Example:
    >>> service = DirectoryIndexingService()
    >>> service.execute_indexing_process()
"""

import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class FileSystemTraversalService:
    """
    Service for traversing the file system and collecting file and directory paths.
    """

    def __init__(self, root_directory_path: Path):
        """
        Initialize the FileSystemTraversalService.

        Args:
            root_directory_path: The root directory to start traversal from.
        """
        self.root_directory_path = root_directory_path

    def collect_all_filesystem_entries(self) -> List[Path]:
        """
        Recursively collect all file and directory paths under the root directory.

        Returns:
            List of all file and directory paths found.
        """
        return list(self.root_directory_path.rglob("*"))


class FileSystemMetadataExtractionService:
    """
    Service for extracting comprehensive metadata from file system entries.
    """

    @staticmethod
    def extract_entry_metadata(filesystem_entry_path: Path) -> Dict[str, Any]:
        """
        Extract detailed metadata for a given file or directory.

        Args:
            filesystem_entry_path: Path to the file or directory.

        Returns:
            Dictionary containing comprehensive metadata about the entry.
        """
        entry_statistics = filesystem_entry_path.stat()

        # Build comprehensive metadata dictionary
        entry_metadata = {
            "name": filesystem_entry_path.name,
            "path": str(filesystem_entry_path.resolve()),
            "is_file": filesystem_entry_path.is_file(),
            "is_dir": filesystem_entry_path.is_dir(),
            "size": entry_statistics.st_size,
            "created": datetime.datetime.fromtimestamp(
                entry_statistics.st_ctime
            ).isoformat(),
            "modified": datetime.datetime.fromtimestamp(
                entry_statistics.st_mtime
            ).isoformat(),
            "accessed": datetime.datetime.fromtimestamp(
                entry_statistics.st_atime
            ).isoformat(),
            "suffix": filesystem_entry_path.suffix,
            "parent": str(filesystem_entry_path.parent.resolve()),
            "stat": {
                "mode": entry_statistics.st_mode,
                "inode": entry_statistics.st_ino,
                "device": entry_statistics.st_dev,
                "nlink": entry_statistics.st_nlink,
                "uid": entry_statistics.st_uid,
                "gid": entry_statistics.st_gid,
            },
        }

        return entry_metadata


class DirectoryIndexConstructionService:
    """
    Service for constructing a structured directory index from metadata.
    """

    def __init__(self):
        """
        Initialize the DirectoryIndexConstructionService with an empty index structure.
        """
        self.directory_index: Dict[str, Any] = {"files": [], "directories": []}

    def add_entry_to_index(self, entry_metadata: Dict[str, Any]) -> None:
        """
        Add an entry's metadata to the appropriate section of the index.

        Args:
            entry_metadata: Metadata dictionary for a file system entry.
        """
        if entry_metadata["is_file"]:
            self.directory_index["files"].append(entry_metadata)
        elif entry_metadata["is_dir"]:
            self.directory_index["directories"].append(entry_metadata)

    def get_complete_index(self) -> Dict[str, Any]:
        """
        Get the complete directory index structure.

        Returns:
            The complete directory index.
        """
        return self.directory_index


class IndexFileWriterService:
    """
    Service for writing the directory index to a JSON file.
    """

    def __init__(self, output_file_path: Path):
        """
        Initialize the IndexFileWriterService.

        Args:
            output_file_path: Path where the index file will be written.
        """
        self.output_file_path = output_file_path

    def write_index_to_file(self, directory_index: Dict[str, Any]) -> None:
        """
        Write the directory index to a JSON file with proper formatting.

        Args:
            directory_index: The directory index to write.
        """
        with open(self.output_file_path, "w", encoding="utf-8") as output_file:
            json.dump(
                directory_index,
                output_file,
                indent=2,  # Pretty-print with 2-space indentation
                ensure_ascii=False,  # Preserve non-ASCII characters
            )


class UserFeedbackService:
    """
    Service for providing feedback to the user during the indexing process.
    """

    @staticmethod
    def display_indexing_start_message(directory_path: Path) -> None:
        """
        Display a message indicating the start of the indexing process.

        Args:
            directory_path: The directory being indexed.
        """
        print(f"Indexing directory: {directory_path.resolve()}")

    @staticmethod
    def display_indexing_completion_message(output_file_path: Path) -> None:
        """
        Display a message indicating the completion of the indexing process.

        Args:
            output_file_path: Path to the generated index file.
        """
        print(f"Index written to {output_file_path.resolve()}")


class DirectoryIndexingService:
    """
    Service for orchestrating the directory indexing process.
    """

    def __init__(
        self,
        target_directory_path: Optional[str] = None,
        output_filename: str = "index.json",
    ):
        """
        Initialize the DirectoryIndexingService.

        Args:
            target_directory_path: Path to the directory to index. If None, uses current directory.
            output_filename: Name of the output index file.
        """
        self.target_directory_path = (
            Path(target_directory_path) if target_directory_path else Path(".")
        )
        self.output_filename = output_filename

        # Initialize component services
        self.traversal_service = FileSystemTraversalService(self.target_directory_path)
        self.metadata_service = FileSystemMetadataExtractionService()
        self.index_construction_service = DirectoryIndexConstructionService()
        self.writer_service = IndexFileWriterService(
            self.target_directory_path / self.output_filename
        )
        self.feedback_service = UserFeedbackService()

    def execute_indexing_process(self) -> None:
        """
        Execute the complete directory indexing process.
        """
        # Display start message
        self.feedback_service.display_indexing_start_message(self.target_directory_path)

        # Collect all file system entries
        filesystem_entries = self.traversal_service.collect_all_filesystem_entries()

        # Process each entry
        for entry_path in filesystem_entries:
            # Extract metadata
            entry_metadata = self.metadata_service.extract_entry_metadata(entry_path)

            # Add to index
            self.index_construction_service.add_entry_to_index(entry_metadata)

        # Get the complete index
        complete_index = self.index_construction_service.get_complete_index()

        # Write the index to file
        self.writer_service.write_index_to_file(complete_index)

        # Display completion message
        self.feedback_service.display_indexing_completion_message(
            self.writer_service.output_file_path
        )


class DirectoryIndexingApplicationLauncher:
    """
    Launcher for the directory indexing application.
    """

    @staticmethod
    def launch_application() -> None:
        """
        Launch the directory indexing application.
        """
        indexing_service = DirectoryIndexingService()
        indexing_service.execute_indexing_process()


def main() -> None:
    """
    Main entry point for the directory indexer script.
    """
    application_launcher = DirectoryIndexingApplicationLauncher()
    application_launcher.launch_application()


if __name__ == "__main__":
    main()
