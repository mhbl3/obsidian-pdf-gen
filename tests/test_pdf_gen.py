import os
import logging
import pytest
import shutil
from obsidian_pdf_gen.generate_pdf.md_notes_pdf import ObsiPdfGenerator

logger = logging.getLogger("ObiPdfGen")
logger.setLevel(logging.DEBUG)


class TestPdfGen:
    @pytest.mark.parametrize(
        "note,note_paths,path,colorfull_headers,toc",
        [
            (
                None,
                # No .md on purpose
                "./test_files/simple_md_codeblock",
                "./test_files/simple_md_codeblock.tex",
                False,
                False,
            ),
            (
                None,
                "./test_files/multiple_codeblocks.md",
                "./test_files/multiple_codeblocks.tex",
                False,
                False,
            ),
            (
                None,
                "./test_files/colorful_headers.md",
                "./test_files/colorful_headers.tex",
                True,
                False,
            ),
            (
                None,
                "./test_files/latex_equation.md",
                "./test_files/latex_equation.tex",
                False,
                False,
            ),
            (
                None,
                "./test_files/bullet_points.md",
                "./test_files/bullet_points.tex",
                False,
                False,
            ),
            (
                None,
                "./test_files/linked_notes_1.md",
                "./test_files/linked_notes_1.tex",
                False,
                True,
            ),
            (
                None,
                "./test_files/table.md",
                "./test_files/table.tex",
                False,
                False,
            ),
            (
                None,
                "./test_files/block_quote.md",
                "./test_files/block_quote.tex",
                False,
                False,
            ),
            (
                None,
                "./test_files/front_matter.md",
                "./test_files/front_matter.tex",
                False,
                False,
            ),
            (
                None,
                "./test_files/hyperlinks.md",
                "./test_files/hyperlinks.tex",
                False,
                False,
            ),
            (
                None,
                "./test_files/Damping Ratio.md",
                "./test_files/Damping Ratio.tex",
                False,
                False,
            ),
            (
                None,
                "./test_files/note_with_image.md",
                "./test_files/note_with_image.tex",
                False,
                False,
            ),
        ],
        ids=[
            "simple case, one code block",
            "multiple_code_blocks",
            "colorful_headers",
            "latex_equation",
            "bullet_points",
            "linked_notes_1",
            "md_table",
            "quote_block",
            "front_matter",
            "hyperlinks",
            "complexed_note",
            "note_with_image",
        ],
    )
    def test_ObsiPdfGenerator(self, note, note_paths, path, colorfull_headers, toc):
        # Remove tex file and pdf file if they exist before generating new ones
        if os.path.exists(path):
            os.remove(path)
        if os.path.exists(path.replace(".tex", ".pdf")):
            os.remove(path.replace(".tex", ".pdf"))

        # Create the .tex file
        obsi = ObsiPdfGenerator(colorfull_headers, toc)
        obsi.add_note(note=note, note_paths=note_paths)
        logger.debug(obsi.document)
        obsi.save(path)

        # Genereate the .pdf file
        logger.debug("Generating the .pdf file")
        obsi.generate_pdf(path, clear=False, toc=toc)

        # Remove unwated files
        for file_ext in [".aux", ".log", ".toc", ".out", ".pyg"]:
            current_file = path.replace(".tex", file_ext)
            if os.path.exists(current_file):
                logger.debug(f"Removing {current_file}")
                os.remove(current_file)
        current_folder_files = os.listdir()
        for file_or_folder in current_folder_files:
            logger.debug(f"Removing {file_or_folder}")
            if "_minted-" in file_or_folder:
                shutil.rmtree(file_or_folder)

        # Check that path exists
        assert os.path.exists(path.replace(".tex", ".pdf"))
