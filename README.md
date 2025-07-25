---
title: Computer Science Scripts (csScripts)
linter-yaml-title-alias: Computer Science Scripts (csScripts)
date created: Friday, February 21st 2025, 18:44:48
date modified: Friday, July 25th 2025, 21:56:08
aliases: Computer Science Scripts (csScripts)
---

# Computer Science Scripts (csScripts)

## Description

A comprehensive collection of utility scripts for academic and research workflows, with a focus on LaTeX document management, file operations, and productivity automation. This repository implements service-oriented architecture with descriptive naming conventions following Google’s style guide.

## Features

- **Document Management Services**
  - LaTeX document generation and compilation
  - LaTeX auxiliary file cleaning
  - Book structure generation
  - PDF linearization and optimization
  - PDF signing with GPG
  - Directory indexing
- **File Operation Services**
  - File and directory batch renaming
  - Case-sensitive file transformation
  - PDF metadata handling and batch processing
  - File search and discovery
- **Utility Services**
  - Code formatting and style enforcement
  - Git repository management
  - Python code optimization

## Directory Structure

```
csScripts/
├── README.md
├── LICENSE
├── requirements.txt
├── setup.py
├── script_launcher.py
├── scripts/
│   ├── __init__.py
│   ├── document/
│   │   ├── __init__.py
│   │   ├── book_structure_generator.py
│   │   ├── latex_auxiliary_cleaner.py
│   │   ├── latex_code_formatter.py
│   │   ├── latex_document_generator.py
│   │   ├── pdf_linearizer.py
│   │   ├── postscript_to_pdf_converter.py
│   │   ├── pdf_gpg_signer.py
│   │   └── directory_indexer.py
│   ├── file_ops/
│   │   ├── __init__.py
│   │   ├── case_sensitive_file_renamer.py
│   │   ├── directory_batch_renamer.py
│   │   ├── file_batch_renamer.py
│   │   ├── file_search_utility.py
│   │   └── pdf_batch_renamer.py
│   └── utils/
│       ├── __init__.py
│       ├── git_repository_reset.py
│       └── python_code_formatter.py
├── tests/
│   ├── __init__.py
│   ├── test_document.py
│   └── test_file_ops.py
├── docs/
│   └── README.md
└── examples/
    ├── example_batch_rename.py
    ├── example_latex_cleaner.py
    └── README.md
```

## Requirements

- Python 3.8 or higher
- Dependencies enumerated in `requirements.txt`

## Installation

### From Source Repository

```bash
git clone https://github.com/your-username/csScripts.git
cd csScripts
pip install -e .
```

### Using Package Manager

```bash
pip install csScripts
```

## Usage

### Interactive Script Launcher

Execute the interactive script launcher to access all available services:

```bash
python script_launcher.py
```

### Command Line Interfaces

After installation, the following command-line interfaces are available:

- `cs_book_generator` - Generate structured book templates
- `cs_latex_cleaner` - Clean LaTeX auxiliary files
- `cs_code_formatter` - Format code according to Google’s style guide
- `cs_file_renamer` - Perform batch file renaming operations
- `cs_pdf_renamer` - Process PDF files with metadata optimization

### Python API Integration

```python
from scripts.document.latex_auxiliary_cleaner import LatexAuxiliaryFileCleaningService

# Clean LaTeX auxiliary files in a directory
cleaning_service = LatexAuxiliaryFileCleaningService()
cleaning_service.execute_cleaning_process("/path/to/latex/project")
```

## Development Methodology

### Establishing Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Execute test suite
pytest

# Perform code quality analysis
flake8 scripts tests

# Conduct static type checking
mypy scripts tests
```

## Contribution Guidelines

Scholarly contributions are welcomed and encouraged. Please consult our [Contributing Guidelines](CONTRIBUTING.md) for comprehensive details on the contribution process.

## License

This project is distributed under the MIT License - see the [LICENSE](LICENSE) file for complete legal text.

## Contact Information

Maintained by Agni Datta. For inquiries or technical support, please open an issue in the repository or contact via electronic mail.
