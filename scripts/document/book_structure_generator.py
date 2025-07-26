"""
Book Structure Generator Module

This module provides tools for creating and managing the file structure of a LaTeX book project.
It automates the creation of chapters, sections, and other organizational files needed for
academic book writing and publishing workflows.

Features:
- Automated directory and file creation for LaTeX book projects
- Customizable templates for chapters and sections with front/back matter
- Interactive and batch file generation modes
- Command-line interface and library usage
- Modular bibliography file generation
- LaTeX document structure with proper matter separation

Example:
    >>> generator = BookStructureGenerationService()
    >>> generator.execute_generation_process()  # Interactive mode
    >>> # Or use as library:
    >>> config = BookStructureConfiguration(number_of_chapters=10)
    >>> generator = BookStructureGenerationService(config)
    >>> generator.execute_generation_process()
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class DocumentFileGroup:
    """
    Represents a logical group of .tex files under a common directory,
    such as front-matter or back-matter sections.
    """

    group_name: str
    directory_name: str
    file_list: List[str]

    def get_absolute_file_paths(self) -> List[str]:
        """
        Compute full file paths relative to directory.

        Returns:
            List[str]: List of full paths to each file in the group.
        """
        return [
            os.path.join(self.directory_name, file_name) for file_name in self.file_list
        ]


@dataclass
class BookStructureConfiguration:
    """
    Configuration container for book generation parameters,
    including chapter count and matter file groups.
    """

    number_of_chapters: int = 0
    manual_selection_mode: bool = False
    front_matter: DocumentFileGroup = field(
        default_factory=lambda: DocumentFileGroup(
            "front",
            "front-matter",
            [
                "half_title.tex",
                "series_page.tex",
                "cover_page.tex",
                "frontispiece.tex",
                "title_page.tex",
                "copyright_page.tex",
                "dedication.tex",
                "epigraph.tex",
                "endorsements.tex",
                "table_of_contents.tex",
                "list_of_illustrations.tex",
                "list_of_tables.tex",
                "list_of_figures.tex",
                "list_of_algorithms.tex",
                "foreword.tex",
                "preface.tex",
                "acknowledgements.tex",
                "introduction.tex",
                "list_of_abbreviations.tex",
            ],
        )
    )
    back_matter: DocumentFileGroup = field(
        default_factory=lambda: DocumentFileGroup(
            "back",
            "back-matter",
            [
                "appendix.tex",
                "glossary.tex",
                "notes.tex",
                "endnotes.tex",
                "bibliography.tex",
                "references.tex",
                "index.tex",
                "author_bio.tex",
                "contributors.tex",
                "colophon.tex",
                "errata.tex",
                "afterword.tex",
                "marketing_blurb.tex",
                "other_works.tex",
                "contact_info.tex",
            ],
        )
    )

    def generate_chapter_file_names(self) -> List[str]:
        """
        Generate .tex filenames for chapters with proper numbering.

        Returns:
            List[str]: List of chapter filenames.
        """
        return [
            f"chapter_{chapter_number:02d}.tex"
            for chapter_number in range(1, self.number_of_chapters + 1)
        ]


class UserInteractionService:
    """
    Handles user interaction for the book structure generator.
    """

    def prompt_for_generation_mode(self) -> bool:
        """
        Ask the user whether to enter manual file selection mode.

        Returns:
            bool: True if manual mode selected, False otherwise.
        """
        user_response = (
            input("Enter 'm' for manual selection or press enter for full generation: ")
            .strip()
            .lower()
        )
        return user_response == "m"

    def prompt_for_chapter_count(self) -> int:
        """
        Prompt user to specify the number of chapters.

        Returns:
            int: The number of chapters specified by the user.
        """
        while True:
            try:
                chapter_count = int(input("Enter number of chapters: "))
                if chapter_count >= 0:
                    return chapter_count
                print("Must be non-negative.")
            except ValueError:
                print("Invalid input")

    def prompt_for_file_selection(self, file_group: DocumentFileGroup) -> List[str]:
        """
        Interactively select files from a DocumentFileGroup.

        Args:
            file_group: The file group to prompt for inclusion.

        Returns:
            List[str]: The list of selected filenames.
        """
        print(f"\nSelect {file_group.group_name}-matter files (y/n):")
        selected_files = []

        for file_name in file_group.file_list:
            user_response = input(f"Include {file_name}? [y/N]: ").strip().lower()
            if user_response == "y":
                selected_files.append(file_name)

        return selected_files


class FileSystemOperationService:
    """
    Handles file system operations for the book structure generator.
    """

    def create_empty_file_with_directory(self, file_path: str) -> None:
        """
        Create a single empty file, ensuring parent directory exists.

        Args:
            file_path: The file path to create.
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w"):
            pass
        print(f"Created {file_path}")

    def create_multiple_empty_files(self, file_paths: List[str]) -> None:
        """
        Create multiple empty files at the specified paths.

        Args:
            file_paths: List of file paths to create.
        """
        for file_path in file_paths:
            self.create_empty_file_with_directory(file_path)


class LatexDocumentGenerator:
    """
    Generates LaTeX document files for the book structure.
    """

    def __init__(self, file_system_service: FileSystemOperationService):
        """
        Initialize the LatexDocumentGenerator.

        Args:
            file_system_service: Service for file system operations.
        """
        self.file_system_service = file_system_service

    def generate_main_tex_file(
        self,
        front_matter_files: List[str],
        chapter_files: List[str],
        back_matter_files: List[str],
    ) -> None:
        """
        Generate the `main.tex` file including all document parts.

        Args:
            front_matter_files: Front-matter files.
            chapter_files: Main chapter files.
            back_matter_files: Back-matter files.
        """
        with open("main.tex", "w") as main_file:
            write_line = main_file.write

            # Document preamble
            write_line("\\documentclass{book}\n")
            write_line("\\usepackage{csbook}\n")
            write_line("\\begin{document}\n")

            # Front matter
            write_line("\\frontmatter\n")
            for file_name in front_matter_files:
                write_line(f"\\input{{front-matter/{file_name}}}\n")

            # Main matter
            write_line("\\mainmatter\n")
            for file_name in chapter_files:
                write_line(f"\\input{{main-matter/{file_name}}}\n")

            # Back matter
            write_line("\\backmatter\n")
            for file_name in back_matter_files:
                write_line(f"\\input{{back-matter/{file_name}}}\n")

            # Bibliography
            write_line("\\bibliographystyle{plain}\n")
            write_line(
                "\\bibliography{references,further_reading,bibliography,additional,manual}\n"
            )

            # End document
            write_line("\\end{document}\n")

        print("Generated main.tex")

    def generate_bibliography_files(self) -> None:
        """
        Generate multiple structured .bib files for modular citation management.
        """
        bibliography_files = [
            "references.bib",
            "further_reading.bib",
            "bibliography.bib",
            "additional.bib",
            "manual.bib",
        ]

        for bibliography_file in bibliography_files:
            self.file_system_service.create_empty_file_with_directory(bibliography_file)


class BookStructureGenerationService:
    """
    Service for generating a complete LaTeX book structure.
    """

    def __init__(self, configuration: BookStructureConfiguration = None) -> None:
        """
        Initialize the BookStructureGenerationService with optional configuration.

        Args:
            configuration: Configuration for book generation. If None, a default configuration is used.
        """
        self.configuration = configuration or BookStructureConfiguration()
        self.user_interaction_service = UserInteractionService()
        self.file_system_service = FileSystemOperationService()
        self.latex_document_generator = LatexDocumentGenerator(self.file_system_service)

    def _prepare_file_paths_with_directory(
        self, file_names: List[str], directory_name: str
    ) -> List[str]:
        """
        Prepare file paths by joining file names with directory name.

        Args:
            file_names: List of file names.
            directory_name: Directory name to prepend.

        Returns:
            List[str]: List of file paths.
        """
        return [os.path.join(directory_name, file_name) for file_name in file_names]

    def execute_generation_process(self) -> None:
        """
        Execute the complete book structure generation process.
        """
        # Get user preferences if not already set
        if not hasattr(self, "configuration") or self.configuration is None:
            self.configuration = BookStructureConfiguration()

        self.configuration.manual_selection_mode = (
            self.user_interaction_service.prompt_for_generation_mode()
        )
        self.configuration.number_of_chapters = (
            self.user_interaction_service.prompt_for_chapter_count()
        )

        # Select files based on user preferences or use all files
        front_matter_files = (
            self.user_interaction_service.prompt_for_file_selection(
                self.configuration.front_matter
            )
            if self.configuration.manual_selection_mode
            else self.configuration.front_matter.file_list
        )

        back_matter_files = (
            self.user_interaction_service.prompt_for_file_selection(
                self.configuration.back_matter
            )
            if self.configuration.manual_selection_mode
            else self.configuration.back_matter.file_list
        )

        chapter_files = self.configuration.generate_chapter_file_names()

        # Create all necessary files
        self.file_system_service.create_multiple_empty_files(
            self._prepare_file_paths_with_directory(chapter_files, "main-matter")
        )

        self.file_system_service.create_multiple_empty_files(
            self._prepare_file_paths_with_directory(front_matter_files, "front-matter")
        )

        self.file_system_service.create_multiple_empty_files(
            self._prepare_file_paths_with_directory(back_matter_files, "back-matter")
        )

        # Generate bibliography and main tex files
        self.latex_document_generator.generate_bibliography_files()
        self.latex_document_generator.generate_main_tex_file(
            front_matter_files, chapter_files, back_matter_files
        )


class BookGenerationApplicationLauncher:
    """
    Launches the book structure generation application.
    """

    @staticmethod
    def launch_application() -> None:
        """
        Launch the book structure generation application.
        """
        generation_service = BookStructureGenerationService()
        generation_service.execute_generation_process()


def main() -> None:
    """
    Main entry point for the book structure generator script.
    """
    application_launcher = BookGenerationApplicationLauncher()
    application_launcher.launch_application()


if __name__ == "__main__":
    main()
