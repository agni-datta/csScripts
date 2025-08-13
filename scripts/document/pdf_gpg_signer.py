#!/usr/bin/env python3
"""
PDF GPG Signer Module

This module provides functionality to sign PDF files using GPG (GNU Privacy Guard).
It automates the process of finding PDF files and applying digital signatures to them.

Features:
- GPG installation verification
- Interactive GPG key selection
- Recursive PDF file discovery
- Batch signing of multiple files
- Detailed operation feedback

Usage:
    python3 sign_pdfs_with_gpg.py

Example:
    >>> service = PdfGpgSigningService()
    >>> service.execute_signing_process()
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List


class GpgInstallationVerifier:
    """
    Service for verifying GPG installation on the system.
    """

    @staticmethod
    def verify_gpg_installation() -> bool:
        """
        Verify that GPG is installed and available on the system.

        Returns:
            bool: True if GPG is installed, False otherwise.
        """
        try:
            subprocess.run(
                ["gpg", "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


class GpgKeyManagementService:
    """
    Service for managing GPG keys and key selection.
    """

    @staticmethod
    def retrieve_available_gpg_keys() -> List[Dict[str, str]]:
        """
        Retrieve all available GPG secret keys from the system.

        Returns:
            List[Dict[str, str]]: List of keys with keyid and user IDs.
        """
        result = subprocess.run(
            ["gpg", "--list-secret-keys", "--with-colons"],
            stdout=subprocess.PIPE,
            text=True,
        )

        available_keys = []
        current_key = None

        for line in result.stdout.splitlines():
            if line.startswith("sec"):  # Secret key line
                parts = line.split(":")
                key_id = str(parts[4])
                current_key = {"keyid": key_id, "uids": []}
                available_keys.append(current_key)
            elif line.startswith("uid") and current_key:  # User ID line
                user_id = str(line.split(":")[9])
                current_key["uids"].append(user_id)

        return available_keys


class UserInteractionService:
    """
    Service for handling user interactions.
    """

    @staticmethod
    def display_available_keys(available_keys: List[Dict[str, str]]) -> None:
        """
        Display available GPG keys to the user.

        Args:
            available_keys: List of available GPG keys.
        """
        print("Available GPG secret keys:")
        for index, key in enumerate(available_keys):
            print(f"[{index}] {key['keyid']} - {', '.join(key['uids'])}")

    @staticmethod
    def prompt_for_key_selection(available_keys: List[Dict[str, str]]) -> str:
        """
        Prompt the user to select a GPG key from the available keys.

        Args:
            available_keys: List of available GPG keys.

        Returns:
            str: The selected key ID.
        """
        while True:
            try:
                user_choice = int(
                    input("Enter the number of the key to use for signing: ")
                )
                if 0 <= user_choice < len(available_keys):
                    return available_keys[user_choice]["keyid"]
            except ValueError:
                pass
            print("Invalid choice. Please try again.")

    @staticmethod
    def display_message(message: str) -> None:
        """
        Display a message to the user.

        Args:
            message: The message to display.
        """
        print(message)


class PdfFileDiscoveryService:
    """
    Service for discovering PDF files in a directory structure.
    """

    @staticmethod
    def find_pdf_files_recursively(root_directory_path: Path) -> List[Path]:
        """
        Recursively find all PDF files in a directory and its subdirectories.

        Args:
            root_directory_path: The root directory to search.

        Returns:
            List of paths to PDF files found.
        """
        return list(root_directory_path.rglob("*.pdf"))


class GpgSigningService:
    """
    Service for signing files using GPG.
    """

    @staticmethod
    def sign_file_with_gpg(file_path: Path, key_id: str) -> bool:
        """
        Sign a file with the specified GPG key.

        Args:
            file_path: Path to the file to sign.
            key_id: ID of the GPG key to use for signing.

        Returns:
            bool: True if signing was successful, False otherwise.
        """
        signature_path = file_path.with_suffix(file_path.suffix + ".sig")
        print(f"Signing {file_path} -> {signature_path}")

        result = subprocess.run(
            [
                "gpg",
                "--batch",
                "--yes",
                "--local-user",
                str(key_id),
                "--output",
                str(signature_path),
                "--detach-sign",
                str(file_path),
            ],
            capture_output=True,
        )

        if result.returncode != 0:
            print(f"Failed to sign {file_path}")
            return False
        else:
            print(f"Signed: {signature_path}")
            return True


class PdfGpgSigningService:
    """
    Service for signing PDF files with GPG.
    """

    def __init__(self, target_directory_path: str = "."):
        """
        Initialize the PdfGpgSigningService.

        Args:
            target_directory_path: Directory to search for PDF files.
        """
        self.target_directory_path = Path(target_directory_path)
        self.selected_key_id = None

        # Initialize component services
        self.installation_verifier = GpgInstallationVerifier()
        self.key_management_service = GpgKeyManagementService()
        self.user_interaction_service = UserInteractionService()
        self.file_discovery_service = PdfFileDiscoveryService()
        self.signing_service = GpgSigningService()

    def execute_signing_process(self) -> None:
        """
        Execute the complete PDF signing process.
        """
        # Verify GPG installation
        if not self.installation_verifier.verify_gpg_installation():
            self.user_interaction_service.display_message(
                "GPG is not installed. Please install GPG and try again."
            )
            sys.exit(1)

        # Get available GPG keys
        available_keys = self.key_management_service.retrieve_available_gpg_keys()
        if not available_keys:
            self.user_interaction_service.display_message(
                "No GPG secret keys found. Please generate or import a key and try again."
            )
            sys.exit(1)

        # Display keys and get user selection
        self.user_interaction_service.display_available_keys(available_keys)
        self.selected_key_id = self.user_interaction_service.prompt_for_key_selection(
            available_keys
        )

        # Find PDF files
        pdf_files = self.file_discovery_service.find_pdf_files_recursively(
            self.target_directory_path
        )
        if not pdf_files:
            self.user_interaction_service.display_message("No PDF files found to sign.")
            return

        # Sign each PDF file
        successful_count = 0
        failed_count = 0

        for pdf_file_path in pdf_files:
            if self.signing_service.sign_file_with_gpg(
                pdf_file_path, self.selected_key_id
            ):
                successful_count += 1
            else:
                failed_count += 1

        # Display summary
        self.user_interaction_service.display_message(
            f"\nSigning complete: {successful_count} files signed successfully, {failed_count} files failed."
        )


class PdfGpgSigningApplicationLauncher:
    """
    Launcher for the PDF GPG signing application.
    """

    @staticmethod
    def launch_application(target_directory_path: str = ".") -> None:
        """
        Launch the PDF GPG signing application.

        Args:
            target_directory_path: Directory to search for PDF files.
        """
        signing_service = PdfGpgSigningService(target_directory_path)
        signing_service.execute_signing_process()


def main() -> None:
    """
    Main entry point for the PDF GPG signing script.
    """
    application_launcher = PdfGpgSigningApplicationLauncher()
    application_launcher.launch_application()


if __name__ == "__main__":
    main()
