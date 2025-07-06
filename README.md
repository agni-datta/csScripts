---
title: csScripts
linter-yaml-title-alias: csScripts
date created: Friday, February 21st 2025, 18:44:48
date modified: Sunday, July 6th 2025, 01:42:10
aliases: csScripts
---

# csScripts

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive collection of utility scripts for academic and research workflows, focusing on LaTeX document management, file operations, and productivity automation.

## Overview

csScripts provides a suite of Python utilities designed to streamline common tasks in academic writing, research, and document management. These tools are particularly useful for LaTeX projects, file organization, and batch processing operations.

## Features

### Document Management

- **LaTeX Document Generator**: Automated creation of structured LaTeX documents
- **LaTeX Code Formatter**: Consistent formatting and style enforcement
- **LaTeX Cleaner**: Remove auxiliary files and optimize document structure
- **Book Structure Generator**: Create complete book project structures
- **PDF Linearizer**: Optimize PDF files for web distribution

### File Operations

- **Batch File Renamer**: Bulk file renaming with pattern matching
- **Case Sensitive File Renamer**: Handle case-sensitive file systems
- **Directory Batch Renamer**: Organize directory structures
- **PDF Batch Renamer**: Manage PDF collections efficiently
- **File Search Utility**: Advanced file discovery and filtering

### Development Tools

- **Python Code Formatter**: Enforce consistent Python code style
- **Git Repository Reset**: Clean repository state management
- **PostScript to PDF Converter**: Document format conversion

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup

```bash
# Clone the repository
git clone https://github.com/your-username/csScripts.git
cd csScripts

# Install dependencies (if any)
pip install -r requirements.txt
```

## Quick Start

### Interactive Script Runner

```bash
python cs_scripts.py
```

### LaTeX Document Generation

```bash
python scripts/document/latex_document_generator.py
```

### File Batch Renaming

```bash
python scripts/file_ops/file_batch_renamer.py --pattern "*.pdf" --prefix "document_"
```

### Book Structure Creation

```bash
python scripts/document/book_structure_generator.py
```

## Usage Examples

### 1. Generate a Complete Book Structure

```python
from scripts.document.book_structure_generator import BookStructureGenerator

generator = BookStructureGenerator()
generator.config.chapters = 10
generator.run()
```

### 2. Clean LaTeX Project

```python
from scripts.document.latex_cleaner import LatexCleaner

cleaner = LatexCleaner()
cleaner.clean_directory("./my_latex_project")
```

### 3. Batch Rename Files

```python
from scripts.file_ops.file_batch_renamer import FileBatchRenamer

renamer = FileBatchRenamer()
renamer.rename_files(
    directory="./documents",
    pattern="*.pdf",
    prefix="research_",
    start_number=1
)
```

## Project Structure

```
csScripts/
├── README.md                 # This file
├── LICENSE                   # MIT License
├── requirements.txt          # Python dependencies
├── setup.py                 # Package setup
├── cs_scripts.py            # Interactive script runner
├── .gitignore              # Git ignore rules
├── .gitattributes          # Git attributes
├── scripts/                # Main script directory
│   ├── __init__.py
│   ├── document/           # Document management scripts
│   ├── file_ops/           # File operation scripts
│   └── utils/              # Utility scripts
├── tests/                  # Test suite
├── docs/                   # Documentation
└── examples/               # Usage examples
```

## Testing

Run the test suite to ensure everything works correctly:

```bash
python -m pytest tests/
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the need for better academic workflow automation
- Built with the academic and research community in mind
- Thanks to all contributors and users

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/your-username/csScripts/issues) page
2. Create a new issue with detailed information
3. Contact the maintainers

---

**Made with love for the academic community**
