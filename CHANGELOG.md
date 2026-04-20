---
title: CHANGELOG
linter-yaml-title-alias: CHANGELOG
date created: Monday, April 20th 2026, 10:44:39 pm
date modified: Monday, April 20th 2026, 11:10:41 pm
aliases: CHANGELOG
---

## CHANGELOG

### Version 1.1.0—2026-04-21

#### Breaking Changes

- Entry point names changed from `cs_*` (underscores) to `cs-*` (hyphens) per PEP convention.
- `python_code_formatter.py` removed—functionality merged into `code_formatter.py`.
- `setup.py` replaced by `pyproject.toml` as the authoritative build/tool config.

#### Fixes

- `check_british.py`, `check_grammar.py`, `check_spelling.py` were broken (called with a literal `"*.tex"` at module level). Rewritten as proper CLI tools accepting file/directory arguments.

#### Improvements

- `join_lines.py`, `remove_blank_lines.py`, `remove_comments.py` rewritten with OOP, type hints, and Google-style documentation strings.
- `pyproject.toml` added with `[tool.black]`, `[tool.isort]`, `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest]` sections.
- Thirty unit tests added covering all rewritten document scripts.
- New CLI entry points: `cs-check-british`, `cs-check-grammar`, `cs-check-spelling`.
- `requirements.txt` updated and cleaned.

---

### Version 1.0.0—2025-07-17

#### **Document Management Services**

- **LaTeX Document System**: Complete generation and compilation framework
- **LaTeX Auxiliary File Management**: Comprehensive cleaning and optimization service
- **Book Structure Generation**: Automated framework for academic book creation
- **PDF Optimization**: Linearization and optimization service for large documents
- **PDF Cryptographic Signing**: GPG integration for document security and verification
- **Directory Indexing**: Metadata extraction and indexing service

#### **File Operations Services**

- **Batch Renaming System**: File and directory transformation capabilities
- **Case-Sensitive Transformations**: Advanced file naming and organization tools
- **PDF Metadata Handling**: Batch processing and metadata management
- **File Discovery Service**: Pattern matching and search capabilities

#### **Utility Services**

- **Code Formatting**: Style enforcement and optimization tools
- **Git Repository Management**: Automated version control operations
- **Python Code Optimization**: Performance enhancement and analysis tools

#### **Technical Architecture**

- **Service-Oriented Design**: Modular architecture with separation of concerns
- **Google Naming Conventions**: Descriptive and consistent naming standards
- **Comprehensive Testing**: Unit and integration testing framework
- **Error Handling**: Robust logging and error management mechanisms
- **Type Safety**: Static typing implementation for reliability
- **Open Source**: MIT License for community distribution

#### **Documentation & Standards**

- **Academic Documentation**: Comprehensive implementation guides
- **Exemplar Scripts**: Reference implementations and examples
- **Testing Framework**: Extensive validation and quality assurance
