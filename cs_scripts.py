#!/usr/bin/env python3
"""
csScripts Wrapper

An interactive wrapper script that allows users to easily run any script
in the csScripts collection through a simple menu interface.
"""

import os
import sys
import subprocess
from typing import Dict, List, Optional
import importlib.util


class ScriptRunner:
    """Manages and runs scripts from the csScripts collection."""

    def __init__(self):
        self.scripts_dir = os.path.dirname(os.path.abspath(__file__))
        self.available_scripts = self._discover_scripts()

    def _discover_scripts(self) -> Dict[str, str]:
        """Discover all available Python scripts in the repository."""
        scripts = {}

        # Define script categories and their directories
        categories = {
            "Document Management": "scripts/document",
            "File Operations": "scripts/file_ops",
            "Utilities": "scripts/utils",
        }

        for category, subdir in categories.items():
            category_path = os.path.join(self.scripts_dir, subdir)
            if os.path.exists(category_path):
                for file in os.listdir(category_path):
                    if file.endswith(".py") and not file.startswith("__"):
                        script_name = file[:-3]  # Remove .py extension
                        script_path = os.path.join(category_path, file)
                        scripts[f"{category}: {script_name}"] = script_path

        return scripts

    def display_menu(self) -> None:
        """Display the available scripts menu."""
        print("\n" + "=" * 60)
        print("                    csScripts Menu")
        print("=" * 60)
        print("Available scripts:\n")

        if not self.available_scripts:
            print("No scripts found!")
            return

        for i, (name, path) in enumerate(self.available_scripts.items(), 1):
            print(f"{i:2d}. {name}")

        print(f"\n{len(self.available_scripts) + 1:2d}. Exit")
        print("=" * 60)

    def get_user_choice(self) -> Optional[int]:
        """Get user choice from the menu."""
        try:
            choice = input("\nEnter your choice (number): ").strip()
            if not choice:
                return None

            choice_num = int(choice)
            if 1 <= choice_num <= len(self.available_scripts):
                return choice_num
            elif choice_num == len(self.available_scripts) + 1:
                return -1  # Exit
            else:
                print("Invalid choice. Please try again.")
                return None
        except ValueError:
            print("Please enter a valid number.")
            return None

    def run_script(self, script_path: str) -> None:
        """Run a specific script."""
        try:
            print(f"\nRunning: {os.path.basename(script_path)}")
            print("-" * 40)

            # Change to the script's directory
            script_dir = os.path.dirname(script_path)
            original_dir = os.getcwd()
            os.chdir(script_dir)

            # Run the script
            result = subprocess.run(
                [sys.executable, script_path], cwd=script_dir, capture_output=False
            )

            # Return to original directory
            os.chdir(original_dir)

            if result.returncode == 0:
                print(f"\nScript completed successfully!")
            else:
                print(f"\nScript exited with code {result.returncode}")

        except Exception as e:
            print(f"Error running script: {e}")

    def run(self) -> None:
        """Main run loop."""
        while True:
            self.display_menu()
            choice = self.get_user_choice()

            if choice is None:
                continue
            elif choice == -1:
                print("\nGoodbye!")
                break
            else:
                script_name = list(self.available_scripts.keys())[choice - 1]
                script_path = self.available_scripts[script_name]
                self.run_script(script_path)

                # Ask if user wants to run another script
                another = input("\nRun another script? (y/N): ").strip().lower()
                if another != "y":
                    print("\nGoodbye!")
                    break


def main():
    """Main entry point."""
    print("Welcome to csScripts!")
    print("This wrapper allows you to easily run any script in the collection.")

    runner = ScriptRunner()
    runner.run()


if __name__ == "__main__":
    main()
