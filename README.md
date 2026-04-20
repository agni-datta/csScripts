---
title: README
aliases: README
linter-yaml-title-alias: README
date created: Monday, April 20th 2026, 10:44:03 pm
date modified: Monday, April 20th 2026, 11:10:42 pm
---

## csScripts

Utility scripts for academic and research workflows—LaTeX document management, file operations, and productivity automation. Written in Python 3.10+ following Google style with full type hints.

### Directory Structure

```
csScripts/
├── pyproject.toml          # build + tool config (black, isort, ruff, mypy, pytest)
├── setup.py                # minimal shim (pyproject.toml is authoritative)
├── requirements.txt
├── script_launcher.py      # interactive menu launcher
├── scripts/
│   ├── document/           # LaTeX + PDF tools
│   │   ├── book_structure_generator.py
│   │   ├── check_british.py
│   │   ├── check_grammar.py
│   │   ├── check_spelling.py
│   │   ├── directory_indexer.py
│   │   ├── join_lines.py
│   │   ├── latex_auxiliary_cleaner.py
│   │   ├── latex_code_formatter.py
│   │   ├── latex_document_generator.py
│   │   ├── pdf_gpg_signer.py
│   │   ├── pdf_linearizer.py
│   │   ├── pdf_meta_analyzer.py
│   │   ├── pdf_to_eps_converter.py
│   │   ├── postscript_to_pdf_converter.py
│   │   ├── remove_blank_lines.py
│   │   └── remove_comments.py
│   ├── file_ops/           # Batch renaming, search, sync
│   │   ├── case_sensitive_file_renamer.py
│   │   ├── directory_batch_renamer.py
│   │   ├── file_batch_renamer.py
│   │   ├── file_search_utility.py
│   │   ├── fileops.py
│   │   ├── mirror_shell.py
│   │   └── pdf_batch_renamer.py
│   └── utils/              # System, git, image, packaging
│       ├── check_extensions.py
│       ├── chocolatey_installer.py
│       ├── code_formatter.py
│       ├── folder_compressor.py
│       ├── git_repository_reset.py
│       ├── gnome_templates.py
│       ├── image_to_nord_converter.py
│       ├── nfo_renamer.py
│       ├── package_housekeeping.py
│       ├── setup_submodules.py
│       └── track_repos.py
└── tests/
    ├── test_check_british.py
    ├── test_check_grammar.py
    ├── test_check_spelling.py
    ├── test_join_lines.py
    ├── test_remove_blank_lines.py
    └── test_remove_comments.py
```

### Requirements

- Python 3.10+
- External tools (where applicable): `aspell`, `latexmk`, `qpdf`, `ghostscript`, `rclone`, `7z`, `gpg`, `black`, `isort`

### Installation

```bash
git clone https://github.com/your-username/csScripts.git
cd csScripts
pip install -e .
# with dev tools:
pip install -e ".[dev]"
```

### CLI Entry Points

| Command | Script |
| --- | --- |
| `cs-book-generator` | `scripts/document/book_structure_generator.py` |
| `cs-latex-cleaner` | `scripts/document/latex_auxiliary_cleaner.py` |
| `cs-file-renamer` | `scripts/file_ops/file_batch_renamer.py` |
| `cs-pdf-renamer` | `scripts/file_ops/pdf_batch_renamer.py` |
| `cs-code-formatter` | `scripts/utils/code_formatter.py` |
| `cs-check-british` | `scripts/document/check_british.py` |
| `cs-check-grammar` | `scripts/document/check_grammar.py` |
| `cs-check-spelling` | `scripts/document/check_spelling.py` |

### Usage Examples

```bash
# Check a LaTeX project for British spellings
cs-check-british path/to/project/

# Remove LaTeX comments from a file
python -m scripts.document.remove_comments paper.tex

# Batch rename files with sequential numbers
cs-file-renamer /path/to/dir

# Format all Python files in a directory
cs-code-formatter /path/to/project
```

### Development

```bash
# Run tests
python3 -m pytest

# Format code
black scripts/ tests/
isort scripts/ tests/

# Lint
ruff check scripts/ tests/

# Type check
mypy scripts/
```

### License

MIT—see [LICENSE](LICENSE).
