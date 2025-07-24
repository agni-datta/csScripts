#!/usr/bin/env python3
"""
Computer Science Scripts Interactive Launcher

An interactive wrapper script that allows users to easily run any script
in the csScripts collection through a simple menu interface.

This module serves as the main entry point for the csScripts package,
providing a user-friendly interface to access all available scripts.
"""

import importlib.util
import os
import subprocess
import sys
from typing import Dict, List, Optional


class ScriptCategoryManager:
    """Manages script categories and their directory mappings."""

    def __init__(self):
        """Initialize the ScriptCategoryManager with predefined script categories."""
        self.script_category_directory_mapping = {
            "Document Management": "scripts/document",
            "File Operations": "scripts/file_ops",
            "Utilities": "scripts/utils",
        }

    def get_category_directory_mapping(self) -> Dict[str, str]:
        """Get the mapping of script categories to their directories.

        Returns:
            Dict[str, str]: A dictionary mapping category names to directory paths.
        """
        return self.script_category_directory_mapping


class ScriptDiscoveryService:
    """Discovers available scripts in the repository."""

    def __init__(
        self, root_directory_path: str, category_manager: ScriptCategoryManager
    ):
        """Initialize the ScriptDiscoveryService.

        Args:
            root_directory_path: The root directory of the script repository.
            category_manager: Manager for script categories.
        """
        self.root_directory_path = root_directory_path
        self.category_manager = category_manager

    def discover_available_scripts(self) -> Dict[str, str]:
        """Discover all available Python scripts in the repository.

        Returns:
            Dict[str, str]: A dictionary mapping script display names to their absolute paths.
        """
        discovered_script_collection = {}
        category_directory_mapping = (
            self.category_manager.get_category_directory_mapping()
        )

        for category_name, subdirectory_path in category_directory_mapping.items():
            category_absolute_directory_path = os.path.join(
                self.root_directory_path, subdirectory_path
            )

            if os.path.exists(category_absolute_directory_path):
                for script_filename in os.listdir(category_absolute_directory_path):
                    if script_filename.endswith(
                        ".py"
                    ) and not script_filename.startswith("__"):
                        script_display_name = script_filename[
                            :-3
                        ]  # Remove .py extension
                        script_absolute_path = os.path.join(
                            category_absolute_directory_path, script_filename
                        )
                        discovered_script_collection[
                            f"{category_name}: {script_display_name}"
                        ] = script_absolute_path

        return discovered_script_collection


class InteractiveMenuRenderer:
    """Renders the interactive menu for script selection."""

    def render_menu_header(self) -> None:
        """Render the menu header with formatting."""
        print("\n" + "=" * 60)
        print("                    csScripts Menu")
        print("=" * 60)
        print("Available scripts:\n")

    def render_menu_footer(self, exit_option_number: int) -> None:
        """Render the menu footer with exit option.

        Args:
            exit_option_number: The number to display for the exit option.
        """
        print(f"\n{exit_option_number:2d}. Exit")
        print("=" * 60)

    def render_menu_items(self, available_script_collection: Dict[str, str]) -> None:
        """Render the menu items for available scripts.

        Args:
            available_script_collection: Dictionary of available scripts.
        """
        if not available_script_collection:
            print("No scripts found! Please check the scripts directory.")
            return

        for menu_index, script_display_name in enumerate(
            available_script_collection.keys(), 1
        ):
            print(f"{menu_index:2d}. {script_display_name}")


class UserInputProcessor:
    """Processes user input for menu selection."""

    def get_validated_menu_selection(self, max_valid_option: int) -> Optional[int]:
        """Get and validate user menu selection.

        Args:
            max_valid_option: The maximum valid option number.

        Returns:
            Optional[int]: The validated user choice, None if invalid, or -1 to exit.
        """
        try:
            user_input_text = input("\nEnter your choice (number): ").strip()
            if not user_input_text:
                return None

            selected_menu_option_number = int(user_input_text)
            if 1 <= selected_menu_option_number <= max_valid_option:
                return selected_menu_option_number
            elif selected_menu_option_number == max_valid_option + 1:
                return -1  # Exit code
            else:
                print("Invalid choice. Please enter a number from the menu.")
                return None
        except ValueError:
            print("Please enter a valid number corresponding to a menu option.")
            return None

    def get_continue_session_preference(self) -> bool:
        """Get user preference for continuing the session.

        Returns:
            bool: True if user wants to continue, False otherwise.
        """
        continue_session_response = (
            input("\nWould you like to run another script? (y/N): ").strip().lower()
        )
        return continue_session_response == "y"


class ScriptExecutionService:
    """Handles the execution of selected scripts."""

    def execute_script(self, script_absolute_path: str) -> bool:
        """Execute a specific script with proper environment setup and error handling.

        Args:
            script_absolute_path: The absolute path to the script to execute.

        Returns:
            bool: True if execution was successful, False otherwise.
        """
        try:
            script_filename = os.path.basename(script_absolute_path)
            print(f"\nExecuting script: {script_filename}")
            print("-" * 40)

            # Change to the script's directory to ensure proper relative path resolution
            script_directory_path = os.path.dirname(script_absolute_path)
            original_working_directory_path = os.getcwd()
            os.chdir(script_directory_path)

            # Execute the script using the current Python interpreter
            execution_result = subprocess.run(
                [sys.executable, script_absolute_path],
                cwd=script_directory_path,
                capture_output=False,
            )

            # Restore the original working directory
            os.chdir(original_working_directory_path)

            # Provide feedback based on the execution result
            if execution_result.returncode == 0:
                print(f"\nScript executed successfully!")
                return True
            else:
                print(
                    f"\nScript execution failed with exit code {execution_result.returncode}"
                )
                return False

        except Exception as execution_error:
            print(f"Error executing script: {execution_error}")
            return False


class ScriptExecutionOrchestrator:
    """Orchestrates the script execution process."""

    def __init__(self):
        """Initialize the ScriptExecutionOrchestrator with necessary components."""
        self.root_directory_path = os.path.dirname(os.path.abspath(__file__))
        self.category_manager = ScriptCategoryManager()
        self.discovery_service = ScriptDiscoveryService(
            self.root_directory_path, self.category_manager
        )
        self.menu_renderer = InteractiveMenuRenderer()
        self.input_processor = UserInputProcessor()
        self.execution_service = ScriptExecutionService()
        self.available_script_collection = (
            self.discovery_service.discover_available_scripts()
        )

    def display_interactive_menu(self) -> None:
        """Display the interactive menu for script selection."""
        self.menu_renderer.render_menu_header()
        self.menu_renderer.render_menu_items(self.available_script_collection)
        self.menu_renderer.render_menu_footer(len(self.available_script_collection) + 1)

    def process_user_selection(self, user_selection: int) -> bool:
        """Process the user's menu selection.

        Args:
            user_selection: The user's menu selection.

        Returns:
            bool: True if processing should continue, False if session should end.
        """
        if user_selection == -1:
            # User selected exit option
            print("\nExiting csScripts. Goodbye!")
            return False
        else:
            # Valid script selection - get the script details and execute it
            selected_script_name = list(self.available_script_collection.keys())[
                user_selection - 1
            ]
            selected_script_path = self.available_script_collection[
                selected_script_name
            ]
            self.execution_service.execute_script(selected_script_path)

            # Ask if user wants to continue with another script
            if not self.input_processor.get_continue_session_preference():
                print("\nExiting csScripts. Goodbye!")
                return False
            return True

    def start_interactive_session(self) -> None:
        """Start the main interactive session loop for script selection and execution."""
        while True:
            self.display_interactive_menu()
            user_selection = self.input_processor.get_validated_menu_selection(
                max_valid_option=len(self.available_script_collection)
            )

            if user_selection is None:
                # Invalid selection, loop again
                continue

            should_continue = self.process_user_selection(user_selection)
            if not should_continue:
                break


class ApplicationLauncher:
    """Launches the csScripts application."""

    def display_welcome_message(self) -> None:
        """Display the welcome message for the application."""
        print("Welcome to csScripts!")
        print(
            "This interactive tool allows you to easily execute any script in the collection."
        )

    def launch_application(self) -> None:
        """Launch the csScripts application."""
        self.display_welcome_message()
        orchestrator = ScriptExecutionOrchestrator()
        orchestrator.start_interactive_session()


def main() -> None:
    """Main entry point for the csScripts application.

    This function initializes the application launcher and starts the application.
    """
    application_launcher = ApplicationLauncher()
    application_launcher.launch_application()


if __name__ == "__main__":
    main()
