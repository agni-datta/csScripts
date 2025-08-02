#!/usr/bin/env python3
"""
pdf_meta_analyzer.py

A modular, object-oriented tool for analyzing PDF files for metadata, font usage, and font embedding status.
Provides interactive file selection and rich terminal output.

Modules:
    pdf_meta_analyzer: Core PDF analysis logic.
    file_picker: Interactive file selection.
    output: Rich terminal output utilities.
    app: Application entry point.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import fitz
import PyPDF2
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table


class PDFMetadataExtractor:
    """Extracts metadata and font information from a PDF file."""

    def __init__(self, pdf_path: Path):
        """Initializes the extractor with the given PDF path."""
        self.pdf_path = pdf_path
        self.metadata: Dict[str, Any] = {}
        self.page_count: int = 0

    def extract(self) -> None:
        """Extracts document metadata and page count using PyPDF2."""
        with open(self.pdf_path, "rb") as file_handle:
            pdf_reader = PyPDF2.PdfReader(file_handle)
            self.page_count = len(pdf_reader.pages)
            self.metadata = dict(pdf_reader.metadata or {})

    def get_metadata(self) -> Dict[str, Any]:
        """Returns the extracted metadata."""
        return self.metadata

    def get_page_count(self) -> int:
        """Returns the total page count."""
        return self.page_count


class PDFFontExtractor:
    """Extracts font and embedding information from a PDF file."""

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.all_fonts: Set[str] = set()
        self.embedded_fonts: Set[str] = set()

    def extract(self) -> None:
        """Enumerates all fonts and embedded fonts in the PDF."""

        def _walk_pdf_object(
            pdf_object: Any, font_names: Set[str], embedded_fonts: Set[str]
        ) -> None:
            """Recursively walks PDF objects to find font and embedding info."""
            if isinstance(pdf_object, dict) and "/BaseFont" in pdf_object:
                font_names.add(pdf_object["/BaseFont"])
            if isinstance(pdf_object, dict):
                for key, value in pdf_object.items():
                    if isinstance(value, PyPDF2.generic.DictionaryObject):
                        if any(
                            font_file_key in value
                            for font_file_key in (
                                "/FontFile",
                                "/FontFile2",
                                "/FontFile3",
                            )
                        ):
                            embedded_fonts.add(value.get("/BaseFont", "<unknown>"))
                        _walk_pdf_object(value, font_names, embedded_fonts)
                    elif isinstance(value, PyPDF2.generic.ArrayObject):
                        for item in value:
                            if hasattr(item, "keys"):
                                _walk_pdf_object(item, font_names, embedded_fonts)

        with open(self.pdf_path, "rb") as file_handle:
            pdf_reader = PyPDF2.PdfReader(file_handle)
            for page in pdf_reader.pages:
                resources = page.get("/Resources", {})
                if resources:
                    _walk_pdf_object(resources, self.all_fonts, self.embedded_fonts)

    def get_all_fonts(self) -> Set[str]:
        """Returns all detected font names."""
        return self.all_fonts

    def get_embedded_fonts(self) -> Set[str]:
        """Returns all embedded font names."""
        return self.embedded_fonts


class PDFFontSpanExtractor:
    """Extracts font usage details from text spans using PyMuPDF."""

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path

    def extract(self) -> List[Tuple[int, str, float]]:
        """Returns a list of (page_number, font_name, font_size) tuples."""
        font_usage_records: List[Tuple[int, str, float]] = []
        document = fitz.open(str(self.pdf_path))
        for page in document:
            text_blocks = page.get_text("dict", sort=True)["blocks"]
            for block in text_blocks:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        font_name = span.get("font", "<no-font>")
                        font_size = span.get("size", 0.0)
                        font_usage_records.append(
                            (page.number + 1, font_name, font_size)
                        )
        document.close()
        return font_usage_records


class PDFAnalysisOutput:
    """Handles all rich output for PDF analysis."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def print_panel(self, pdf_path: Path) -> None:
        self.console.print(
            Panel(f"[bold cyan]PDF Meta Analyzer[/bold cyan]\nFile: {pdf_path}")
        )

    def print_metadata_table(self, metadata: Dict[str, Any], page_count: int) -> None:
        table = Table(title="Document Metadata", show_lines=True)
        table.add_column("Field", style="magenta")
        table.add_column("Value", style="white")
        table.add_row("Pages", str(page_count))
        for key, value in metadata.items():
            table.add_row(str(key), str(value))
        self.console.print(table)

    def print_fonts_summary_table(
        self, all_fonts: Set[str], embedded_fonts: Set[str]
    ) -> None:
        table = Table(title="Fonts Summary", show_lines=True)
        table.add_column("Font Name", style="magenta")
        table.add_column("Embedded", style="green")
        table.add_column("Subset", style="yellow")

        subset_prefixes: Tuple[str, ...] = tuple(
            chr(ord("A") + i) * 6 + "+" for i in range(26)
        )

        for font_name in sorted(all_fonts):
            is_embedded = font_name in embedded_fonts
            is_subset = font_name.startswith(subset_prefixes)
            table.add_row(
                font_name,
                "\u2714" if is_embedded else "\u2718",
                "\u26a0" if is_subset else "",
            )
        self.console.print(table)

    def print_font_spans_table(self, font_spans: List[Tuple[int, str, float]]) -> None:
        table = Table(title="Font Usage by Page", show_lines=False)
        table.add_column("Page", style="cyan")
        table.add_column("Font", style="magenta")
        table.add_column("Size", justify="right", style="white")
        for page_number, font_name, font_size in font_spans:
            table.add_row(str(page_number), font_name, f"{font_size:.1f}")
        self.console.print(table)

    def print_error(self, message: str) -> None:
        self.console.print(f"[red]{message}[/red]")


class PdfFilePicker:
    """Handles interactive selection of a PDF file from a directory and its subdirectories."""

    def __init__(
        self, search_directory: Path = Path("."), console: Optional[Console] = None
    ):
        self.search_directory = search_directory
        self.console = console or Console()

    def list_pdf_files(self) -> List[Path]:
        """Finds all PDF files in the search directory and all subdirectories."""
        return sorted(self.search_directory.rglob("*.pdf"))

    def prompt_for_pdf_file(self) -> Optional[Path]:
        """Prompts the user to select a PDF file interactively."""
        pdf_file_paths = self.list_pdf_files()
        if not pdf_file_paths:
            self.console.print(
                "[red]No PDF files found in this directory or its subdirectories.[/red]"
            )
            return None

        table = Table(title="Available PDF Files")
        table.add_column("Index", style="cyan", justify="right")
        table.add_column("Filename", style="magenta")
        table.add_column("Path", style="white")

        for index, pdf_file in enumerate(pdf_file_paths, start=1):
            table.add_row(str(index), pdf_file.name, str(pdf_file.parent))
        self.console.print(table)

        while True:
            user_choice = Prompt.ask(
                "Enter the index of the PDF to analyze", default="1"
            )
            try:
                selected_index = int(user_choice) - 1
                if 0 <= selected_index < len(pdf_file_paths):
                    return pdf_file_paths[selected_index]
                self.console.print("[red]Invalid index. Try again.[/red]")
            except ValueError:
                self.console.print("[red]Please enter a valid number.[/red]")


class PdfMetadataAnalyzer:
    """Coordinates the PDF analysis process."""

    def __init__(self, pdf_path: Path, console: Optional[Console] = None):
        self.pdf_path = pdf_path
        self.console = console or Console()
        self.output = PDFAnalysisOutput(self.console)
        self.metadata_extractor = PDFMetadataExtractor(pdf_path)
        self.font_extractor = PDFFontExtractor(pdf_path)
        self.font_span_extractor = PDFFontSpanExtractor(pdf_path)

    def analyze(self) -> None:
        """Performs the full PDF analysis and displays results in the terminal."""
        self.output.print_panel(self.pdf_path)

        self.metadata_extractor.extract()
        self.font_extractor.extract()
        font_spans = self.font_span_extractor.extract()

        self.output.print_metadata_table(
            self.metadata_extractor.get_metadata(),
            self.metadata_extractor.get_page_count(),
        )
        self.output.print_fonts_summary_table(
            self.font_extractor.get_all_fonts(),
            self.font_extractor.get_embedded_fonts(),
        )
        self.output.print_font_spans_table(font_spans)


class PdfMetadataAnalyzerApp:
    """Application entry point for PDF metadata analysis."""

    def __init__(self):
        self.console = Console()

    def get_pdf_path(self) -> Optional[Path]:
        """Handles command-line arguments and interactive PDF file selection."""
        if len(sys.argv) == 2:
            candidate_path = Path(sys.argv[1])
            if candidate_path.is_dir():
                file_picker = PdfFilePicker(
                    search_directory=candidate_path, console=self.console
                )
                return file_picker.prompt_for_pdf_file()
            else:
                return candidate_path
        else:
            script_root_directory = Path(__file__).parent.resolve()
            file_picker = PdfFilePicker(
                search_directory=script_root_directory, console=self.console
            )
            return file_picker.prompt_for_pdf_file()

    def run(self) -> None:
        """Runs the PdfMetadataAnalyzer application."""
        selected_pdf_file_path = self.get_pdf_path()
        if selected_pdf_file_path is None:
            sys.exit(1)
        if not selected_pdf_file_path.exists():
            self.console.print(
                f"[red]Error: file not found: {selected_pdf_file_path}[/red]"
            )
            sys.exit(1)
        analyzer = PdfMetadataAnalyzer(selected_pdf_file_path, console=self.console)
        analyzer.analyze()


def main():
    """Main entry point."""
    app = PdfMetadataAnalyzerApp()
    app.run()


if __name__ == "__main__":
    main()
