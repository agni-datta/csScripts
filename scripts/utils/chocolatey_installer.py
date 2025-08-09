#!/usr/bin/env python3
"""
Chocolatey Package Installer Module

This module provides utilities for installing and managing packages using Chocolatey,
a package manager for Windows. It includes colorized terminal output, status reporting,
and structured result handling for package installation operations.

Author: Agni Datta
Date: 2024-07-12
Version: 2.0.0
"""

import os
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess, run
from typing import Any, Dict, List, Optional


# ANSI color codes for Google-style colored terminal output
class TerminalColor:
    HEADER: str = "\033[95m"
    OKBLUE: str = "\033[94m"
    OKCYAN: str = "\033[96m"
    OKGREEN: str = "\033[92m"
    WARNING: str = "\033[93m"
    FAIL: str = "\033[91m"
    ENDC: str = "\033[0m"
    BOLD: str = "\033[1m"
    UNDERLINE: str = "\033[4m"
    GREY: str = "\033[90m"


def color_text(text: str, color_code: str) -> str:
    """Wraps text with ANSI color codes.

    Args:
        text (str): The text to colorize.
        color_code (str): The ANSI color code.

    Returns:
        str: Colorized text.
    """
    return f"{color_code}{text}{TerminalColor.ENDC}"


class InstallStatus(Enum):
    """Enum representing the status of a package installation."""

    SUCCESS: str = "success"
    FAILED: str = "failed"
    SKIPPED: str = "skipped"
    ALREADY_INSTALLED: str = "already_installed"


@dataclass
class InstallResult:
    """Dataclass representing the result of a package installation.

    Attributes:
        package_name (str): Name of the package.
        status (InstallStatus): Status of the installation.
        error_message (Optional[str]): Error message if installation failed.
        processing_time (float): Time taken for installation in seconds.
        version (Optional[str]): Installed version, if available.
    """

    package_name: str
    status: InstallStatus
    error_message: Optional[str] = None
    processing_time: float = 0.0
    version: Optional[str] = None


class PackageFileLoader:
    """Utility class for loading package names from a file."""

    @staticmethod
    def load_package_names_from_file(file_path: str) -> List[str]:
        """Loads package names from a file, ignoring comments and blank lines.

        Args:
            file_path (str): Path to the package file.

        Returns:
            List[str]: List of package names.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If no valid packages are found.
        """
        package_file: Path = Path(file_path)
        if not package_file.exists():
            raise FileNotFoundError(f"Package file not found: {file_path}")

        packages: List[str] = []
        with open(package_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "#" in line:
                    line = line.split("#")[0].strip()
                if line:
                    packages.append(line)
        if not packages:
            raise ValueError(f"No valid packages found in {file_path}")
        return packages


class Logger:
    """Logger class for printing messages with optional verbosity and color."""

    def __init__(self, verbose: bool = True) -> None:
        """Initializes the Logger.

        Args:
            verbose (bool, optional): Whether to print messages. Defaults to True.
        """
        self.verbose: bool = verbose

    def log(self, message: str, color: Optional[str] = None) -> None:
        """Logs a message to the console, optionally with color.

        Args:
            message (str): The message to print.
            color (Optional[str], optional): ANSI color code. Defaults to None.
        """
        if self.verbose:
            if color:
                print(color_text(message, color))
            else:
                print(message)


class ChocolateyCommandChecker:
    """Utility class for checking the availability of the Chocolatey command."""

    @staticmethod
    def get_choco_command(logger: "Logger") -> str:
        """Checks if Chocolatey is available and returns the command name.

        Args:
            logger (Logger): Logger instance for output.

        Returns:
            str: The Chocolatey command.

        Raises:
            RuntimeError: If Chocolatey is not available or not on Windows.
        """
        if os.name != "nt":
            raise RuntimeError("Chocolatey is only available on Windows systems")
        choco_command: str = "choco"
        try:
            result: CompletedProcess = run(
                [choco_command, "--version"], capture_output=True, text=True, check=True
            )
            logger.log(
                f"Chocolatey version: {result.stdout.strip()}", TerminalColor.OKCYAN
            )
            return choco_command
        except (CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "Chocolatey not found. Please install Chocolatey first by running:\n"
                "Set-ExecutionPolicy Bypass -Scope Process -Force; "
                "[System.Net.ServicePointManager]::SecurityProtocol = "
                "[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
                "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
            )


class ChocolateyPackageChecker:
    """Utility class for checking if a package is already installed."""

    @staticmethod
    def is_package_installed(choco_command: str, package_name: str) -> bool:
        """Checks if a package is already installed via Chocolatey.

        Args:
            choco_command (str): The Chocolatey command.
            package_name (str): Name of the package.

        Returns:
            bool: True if installed, False otherwise.
        """
        try:
            base_package: str = package_name.split()[0]
            result: CompletedProcess = run(
                [choco_command, "list", "--local-only", base_package],
                capture_output=True,
                text=True,
                check=True,
            )
            return base_package.lower() in result.stdout.lower()
        except (CalledProcessError, FileNotFoundError):
            return False


class ChocolateyInstaller:
    """Class for installing Chocolatey packages and managing installation results."""

    def __init__(self, verbose: bool = True, dry_run: bool = False) -> None:
        """Initializes the ChocolateyInstaller.

        Args:
            verbose (bool, optional): Whether to print verbose output. Defaults to True.
            dry_run (bool, optional): If True, do not actually install. Defaults to False.
        """
        self.logger: Logger = Logger(verbose)
        self.dry_run: bool = dry_run
        self.choco_command: str = ChocolateyCommandChecker.get_choco_command(
            self.logger
        )
        self.results: List[InstallResult] = []
        self.packages_installed: int = 0
        self.packages_failed: int = 0
        self.packages_skipped: int = 0

    def install_package(self, package: str) -> InstallResult:
        """Installs a single Chocolatey package.

        Args:
            package (str): Name of the package to install.

        Returns:
            InstallResult: Result of the installation.
        """
        start_time: float = time.time()
        if ChocolateyPackageChecker.is_package_installed(self.choco_command, package):
            result: InstallResult = InstallResult(
                package_name=package,
                status=InstallStatus.ALREADY_INSTALLED,
                processing_time=time.time() - start_time,
            )
            self.results.append(result)
            self.packages_skipped += 1
            return result

        if self.dry_run:
            result: InstallResult = InstallResult(
                package_name=package,
                status=InstallStatus.SUCCESS,
                processing_time=time.time() - start_time,
            )
            self.results.append(result)
            return result

        try:
            self.logger.log(f"Installing {package}...", TerminalColor.OKBLUE)
            cmd: List[str] = [
                self.choco_command,
                "install",
                package,
                "-y",
                "--no-progress",
            ]
            completed: CompletedProcess = run(
                cmd, capture_output=True, text=True, check=True
            )
            version: Optional[str] = self._extract_version_from_output(completed.stdout)
            installation_result: InstallResult = InstallResult(
                package_name=package,
                status=InstallStatus.SUCCESS,
                processing_time=time.time() - start_time,
                version=version,
            )
            self.results.append(installation_result)
            self.packages_installed += 1
            return installation_result
        except CalledProcessError as e:
            error_msg: str = f"Chocolatey error: {e.stderr}" if e.stderr else str(e)
            result: InstallResult = InstallResult(
                package_name=package,
                status=InstallStatus.FAILED,
                error_message=error_msg,
                processing_time=time.time() - start_time,
            )
            self.results.append(result)
            self.packages_failed += 1
            return result
        except Exception as e:
            result: InstallResult = InstallResult(
                package_name=package,
                status=InstallStatus.FAILED,
                error_message=f"Unexpected error: {e}",
                processing_time=time.time() - start_time,
            )
            self.results.append(result)
            self.packages_failed += 1
            return result

    def _extract_version_from_output(self, output: str) -> Optional[str]:
        """Extracts the version string from Chocolatey output.

        Args:
            output (str): The output from Chocolatey.

        Returns:
            Optional[str]: The version string if found, else None.
        """
        if not output:
            return None
        for line in output.split("\n"):
            if "version" in line.lower() and any(char.isdigit() for char in line):
                return line.strip()
        return None

    def install_packages(self, packages: List[str]) -> Dict[str, Any]:
        """Installs a list of Chocolatey packages.

        Args:
            packages (List[str]): List of package names.

        Returns:
            Dict[str, Any]: Summary of the installation operation.
        """
        total_packages: int = len(packages)
        self.logger.log(
            f"Starting installation of {total_packages} packages...",
            TerminalColor.HEADER,
        )
        self.logger.log("=" * 60, TerminalColor.GREY)
        if self.dry_run:
            self.logger.log(
                "DRY RUN MODE: No actual installation will be performed",
                TerminalColor.WARNING,
            )
        for i, package in enumerate(packages, 1):
            self.logger.log(
                f"\n[{i}/{total_packages}] Processing: {package}",
                TerminalColor.OKCYAN,
            )
            result: InstallResult = self.install_package(package)
            if result.status == InstallStatus.SUCCESS:
                self.logger.log(
                    f"✓ Successfully installed {package}", TerminalColor.OKGREEN
                )
            elif result.status == InstallStatus.ALREADY_INSTALLED:
                self.logger.log(
                    f"⚠ Already installed: {package}", TerminalColor.WARNING
                )
            else:
                self.logger.log(
                    f"✗ Failed to install {package}: {result.error_message}",
                    TerminalColor.FAIL,
                )
        return self.get_installation_summary()

    def install_packages_from_file(self, file_path: str) -> Dict[str, Any]:
        """Installs packages listed in a file.

        Args:
            file_path (str): Path to the package file.

        Returns:
            Dict[str, Any]: Summary of the installation operation.
        """
        try:
            packages: List[str] = PackageFileLoader.load_package_names_from_file(
                file_path
            )
        except (FileNotFoundError, ValueError) as e:
            return {
                "success": False,
                "error": str(e),
                "packages_processed": 0,
                "packages_installed": 0,
                "packages_failed": 0,
                "packages_skipped": 0,
            }
        return self.install_packages(packages)

    def get_installation_summary(self) -> Dict[str, Any]:
        """Summarizes the installation results.

        Returns:
            Dict[str, Any]: Summary statistics.
        """
        total_processed: int = len(self.results)
        if total_processed == 0:
            return {"message": "No installations performed"}
        successful: List[InstallResult] = [
            r for r in self.results if r.status == InstallStatus.SUCCESS
        ]
        failed: List[InstallResult] = [
            r for r in self.results if r.status == InstallStatus.FAILED
        ]
        skipped: List[InstallResult] = [
            r for r in self.results if r.status == InstallStatus.ALREADY_INSTALLED
        ]
        total_time: float = sum(r.processing_time for r in self.results)
        average_time: float = (
            total_time / total_processed if total_processed > 0 else 0.0
        )
        return {
            "success": True,
            "total_packages": total_processed,
            "packages_installed": len(successful),
            "packages_failed": len(failed),
            "packages_skipped": len(skipped),
            "success_rate": (
                (len(successful) / total_processed * 100) if total_processed > 0 else 0
            ),
            "total_time": total_time,
            "average_time": average_time,
        }

    def backup_installed_packages(
        self, output_file: str = "installed_packages.txt"
    ) -> bool:
        """Backs up the list of currently installed Chocolatey packages to a file.

        Args:
            output_file (str, optional): Output file path. Defaults to "installed_packages.txt".

        Returns:
            bool: True if backup succeeded, False otherwise.
        """
        try:
            result: CompletedProcess = run(
                [self.choco_command, "list", "-l", "-r", "--id-only"],
                capture_output=True,
                text=True,
                check=True,
            )
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("# Backup of installed Chocolatey packages\n")
                f.write(f"# Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("# Format: choco install <package> -y\n\n")
                for package in result.stdout.strip().split("\n"):
                    if package.strip():
                        f.write(f"choco install {package.strip()} -y\n")
            self.logger.log(f"Backup created: {output_file}", TerminalColor.OKGREEN)
            return True
        except (CalledProcessError, FileNotFoundError) as e:
            self.logger.log(f"Failed to create backup: {e}", TerminalColor.FAIL)
            return False


class ChocolateyInstallerCLI:
    """Command-line interface for the ChocolateyInstaller."""

    def __init__(self) -> None:
        """Initializes the CLI."""
        self.installer: Optional[ChocolateyInstaller] = None

    def run(self) -> None:
        """Runs the CLI workflow."""
        self._print_header()
        self.installer = self._initialize_installer()
        package_file: str = self._get_package_file_path()
        self._maybe_create_backup()
        result: Dict[str, Any] = self.installer.install_packages_from_file(package_file)
        self._handle_result(result)

    def _print_header(self) -> None:
        """Prints the CLI header."""
        print(color_text("Chocolatey Package Installer", TerminalColor.HEADER))
        print(color_text("=" * 40, TerminalColor.GREY))

    def _initialize_installer(self) -> ChocolateyInstaller:
        """Initializes the ChocolateyInstaller instance.

        Returns:
            ChocolateyInstaller: The installer instance.

        Raises:
            SystemExit: If Chocolatey is not available.
        """
        try:
            return ChocolateyInstaller(verbose=True)
        except RuntimeError as e:
            print(color_text(f"Error: {e}", TerminalColor.FAIL))
            sys.exit(1)

    def _get_default_package_file(self) -> str:
        """Gets the default package file path.

        Returns:
            str: Default package file path.
        """
        return str(Path(__file__).parent.parent / "setup" / "pkg_chocolatey.txt")

    def _get_package_file_path(self) -> str:
        """Prompts the user for the package file path.

        Returns:
            str: The package file path.
        """
        default_file: str = self._get_default_package_file()
        package_file: str = input(
            color_text(
                f"Enter path to package file (default: {default_file}): ",
                TerminalColor.OKCYAN,
            )
        ).strip()
        if not package_file:
            package_file = default_file
        return package_file

    def _maybe_create_backup(self) -> None:
        """Prompts the user to optionally create a backup of installed packages."""
        backup_choice: str = (
            input(
                color_text(
                    "Create backup of currently installed packages? (y/N): ",
                    TerminalColor.OKCYAN,
                )
            )
            .strip()
            .lower()
        )
        if backup_choice in ["y", "yes"]:
            self.installer.backup_installed_packages()

    def _handle_result(self, result: Dict[str, Any]) -> None:
        """Handles and prints the result summary.

        Args:
            result (Dict[str, Any]): The result summary.
        """
        if not result.get("success", False):
            print(
                color_text(
                    f"Error: {result.get('error', 'Unknown error')}", TerminalColor.FAIL
                )
            )
            sys.exit(1)
        print("\n" + color_text("=" * 60, TerminalColor.GREY))
        print(color_text("Installation Summary:", TerminalColor.HEADER))
        print(
            color_text(
                f"  Total packages: {result['total_packages']}", TerminalColor.OKCYAN
            )
        )
        print(
            color_text(
                f"  Successfully installed: {result['packages_installed']}",
                TerminalColor.OKGREEN,
            )
        )
        print(
            color_text(
                f"  Failed installations: {result['packages_failed']}",
                TerminalColor.FAIL,
            )
        )
        print(
            color_text(
                f"  Skipped (already installed): {result['packages_skipped']}",
                TerminalColor.WARNING,
            )
        )
        print(
            color_text(
                f"  Success rate: {result['success_rate']:.1f}%", TerminalColor.OKBLUE
            )
        )
        if result["total_packages"] > 0:
            print(
                color_text(
                    f"  Total time: {result['total_time']:.2f} seconds",
                    TerminalColor.GREY,
                )
            )
            print(
                color_text(
                    f"  Average time per package: {result['average_time']:.2f} seconds",
                    TerminalColor.GREY,
                )
            )


def main() -> None:
    """Main entry point for the ChocolateyInstaller CLI."""
    cli: ChocolateyInstallerCLI = ChocolateyInstallerCLI()
    cli.run()


if __name__ == "__main__":
    main()
