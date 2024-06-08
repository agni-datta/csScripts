import os
import subprocess


def break_text_to_columns(text, column_width):
    """
    Breaks a given text into lines based on a specified column width while preserving blank lines and existing spacing.

    Args:
        text (str): The input text to be broken into columns.
        column_width (int): The maximum number of characters per line.

    Returns:
        str: The text broken into lines of specified column width.
    """
    lines = text.splitlines()
    broken_lines = []

    for line in lines:
        if not line.strip():  # Preserve blank lines
            broken_lines.append("")
            continue

        words = line.split()
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= column_width:
                if current_line:
                    current_line += " "
                current_line += word
            else:
                broken_lines.append(current_line)
                current_line = word

        if current_line:
            broken_lines.append(current_line)

    return "\n".join(broken_lines)


def format_with_latexindent(input_file, output_file):
    """
    Formats a .tex file using latexindent.

    Args:
        input_file (str): The path to the input .tex file.
        output_file (str): The path to the output .tex file.

    Raises:
        FileNotFoundError: If the specified input .tex file does not exist.
        subprocess.CalledProcessError: If latexindent fails to run.
    """
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"The file {input_file} does not exist.")

    try:
        subprocess.run(
            ["latexindent", "--outputfile=" + output_file, input_file], check=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"latexindent failed: {e}")


def process_tex_file(file_path, column_width):
    """
    Processes a .tex file by breaking its content into columns, creating a backup,
    and formatting it with latexindent.

    Args:
        file_path (str): The path to the .tex file.
        column_width (int): The maximum number of characters per line.

    Raises:
        FileNotFoundError: If the specified .tex file does not exist.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    backup_file_path = f"{file_path}.bak"
    os.rename(file_path, backup_file_path)

    with open(backup_file_path, "r") as file:
        content = file.read()

    broken_text = break_text_to_columns(content, column_width)

    with open(file_path, "w") as file:
        file.write(broken_text)

    format_with_latexindent(file_path, file_path)


if __name__ == "__main__":
    # Get the file name from the user
    input_file_path = input("Enter the path to the .tex file: ")
    column_width = 80  # Adjust as needed

    try:
        process_tex_file(input_file_path, column_width)
        print(
            f"File processed successfully. A backup has been saved as {input_file_path}.bak"
        )
    except Exception as e:
        print(f"An error occurred: {e}")
