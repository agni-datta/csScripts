#!/usr/bin/env python3
"""
Create GNOME Nautilus Templates with sane defaults.

This script builds a set of template files under ~/Templates using a pure OOP
design and Google style naming. Code templates include shebangs. The LaTeX
template uses the article class with common packages and targets LuaLaTeX.

Run:
    python3 create_templates.py
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional


class TemplateFile:
    """Represents a single template file.

    Attributes:
        name: Filename to create inside the templates directory.
        content: UTF-8 text content. Ignored if is_binary is True.
        is_binary: Whether to create an empty binary placeholder.
        executable: Whether to set the executable bit on the file.
    """

    def __init__(
        self,
        name: str,
        content: str = "",
        *,
        is_binary: bool = False,
        executable: bool = False,
    ) -> None:
        self._name = name
        self._content = content
        self._is_binary = is_binary
        self._executable = executable

    @property
    def name(self) -> str:
        """Return the filename."""
        return self._name

    def write_to(self, directory: Path) -> Path:
        """Write the template into the target directory if not present.

        Args:
            directory: Destination folder.

        Returns:
            The path to the file.
        """
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / self._name
        if not path.exists():
            if self._is_binary:
                path.touch(exist_ok=True)
            else:
                path.write_text(self._content, encoding="utf-8")
        if self._executable:
            mode = path.stat().st_mode
            path.chmod(mode | 0o111)
        return path


class TemplateCatalog:
    """Holds the catalog of template definitions."""

    _LATEX_MAIN: str = r"""\documentclass[11pt]{article}

% Engine: LuaLaTeX
% Compile: lualatex -halt-on-error -interaction=nonstopmode LaTeX.tex

\usepackage[a4paper,margin=1in]{geometry}
\usepackage{fontspec}           % LuaLaTeX font loading
\usepackage{unicode-math}       % Math with unicode support
\defaultfontfeatures{Ligatures=TeX}
\setmainfont{Latin Modern Roman}
\setmonofont{Latin Modern Mono}
\setmathfont{Latin Modern Math}

\usepackage{microtype}
\usepackage{amsmath,amssymb}
\usepackage{mathtools}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{csquotes}
\usepackage[hidelinks]{hyperref}

\title{Title}
\author{Author}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
Brief summary.
\end{abstract}

\section{Introduction}
Start writing.

\section{Results}
Content.

\section{Conclusion}
Content.

\bibliographystyle{plain}
% \bibliography{references}

\end{document}
"""

    _LATEX_MAKEFILE: str = r"""# Rename to 'Makefile' after creating a new document
TEX=LaTeX.tex
ENGINE=lualatex
FLAGS=-halt-on-error -interaction=nonstopmode

all:
	$(ENGINE) $(FLAGS) $(TEX)

clean:
	rm -f *.aux *.log *.out *.toc *.bcf *.run.xml *.bbl *.blg

distclean: clean
	rm -f *.pdf
"""

    def __init__(self) -> None:
        self._templates: List[TemplateFile] = []
        self._build_catalog()

    def _build_catalog(self) -> None:
        """Populate the internal template list."""
        self._templates.extend(
            [
                # Text and markup
                TemplateFile(
                    "Text File.txt",
                    "Title\n\nSummary:\n\n",
                ),
                TemplateFile(
                    "Markdown.md",
                    "# Title\n\nShort summary.\n\n## Section\n- Point 1\n- Point 2\n",
                ),
                TemplateFile(
                    "HTML Document.html",
                    "<!doctype html>\n"
                    '<html lang="en">\n<head>\n'
                    '  <meta charset="utf-8">\n'
                    '  <meta name="viewport" content="width=device-width,initial-scale=1">\n'
                    "  <title>Document</title>\n"
                    "</head>\n<body>\n"
                    "  <main>\n    <h1>Title</h1>\n    <p>Start writing.</p>\n  </main>\n"
                    "</body>\n</html>\n",
                ),
                TemplateFile(
                    "JSON.json",
                    '{\n  "name": "example",\n  "version": 1\n}\n',
                ),
                TemplateFile(
                    "YAML.yaml",
                    "name: example\nversion: 1\n",
                ),
                TemplateFile(
                    "XML.xml",
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    "<root>\n  <item>value</item>\n</root>\n",
                ),
                TemplateFile("CSV.csv", "column_a,column_b,column_c\n,,\n"),
                # Code with shebangs where applicable
                TemplateFile(
                    "Python.py",
                    "#!/usr/bin/env python3\n"
                    '"""Script description."""\n\n'
                    "from __future__ import annotations\n\n"
                    "def main() -> None:\n"
                    '    print("OK")\n\n'
                    'if __name__ == "__main__":\n'
                    "    main()\n",
                    executable=True,
                ),
                TemplateFile(
                    "Shell Script.sh",
                    "#!/usr/bin/env bash\n"
                    "set -euo pipefail\nIFS=$'\\n\\t'\n\n"
                    'echo "OK"\n',
                    executable=True,
                ),
                TemplateFile(
                    "JavaScript.js",
                    '"use strict";\n\n(function main() {\n  console.log("OK");\n})();\n',
                ),
                TemplateFile(
                    "C Source.c",
                    '#include <stdio.h>\n\nint main(void) {\n    puts("OK");\n    return 0;\n}\n',
                ),
                TemplateFile(
                    "C++ Source.cpp",
                    '#include <iostream>\nint main() {\n    std::cout << "OK\\n";\n    return 0;\n}\n',
                ),
                TemplateFile(
                    "Java.java",
                    "public class ClassName {\n"
                    "    public static void main(String[] args) {\n"
                    '        System.out.println("OK");\n'
                    "    }\n"
                    "}\n",
                ),
                # LaTeX
                TemplateFile("LaTeX.tex", self._LATEX_MAIN),
                TemplateFile("LaTeX Makefile", self._LATEX_MAKEFILE),
                # Office placeholders as empty binaries
                TemplateFile("Word Document.docx", is_binary=True),
                TemplateFile("Excel Spreadsheet.xlsx", is_binary=True),
                TemplateFile("PowerPoint.pptx", is_binary=True),
                TemplateFile("LibreOffice Writer.odt", is_binary=True),
                TemplateFile("LibreOffice Calc.ods", is_binary=True),
                TemplateFile("LibreOffice Impress.odp", is_binary=True),
                # Extras
                TemplateFile(
                    "HTML5 Boilerplate.html",
                    '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Document</title><main><h1>Title</h1></main></html>',
                ),
            ]
        )

    def list(self) -> Iterable[TemplateFile]:
        """Yield all template file definitions."""
        return list(self._templates)


class TemplateManager:
    """Coordinates writing templates to the system Templates directory."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self._home = Path.home() if base_dir is None else base_dir.expanduser()
        self._templates_dir = self._home / "Templates"
        self._catalog = TemplateCatalog()

    @property
    def templates_dir(self) -> Path:
        """Return the target templates directory."""
        return self._templates_dir

    def sync(self) -> List[Path]:
        """Write all catalog templates into the directory.

        Returns:
            List of paths that now exist in the directory.
        """
        paths: List[Path] = []
        for tpl in self._catalog.list():
            path = tpl.write_to(self._templates_dir)
            paths.append(path)
        return paths


class App:
    """Application entry point."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self._manager = TemplateManager(base_dir=base_dir)

    def run(self) -> None:
        """Execute the synchronization and print the target directory."""
        written = self._manager.sync()
        print(f"Templates directory: {self._manager.templates_dir}")
        print(f"Files present: {len(written)}")


if __name__ == "__main__":
    App().run()
