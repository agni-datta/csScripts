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
    >>> generator = BookStructureGenerator()
    >>> generator.run()  # Interactive mode
    >>> # Or use as library:
    >>> config = BookStructureConfig(chapters=10)
    >>> generator = BookStructureGenerator()
    >>> generator.config = config
    >>> generator.run()
"""

import os
from typing import List
from dataclasses import dataclass, field


@dataclass
class FileGroup:
    """
    Represents a logical group of .tex files under a common directory,
    such as front-matter or back-matter sections.
    """

    name: str
    folder: str
    files: List[str]

    def paths(self) -> List[str]:
        """
        Compute full file paths relative to folder.

        Returns:
            List[str]: List of full paths to each file in the group.
        """
        return list(map(lambda f: os.path.join(self.folder, f), self.files))


@dataclass
class BookStructureConfig:
    """
    Configuration container for book generation parameters,
    including chapter count and matter file groups.
    """

    chapters: int = 0
    manual: bool = False
    front: FileGroup = field(
        default_factory=lambda: FileGroup(
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
    back: FileGroup = field(
        default_factory=lambda: FileGroup(
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

    def chapter_files(self) -> List[str]:
        """
        Generate .tex filenames for chapters.

        Returns:
            List[str]: List of chapter filenames.
        """
        return [f"chapter_{i:02d}.tex" for i in range(1, self.chapters + 1)]


class BookStructureGenerator:
    """
    BookStructureGenerator builds a LaTeX textbook structure using
    modular, selectable front, main, and back matter files.
    """

    def __init__(self) -> None:
        """
        Initialize the generator with a default configuration.
        """
        self.config = BookStructureConfig()

    def prompt_mode(self) -> None:
        """
        Ask the user whether to enter manual file selection mode.
        """
        self.config.manual = (
            input("Enter 'm' for manual selection or press enter for full generation: ")
            .strip()
            .lower()
            == "m"
        )

    def prompt_chapter_count(self) -> None:
        """
        Prompt user to specify the number of chapters.
        """
        while True:
            try:
                n = int(input("Enter number of chapters: "))
                if n >= 0:
                    self.config.chapters = n
                    return
                print("Must be non-negative.")
            except ValueError:
                print("Invalid input")

    def prompt_files(self, group: FileGroup) -> List[str]:
        """
        Interactively select files from a FileGroup.

        Args:
            group (FileGroup): The file group to prompt for inclusion.

        Returns:
            List[str]: The list of selected filenames.
        """
        print(f"\nSelect {group.name}-matter files (y/n):")
        return list(
            filter(
                lambda f: input(f"Include {f}? [y/N]: ").strip().lower() == "y",
                group.files,
            )
        )

    def create_empty_files(self, paths: List[str]) -> None:
        """
        Create a list of empty .tex files at given paths.

        Args:
            paths (List[str]): List of file paths to create.
        """
        list(map(self._touch, paths))

    def _touch(self, filepath: str) -> None:
        """
        Create a single empty file, ensuring parent directory exists.

        Args:
            filepath (str): The file path to create.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w"):
            pass
        print(f"Created {filepath}")

    def generate_main_tex(
        self, front: List[str], chapters: List[str], back: List[str]
    ) -> None:
        """
        Generate the `main.tex` file including all document parts.

        Args:
            front (List[str]): Front-matter files.
            chapters (List[str]): Main chapter files.
            back (List[str]): Back-matter files.
        """
        with open("main.tex", "w") as f:
            write = f.write
            write("\\documentclass{book}\n")
            write("\\usepackage{csbook}\n")
            write("\\begin{document}\n")
            write("\\frontmatter\n")
            list(map(lambda name: write(f"\\input{{front-matter/{name}}}\n"), front))
            write("\\mainmatter\n")
            list(map(lambda name: write(f"\\input{{main-matter/{name}}}\n"), chapters))
            write("\\backmatter\n")
            list(map(lambda name: write(f"\\input{{back-matter/{name}}}\n"), back))
            write("\\bibliographystyle{plain}\n")
            write(
                "\\bibliography{references,further_reading,bibliography,additional,manual}\n"
            )
            write("\\end{document}\n")
        print("Generated main.tex")

    def generate_bib_files(self) -> None:
        """
        Generate multiple structured .bib files for modular citation management.
        """
        bib_files = [
            "references.bib",
            "further_reading.bib",
            "bibliography.bib",
            "additional.bib",
            "manual.bib",
        ]
        for bib in bib_files:
            with open(bib, "w"):
                pass
            print(f"Created {bib}")

    def run(self) -> None:
        """
        Run the interactive generation process based on user input.
        """
        self.prompt_mode()
        self.prompt_chapter_count()

        front_files = (
            self.prompt_files(self.config.front)
            if self.config.manual
            else self.config.front.files
        )
        back_files = (
            self.prompt_files(self.config.back)
            if self.config.manual
            else self.config.back.files
        )
        chapter_files = self.config.chapter_files()

        self.create_empty_files(
            list(map(lambda f: os.path.join("main-matter", f), chapter_files))
        )
        self.create_empty_files(
            list(map(lambda f: os.path.join("front-matter", f), front_files))
        )
        self.create_empty_files(
            list(map(lambda f: os.path.join("back-matter", f), back_files))
        )
        self.generate_bib_files()
        self.generate_main_tex(front_files, chapter_files, back_files)


if __name__ == "__main__":
    BookStructureGenerator().run()
