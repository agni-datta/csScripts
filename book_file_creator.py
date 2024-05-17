import os


class TexFileCreator:
    """
    A class for creating an organized structure of empty .tex files for book writing.

    This class facilitates the creation of an organized structure of empty .tex files
    following Don Knuth's logical style for writing books. It includes folders for
    main-matter, front-matter, and back-matter, along with chapter files, and various
    front and back matter files.

    Attributes:
        num_chapters (int): The number of chapter files to create.
    """

    def __init__(self):
        """
        Initialize the TexFileCreator with default values.
        """
        self.num_chapters = 0

    def get_num_chapters(self):
        """
        Prompt the user to enter the number of chapter files to create.

        Returns:
            int: The number of chapter files to create.
        """
        while True:
            try:
                num_chapters = int(input("Enter the number of chapters: "))
                if num_chapters < 0:
                    print("Please enter a non-negative integer.")
                else:
                    return num_chapters
            except ValueError:
                print("Invalid input. Please enter a valid integer.")

    def create_tex_file(self, filename):
        """
        Create an empty .tex file.

        Args:
            filename (str): The name of the .tex file to create.
        """
        with open(filename, "w"):
            pass  # No content needs to be written

    def create_files(self, filenames, folder_name):
        """
        Create empty .tex files in the specified folder.

        Args:
            filenames (list): A list of filenames for .tex files.
            folder_name (str): The name of the folder to create for the files.
        """
        os.makedirs(folder_name, exist_ok=True)
        for filename in filenames:
            filepath = os.path.join(folder_name, filename)
            self.create_tex_file(filepath)
            print(f"Created empty file: {filepath}")

    def create_main_file(self):
        """
        Create the main.tex file that includes all the created files.
        """
        tex_files = []
        for root, _, files in os.walk("."):
            for file in files:
                if file.endswith(".tex"):
                    tex_files.append(os.path.join(root, file))

        with open("main.tex", "w") as main_file:
            main_file.write("\\documentclass{book}\n")
            main_file.write("\\usepackage{csbook}\n")
            main_file.write("\\begin{document}\n")
            main_file.write("\\frontmatter\n")
            for tex_file in tex_files:
                if "front-matter" in tex_file:
                    main_file.write("\\input{" + tex_file + "}\n")
            main_file.write("\\mainmatter\n")
            for tex_file in tex_files:
                if "main-matter" in tex_file:
                    main_file.write("\\input{" + tex_file + "}\n")
            main_file.write("\\backmatter\n")
            for tex_file in tex_files:
                if "back-matter" in tex_file:
                    main_file.write("\\input{" + tex_file + "}\n")
            main_file.write("\\bibliographystyle{plain}\n")
            main_file.write("\\bibliography{bibliography}\n")
            main_file.write("\\end{document}\n")

    def create_bibliography_file(self):
        """
        Create the bibliography.bib file.
        """
        self.create_tex_file("bibliography.bib")

    def run(self):
        """
        Create the organized structure of empty .tex files, the main.tex file, and bibliography.bib.
        """
        self.num_chapters = self.get_num_chapters()

        folders = ["main-matter", "front-matter", "back-matter"]
        files_front = [
            "colophon.tex",
            "preface.tex",
            "foreword.tex",
            "acknowledgements.tex",
            "title_page.tex",
            "dedication.tex",
            "epigraph.tex",
        ]
        files_back = ["appendix.tex", "listings.tex", "glossaries.tex", "acronyms.tex"]

        for folder in folders:
            if folder == "main-matter" and self.num_chapters > 0:
                self.create_files(
                    [f"chapter{i}.tex" for i in range(1, self.num_chapters + 1)], folder
                )
            elif folder == "front-matter":
                self.create_files(files_front, folder)
            elif folder == "back-matter":
                self.create_files(files_back, folder)

        self.create_main_file()
        self.create_bibliography_file()


if __name__ == "__main__":
    tex_creator = TexFileCreator()
    tex_creator.run()
