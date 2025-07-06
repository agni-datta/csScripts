#!/usr/bin/env python3
"""
Setup script for csScripts package.
"""

from setuptools import setup, find_packages
import os


# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()


# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [
            line.strip() for line in fh if line.strip() and not line.startswith("#")
        ]


setup(
    name="csScripts",
    version="1.0.0",
    author="Agni Datta",
    author_email="your.email@example.com",
    description="A comprehensive collection of utility scripts for academic and research workflows",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/csScripts",
    packages=find_packages(),
    classifiers=[
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
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    entry_points={
        "console_scripts": [
            "cs-book-generator=scripts.document.book_structure_generator:main",
            "cs-latex-cleaner=scripts.document.latex_cleaner:main",
            "cs-file-renamer=scripts.file_ops.file_batch_renamer:main",
            "cs-pdf-renamer=scripts.file_ops.pdf_batch_renamer:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
