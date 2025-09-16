#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compress a folder into a .7z archive using 7-Zip with maximum compression.

- Uses all available CPU threads
- Solid compression with specified block and dictionary sizes
- Displays a file-count progress bar
- Reports original size, compressed size, and compression ratio
- Uses ANSI colors for terminal output (no external color libraries)
- Checks for 7z installation and suggests OS-specific install commands

Author: Agni Datta
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from tqdm import tqdm


# ======== Colors ========
class AnsiColors:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"

    @staticmethod
    def color_text(text: str, color_code: str) -> str:
        return f"{color_code}{text}{AnsiColors.RESET}"


# ======== SevenZip Checker ========
class SevenZipChecker:
    @staticmethod
    def is_seven_zip_installed() -> bool:
        return shutil.which("7z") is not None

    @staticmethod
    def suggest_install_command() -> str:
        os_name = platform.system()
        if os_name == "Linux":
            distro = SevenZipChecker._detect_linux_distro()
            if "debian" in distro or "ubuntu" in distro:
                return "sudo apt install p7zip-full"
            elif "fedora" in distro or "rhel" in distro:
                return "sudo dnf install p7zip"
            elif "arch" in distro or "manjaro" in distro:
                return "sudo pacman -S p7zip"
            else:
                return "Use your distro's package manager to install p7zip"
        elif os_name == "Darwin":
            return "brew install p7zip"
        elif os_name == "Windows":
            return "Download and install from https://www.7-zip.org/"
        return "Please install 7z manually for your OS."

    @staticmethod
    def _detect_linux_distro() -> str:
        try:
            with open("/etc/os-release", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("ID="):
                        return line.strip().split("=")[1].strip('"').lower()
        except Exception:
            return ""
        return ""


# ======== Utilities ========
def human_readable_size(num_bytes: int, suffix: str = "B") -> str:
    """Convert bytes to human-readable format (KB, MB, GB, etc)."""
    for unit in ["", "K", "M", "G", "T", "P"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f}{unit}{suffix}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f}E{suffix}"


def count_files(folder: Path) -> int:
    """Count number of files in folder and subfolders."""
    total = 0
    for _, _, files in os.walk(folder):
        total += len(files)
    return total or 1


def folder_size(folder: Path) -> int:
    """Calculate total size of all files in folder."""
    total = 0
    for root, _, files in os.walk(folder):
        for f in files:
            try:
                fp = Path(root) / f
                total += fp.stat().st_size
            except Exception:
                pass
    return total


def file_size(file_path: Path) -> int:
    """Return file size in bytes or 0 if not found."""
    try:
        return file_path.stat().st_size
    except Exception:
        return 0


# ======== Compressor Config ========
class CompressorConfig:
    def __init__(self, block_size_kb: int = 1024, dict_size_mb: int = 1536):
        self.block_size_kb = block_size_kb
        self.dict_size_mb = dict_size_mb
        self.cpu_threads = os.cpu_count() or 1

    def to_7z_args(self) -> list[str]:
        return [
            "-mx=9",  # max compression
            "-ms=on",  # solid compression
            f"-mmt={self.cpu_threads}",  # use all threads
            f"-md={self.dict_size_mb}m",  # dictionary size
            "-mfb=273",  # word size
            "-bb0",  # minimal output
        ]


# ======== Folder Compressor ========
class FolderCompressor:
    def __init__(
        self, source_folder: str, output_filename: str, config: CompressorConfig
    ):
        self.source_folder = Path(source_folder).resolve()
        self.output_filename = Path(output_filename).with_suffix(".7z").resolve()
        self.config = config

    def compress(self) -> None:
        if not self.source_folder.exists() or not self.source_folder.is_dir():
            raise FileNotFoundError(f"Invalid source directory: {self.source_folder}")

        total_files = count_files(self.source_folder)
        original_size = folder_size(self.source_folder)

        print(
            AnsiColors.color_text(
                f"[INFO] Compressing '{self.source_folder}' → '{self.output_filename}' using {self.config.cpu_threads} threads",
                AnsiColors.BLUE,
            )
        )

        cmd = (
            ["7z", "a", "-t7z"]
            + self.config.to_7z_args()
            + [str(self.output_filename), str(self.source_folder)]
        )

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )

        with tqdm(total=total_files, desc="Files", unit="file") as pbar:
            for root, _, files in os.walk(self.source_folder):
                for _ in files:
                    pbar.update(1)

        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            print(
                AnsiColors.color_text(
                    f"[ERROR] 7z exited with code {proc.returncode}", AnsiColors.RED
                )
            )
            print(stderr)
            raise RuntimeError(f"7z failed: {stderr.strip()}")

        compressed_size = file_size(self.output_filename)
        reduction_bytes = original_size - compressed_size
        reduction_pct = (
            (reduction_bytes / original_size * 100) if original_size else 0.0
        )

        print(
            AnsiColors.color_text(
                f"[SUCCESS] Archive created: {self.output_filename}", AnsiColors.GREEN
            )
        )
        print(
            AnsiColors.color_text(
                f"Original size: {human_readable_size(original_size)}", AnsiColors.CYAN
            )
        )
        print(
            AnsiColors.color_text(
                f"Compressed size: {human_readable_size(compressed_size)}",
                AnsiColors.CYAN,
            )
        )
        print(
            AnsiColors.color_text(
                f"Size reduced by: {human_readable_size(reduction_bytes)} ({reduction_pct:.2f}%)",
                AnsiColors.YELLOW,
            )
        )


# ======== CLI Handler ========
class CLI:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="Compress a folder into a .7z archive with maximum compression and progress"
        )
        self._setup_arguments()

    def _setup_arguments(self):
        self.parser.add_argument("source", help="Folder to compress")
        self.parser.add_argument(
            "output", help="Output archive name (without extension)"
        )
        self.parser.add_argument(
            "--block-size",
            type=int,
            default=1024,
            help="Block size in KB (default: 1024)",
        )
        self.parser.add_argument(
            "--dict-size",
            type=int,
            default=1536,
            help="Dictionary size in MB (default: 1536)",
        )

    def parse(self):
        args = self.parser.parse_args()

        if not SevenZipChecker.is_seven_zip_installed():
            print(AnsiColors.color_text("[ERROR] 7z not found in PATH", AnsiColors.RED))
            print(
                AnsiColors.color_text(
                    f"[HINT] {SevenZipChecker.suggest_install_command()}",
                    AnsiColors.YELLOW,
                )
            )
            sys.exit(1)

        config = CompressorConfig(
            block_size_kb=args.block_size, dict_size_mb=args.dict_size
        )

        compressor = FolderCompressor(args.source, args.output, config)

        try:
            compressor.compress()
        except Exception as e:
            print(AnsiColors.color_text(f"[ERROR] {e}", AnsiColors.RED))
            sys.exit(1)


def main():
    cli = CLI()
    cli.parse()


if __name__ == "__main__":
    main()
