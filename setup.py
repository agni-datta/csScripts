#!/usr/bin/env python3
"""
Setup script for Computer Science Scripts (csScripts) package.

This module provides the necessary configuration for packaging and distributing
the csScripts library according to Python packaging standards.
"""

import os

from setuptools import find_packages, setup


class PackageMetadataProvider:
    """
    Provider for package metadata extracted from documentation files.
    """

    @staticmethod
    def extract_readme_content() -> str:
        """Extract the README.md file content for package documentation.

        Returns:
            The complete textual content of the README.md file.
        """
        with open("README.md", "r", encoding="utf-8") as readme_file:
            return readme_file.read()

    @staticmethod
    def extract_requirements_list() -> list:
        """Extract the requirements list from requirements.txt file.

        Returns:
            A list of package dependencies required for installation.
        """
        with open("requirements.txt", "r", encoding="utf-8") as requirements_file:
            return [
                line.strip()
                for line in requirements_file
                if line.strip() and not line.startswith("#")
            ]


class PackageConfigurationService:
    """
    Service for providing comprehensive package configuration.
    """

    @staticmethod
    def generate_package_metadata():
        """Generate the complete package metadata for setup.

        Returns:
            Dictionary containing all package metadata configuration parameters.
        """
        metadata_provider = PackageMetadataProvider()

        return {
            "name": "csScripts",
            "version": "1.0.0",
            "author": "Agni Datta",
            "author_email": "agnidatta.org@gmail.com",
            "description": "A comprehensive collection of utility scripts for academic and research workflows",
            "long_description": metadata_provider.extract_readme_content(),
            "long_description_content_type": "text/markdown",
            "url": "https://github.com/your-username/csScripts",
            "packages": find_packages(),
            "classifiers": [
                "Development Status :: 4 - Beta",
                "Intended Audience :: Science/Research",
                "Intended Audience :: Education",
                "License :: OSI Approved :: MIT License",
                "Operating System :: OS Independent",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
                "Topic :: Scientific/Engineering",
                "Topic :: Text Processing :: Markup :: LaTeX",
                "Topic :: Utilities",
            ],
            "python_requires": ">=3.8",
            "install_requires": metadata_provider.extract_requirements_list(),
            "extras_require": {
                "dev": [
                    "pytest>=7.0.0",
                    "black>=22.0.0",
                    "flake8>=4.0.0",
                    "mypy>=0.950",
                ],
            },
            "entry_points": {
                "console_scripts": [
                    "cs_book_generator=scripts.document.book_structure_generator:main",
                    "cs_latex_cleaner=scripts.document.latex_auxiliary_cleaner:main",
                    "cs_file_renamer=scripts.file_ops.file_batch_renamer:main",
                    "cs_pdf_renamer=scripts.file_ops.pdf_batch_renamer:main",
                    "cs_code_formatter=scripts.utils.code_formatter:main",
                ],
            },
            "include_package_data": True,
            "zip_safe": False,
            "license": "MIT",
        }


setup(**PackageConfigurationService.generate_package_metadata())
