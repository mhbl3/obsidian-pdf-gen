import os
import re
import yaml
import copy
import shutil
import logging
import pathlib
import platform
import argparse
import subprocess
import pkg_resources
from typing import Union, Tuple
from obsidian_pdf_gen.media_retriever.tools import (
    get_media_path,
    change_to_vault_directory,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ObiPdfGen")

path_to_config = pathlib.Path(__file__).parent / "../config/note_configs.yaml"
with path_to_config.open("r") as f:
    CONFIG = yaml.safe_load(f)


class ObsiPdfGenerator:
    """Generator of pdfs from Obsidian notes."""

    def __init__(
        self,
        colorfull_headers: bool = False,
        include_toc: bool = False,
        img_width: float = 1.5,
    ):
        """Initialization of the class responsible for creating the latex doc that will be used to create the pdf.

        Args:
            colorfull_headers (bool, optional): Whether or not to have colorful headers in the pdf. Defaults to False.
            include_toc (bool, optional): If `True` the Table of Content will be included in the pdf. Defaults to False.
            img_width (float, optional): Image width in inches. Defaults to 1.5.
        """
        font_style = CONFIG["font"].get("style", None)
        font_size = CONFIG["font"]["size"]
        inline_code_lang = CONFIG["inline code"]["default language"]
        hl_color = CONFIG.get("highlight color", "yellow")
        document_class = CONFIG["document class"].get("name")
        self.img_width = img_width
        force_document_class = CONFIG["document class"].get("force document class")
        toc_latex = "\\tableofcontents\n" if include_toc else ""

        if not force_document_class:
            if font_size in [10, 11, 12]:
                document_class = "article"
            else:
                # Enables more font sizes
                document_class = "extarticle"
        self.document = (
            "\\documentclass["
            + str(font_size)
            + "pt"
            + "]"
            + "{{"
            + document_class
            + "}}"
            + "\n"
        )
        self.document += """\\usepackage{{minted}}
\\usepackage{{enumitem}}
\\setlistdepth{{9}}

\\setlist[itemize,1]{{label=\\textbullet}}
\\setlist[itemize,2]{{label=\\textbullet}}
\\setlist[itemize,3]{{label=\\textbullet}}
\\setlist[itemize,4]{{label=\\textbullet}}
\\setlist[itemize,5]{{label=\\textbullet}}
\\setlist[itemize,6]{{label=\\textbullet}}
\\setlist[itemize,7]{{label=\\textbullet}}
\\setlist[itemize,8]{{label=\\textbullet}}
\\setlist[itemize,9]{{label=\\textbullet}}

\\renewlist{{itemize}}{{itemize}}{{9}}

\\usepackage{{graphicx}}

\\usepackage{{csquotes}}

\\usepackage{{hyperref}}

\\usepackage[T1]{{fontenc}}

\\usepackage[most]{{tcolorbox}}
\\definecolor{{block-gray}}{{gray}}{{0.95}}
\\newtcolorbox{{advtcolorbox}}{{
    %colback=block-gray,
    boxrule=0pt,
    boxsep=0pt,
    breakable,
    enhanced jigsaw,
    borderline west={{4pt}}{{0pt}}{{gray}},
}}

\\newtcbox{{\pill}}[1][blue]{{on line,
arc=7pt,colback=#1!10!white,colframe=#1!50!black,
before upper={{\\rule[-3pt]{{0pt}}{{10pt}}}},boxrule=1pt,
boxsep=0pt,left=6pt,right=6pt,top=2pt,bottom=2pt}}

\\usepackage{{amsmath}}
\\usepackage[dvipsnames]{{xcolor}} % to access the named colour LightGray
\\usepackage{{soul}}
\\usepackage{{sectsty}}
\\definecolor{{LightGray}}{{rgb}}{{0.9, 0.9, 0.9}}
\\definecolor{{inlinecodecolor}}{{rgb}}{{0, 0.3, 0.6}}
\\usepackage{{lmodern}}
\\makeatletter
\\renewcommand\\subparagraph{{%
\\@startsection{{subparagraph}}{{5}}{{0pt}}%
{{3.25ex \\@plus 1ex \\@minus .2ex}}{{-1em}}%
{{\\normalfont\\normalsize\\bfseries}}}}
\\makeatother
"""

        self.document += "\\sethlcolor{{" + hl_color + "}}" + "\n"
        if font_style:
            self.document += "\\usepackage{{" + font_style + "}}" + "\n"

        self.document += (
            "\\newrobustcmd*\\inlinecode[2][]{{"
            + "\\textcolor{{inlinecodecolor}}{{\\mintinline[#1]{{"
            + inline_code_lang
            + "}}{{#2}}}}}}\n"
        )

        if colorfull_headers:
            h1 = CONFIG["Header Colors"]["\\#"]
            h2 = CONFIG["Header Colors"]["\\##"]
            h3 = CONFIG["Header Colors"]["\\###"]
            h4 = CONFIG["Header Colors"]["\\####"]
            h5 = CONFIG["Header Colors"]["\\#####"]
            self.document += r"\sectionfont{{" + "\\color{{" + h1 + "}}" + "}}" + "\n"
            self.document += (
                r"\subsectionfont{{" + "\\color{{" + h2 + "}}" + "}}" + "\n"
            )
            self.document += (
                r"\subsubsectionfont{{" + "\\color{{" + h3 + "}}" + "}}" + "\n"
            )
            self.document += (
                "\\newcommand{{\\myparagraph}}[1]{{\\paragraph{{"
                + "\\textcolor{{"
                + h4
                + "}}"
                + "{{#1}}"
                + "}}\\mbox{{}}\\\\}}"
                + "\n"
            )
            self.document += (
                "\\newcommand{{\\mysubparagraph}}[1]{{\\subparagraph{{"
                + "\\textcolor{{"
                + h5
                + "}}"
                + "{{#1}}"
                + "}}\\mbox{{}}\\\\}}"
                + "\n"
            )

        self.document += "\\begin{{document}}\n" + toc_latex + "\n"
        self.document += """
{}
\\end{{document}}
"""

    def add_note(
        self,
        note: str = None,
        note_paths: Union[str, list] = None,
        use_chapters: bool = True,
        include_linked_notes: bool = True,
    ):
        """Main method to add notes to the pdf.

        Args:
            note (str, optional): The note to add passed as a string. Defaults to None.
            note_paths (Union[str, list], optional): The path to the note to add. Defaults to None.
            use_chapters (bool, optional): Whether to use chapters or not. All headings will converted to chapters in Latex.
                Defaults to True.
            include_linked_notes (bool, optional): Whether to include notes that are linked to the notes specified in the `note_paths`.
                Defaults to True.
        """
        tex = []
        # If a path is specified
        if not note and note_paths:
            if isinstance(note_paths, str):
                note_paths = [note_paths]
                self.note_tex = ""
            # For each notes specified
            while len(note_paths) > 0:
                note_path = note_paths.pop(0)
                # Add the .md to the file name is it is not there
                note_path = (
                    note_path if note_path.endswith(".md") else note_path + ".md"
                )
                note_title = self.extract_note_title(note_path)
                # Open the note file
                try:
                    with open(note_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                except FileNotFoundError:
                    logger.warning(
                        f"File '{note_path}' not found, trying to find it..."
                    )
                    # Let's try to find the file in current directory and subdirectories
                    note_path_retrieved = get_media_path(note_path)
                    if note_path_retrieved:
                        with open(note_path_retrieved, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                    else:
                        raise FileNotFoundError(
                            f"File '{note_path}' not found in current directory and subdirectories"
                        )

                if use_chapters:
                    # Add the note file name as the chapter name
                    latex_chapter = (
                        "\\chapter{" + note_title + "}\\label{ch:" + note_title + "}\n"
                    )
                    tex.append(latex_chapter)
                # Loop through every line
                lines_to_skip = []
                for ln, line in enumerate(lines):
                    if ln in lines_to_skip:
                        continue
                    # Apply different changes to line
                    (
                        line,
                        additional_lines_to_skip,
                        additional_notes,
                    ) = self._apply_transformation(line, ln, lines)
                    logger.debug(f"Current line index = {ln}, line : {line}")
                    # Update the lines to skip, if any
                    lines_to_skip += additional_lines_to_skip
                    logger.debug(f"lines_to_skip : {lines_to_skip}")
                    tex.append(line)
                    if include_linked_notes:
                        if len(additional_notes) > 0:
                            for graphic in additional_notes:
                                if ".png" in graphic:
                                    line = self._include_graphic(
                                        graphic, self.img_width
                                    )
                                    # pop the last line to remve "[[my image.png]]" being present in doc
                                    tex.pop(-1)
                                    tex.append(line)
                        # Add new notes to go through
                        additional_md_notes = [
                            a_note for a_note in additional_notes if ".md" in a_note
                        ]
                        note_paths.extend(additional_md_notes)

            # Combine the lines
            note = "\n".join(tex)
            self.note_tex += f"""{note}"""

        else:
            # Assume the title is the first line
            note_title = note.split("\n")[0]

            self.note_tex = f"""
\\section{{{note_title}}}
{note}
"""

    @staticmethod
    def replace_text_style(line: str) -> str:
        """Replace a bunch of markdown syntax to latex.

        Args:
            line (str): Current line of the note.

        Returns:
            str: Trsnsformed line.
        """
        # check if math equation is present
        if ((line.count("$") % 1 == 0) and (line.count("$") > 1)) or (
            (line.count("$$") % 1 == 0) and ((line.count("$$") > 1))
        ):
            original_content = re.findall(r"\$\$(.*?)\$\$", line) + re.findall(
                r"\$(.*?)\$", line
            )

        # Find italic words
        all_italics = re.findall(r"_(.*?)_", line)
        for word in all_italics:
            line = line.replace(f"_{word}_", f"\\textit{{{word}}}")

        # Find bold words
        all_bolds = re.findall(r"\*\*(.*?)\*\*", line)
        for word in all_bolds:
            line = line.replace(f"**{word}**", f"\\textbf{{{word}}}")

        # Find highlighted words
        all_hls = re.findall(r"==(.*?)==", line)
        for word in all_hls:
            line = line.replace(f"=={word}==", f"\\hl{{{word}}}")

        # Replace hyperlinks
        if (
            "[" in line
            and "]" in line
            and "(" in line
            and ")" in line
            and ("http" in line or "www" in line)
        ):
            links = re.findall(r"\]\((.*?)\)", line)
            text_for_links = re.findall(r"\[(.*?)\]\(", line)
            for txt, link in zip(text_for_links, links):
                line = line.replace(f"[{txt}]({link})", f"\\href{{{link}}}{{{txt}}}")

        # Find all inline code
        all_inline = re.findall(r"`(.+?)`", line)
        for word in all_inline:
            if word != "`":
                line = line.replace(
                    f"`{word}`",
                    "\\inlinecode[bgcolor=LightGray, fontsize=\\scriptsize]{"
                    + word
                    + "}",
                )

        # Find and replace tags
        for word in line.split():
            if word.startswith("#") and len(word) > 1 and word.count("#") == 1:
                line = line.replace(word, f"\\pill{{{word}}}")

        # Reverse these fixes if they are in a math block
        if ((line.count("$") % 1 == 0) and (line.count("$") > 1)) or (
            (line.count("$$") % 1 == 0) and ((line.count("$$") > 1))
        ):
            contents_of_math = re.findall(r"\$\$(.*?)\$\$", line) + re.findall(
                r"\$(.*?)\$", line
            )
            for e, content in enumerate(contents_of_math):
                line = line.replace(content, original_content[e])

        return line

    @staticmethod
    def handle_special_characters(line: str) -> str:
        """Handle special characters, and replaces markown with latex syntax.

        Args:
            line (str): Current line of the note.

        Returns:
            str: Transformed line.
        """
        replace_underscore = True
        # check if math equation is present
        if ((line.count("$") % 1 == 0) and (line.count("$") > 1)) or (
            (line.count("$$") % 1 == 0) and ((line.count("$$") > 1))
        ):
            original_content = re.findall(r"\$\$(.*?)\$\$", line) + re.findall(
                r"\$(.*?)\$", line
            )
        # Check if inline code is present
        if (line.count("`") % 1 == 0) and (line.count("`") > 1):
            original_content_inline = re.findall(r"`(.*?)`", line)

        line = line.replace("&", "\\&")
        line = line.replace("%", "\\%")
        # line = line.replace("$", "\\$")
        line = line.replace(">", "\\>")
        line = line.replace("<", "\\<")
        line = line.replace("#", "\\#")
        line = line.replace("---", "\\noindent\\rule[0.5ex]{\\linewidth}{1pt}")
        line = line.replace("***", "\\noindent\\rule[0.5ex]{\\linewidth}{1pt}")
        # Reverse these fixes if they are in a math block
        if ((line.count("$") % 1 == 0) and (line.count("$") > 1)) or (
            (line.count("$$") % 1 == 0) and ((line.count("$$") > 1))
        ):
            contents_of_math = re.findall(r"\$\$(.*?)\$\$", line) + re.findall(
                r"\$(.*?)\$", line
            )
            for e, content in enumerate(contents_of_math):
                line = line.replace(content, original_content[e])
            replace_underscore = False
        if (line.count("`") % 1 == 0) and (line.count("`") > 1):
            content_of_inline = re.findall(r"`(.*?)`", line)
            for e, content in enumerate(content_of_inline):
                line = line.replace(content, original_content_inline[e])
            replace_underscore = False
        if replace_underscore:
            line = line.replace("_", "\\_")
        # line = line.replace("\\", "\\\\")
        # line = line.replace("{", "\\{")
        # line = line.replace("}", "\\}")
        return line

    # Find and add linked notes

    def _apply_transformation(
        self, line: str, current_line_idx: int, note_content: list
    ) -> Tuple[str, list, list]:
        """Applies a set of transformations to convert from markdown to latex.

        Args:
            line (str): The current line of the note.
            current_line_idx (int): The current line index.
            note_content (list): List containing all the lines of the note.

        Returns:
            Tuple[str, list, list]: The transformed line, the lines to skip and the names of additional notes to add.
        """
        lines_to_skip = []
        # Check if we reached an obsidian pluggin settings
        if line.lstrip().startswith("%%") or line.lstrip().startswith(">%%"):
            return "", [i for i in range(current_line_idx, len(note_content))], []
        line, lines_to_skip, is_table = self.convert_to_latex_table(
            line, current_line_idx, note_content
        )
        # Check for front matter and handle it
        if line.lstrip().startswith("---") and current_line_idx == 0:
            lines_to_skip.append(current_line_idx)
            for ln, next_line in enumerate(note_content[current_line_idx + 1 :], 1):
                lines_to_skip.append(ln)
                if next_line.lstrip().startswith("---"):
                    break
            line = ""
            return line, lines_to_skip, []
        additional_notes = self.check_for_linked_notes(line)
        if len(additional_notes) > 0:
            links = re.findall(r"\[\[(.*?)\]\]", line)
            for link in links:
                logger.debug(f"link: {link}")
                # In case there are multiple separators, but this does happen really when linking notes.
                # It does happen for pictures, to the best of my knownledge.
                alias_idx = -1 if link.count("|") <= 1 else 1
                split_link_file = self.extract_note_title(link.split("|")[0])
                split_link_alias = link.split("|")[alias_idx].lstrip()
                split_link = f"\\hyperref[ch:{split_link_file}]{{{split_link_alias}}}"
                line = line.replace(f"[[{link}]]", split_link)
                logger.debug(f"line: {line}")
                note_content[current_line_idx] = line

        logger.debug(f"is_table: {is_table}")
        if is_table:
            return line, lines_to_skip, additional_notes
        line, lines_to_skip = self.convert_callouts_block_text(
            current_line_idx, note_content
        )
        if len(lines_to_skip) > 0:
            return line, lines_to_skip, additional_notes

        return self.apply_conversion_routine(
            line, current_line_idx, note_content, additional_notes
        )

    def convert_callouts_block_text(
        self, current_line_idx: int, note_content: list
    ) -> Tuple[str, list]:
        """Converts callouts and block text syntax to latex.

        Args:
            current_line_idx (int): Current line number.
            note_content (list): Lidt of lines in the note.

        Returns:
            Tuple[str, list]: Return the transformed line and a list of lines to skip.
        """
        counter = 0
        lines_to_skip = []
        line = note_content[current_line_idx]

        # Check if this is the start of a block quote
        if line.lstrip().startswith(">"):
            # Count the number of block quotes
            counter += 1
            for next_line in note_content[current_line_idx + 1 :]:
                if next_line.lstrip().startswith(">"):
                    counter += 1
                else:
                    break
            lines_to_skip = [
                i for i in range(current_line_idx, current_line_idx + counter)
            ]
            logger.debug(
                f"lines_to_skip in convert_callouts_block_text: {lines_to_skip}"
            )
            # Remove text in between [! and ] and replace it with a empty text
            txt_to_replace = re.findall(r"\[!(.*?)\]", line)
            if len(txt_to_replace) > 0:
                txt_to_replace = txt_to_replace[0]
                line = self.handle_special_characters(
                    self.replace_text_style(
                        line.replace(f"[!{txt_to_replace}]", "").lstrip(">").lstrip()
                    )
                )
                line = "\\begin{tcolorbox}" + f"[title={line}]\n"
            else:
                line = "\\begin{advtcolorbox}\n" + self.handle_special_characters(
                    self.replace_text_style(line.lstrip(">").lstrip() + "\n")
                )

            for idx_blocks in lines_to_skip[1:]:
                line += self.handle_special_characters(
                    self.replace_text_style(
                        note_content[idx_blocks].lstrip(">").lstrip() + "\n"
                    )
                )

            if len(txt_to_replace) > 0:
                line += "\\end{tcolorbox}\n"
            else:
                line += "\\end{advtcolorbox}\n"
        logger.debug(f"line in convert_callouts_block_text: {line}")
        return line, lines_to_skip

    def apply_conversion_routine(
        self,
        line: str,
        current_line_idx: int,
        note_content: list,
        additional_notes: list,
    ) -> Tuple[str, list, list]:
        """Group apply multiple functions to change the markdown syntax to latex.

        Args:
            line (str): Line to transform.
            current_line_idx (int): The current line number.
            note_content (list): List of lines in the note.
            additional_notes (list): List of the name of additional notes to add.

        Returns:
            Tuple[str, list, list]: Return the transformed line, a list of lines to skip and a list of additional notes.
        """
        line = self.replace_text_style(line)
        line, is_section = self.replace_md_headers(line)
        line, lines_to_skip, is_math = self.keep_math(
            line, current_line_idx, note_content
        )
        line, additional_lines_to_skip = self.find_replace_footnotes(
            line, note_content, current_line_idx
        )
        lines_to_skip += additional_lines_to_skip
        logger.debug(f"is_math: {is_math}")
        if is_math:
            return line, lines_to_skip, additional_notes

        line = self.handle_special_characters(line)
        logger.debug(f"is_section: {is_section}")
        if is_section:
            return line, lines_to_skip, additional_notes
        line, additional_lines_to_skip, is_codeblock = self.replace_md_code_block(
            line, current_line_idx, note_content
        )
        lines_to_skip += additional_lines_to_skip
        logger.debug(f"is_codeblock: {is_codeblock}")
        if is_codeblock:
            return line, lines_to_skip, additional_notes
        line, additional_lines_to_skip, is_bullet_point = self.replace_md_bullet_point(
            line, current_line_idx, note_content, CONFIG["indent"]
        )
        lines_to_skip += additional_lines_to_skip
        if is_bullet_point:
            return line, lines_to_skip, additional_notes

        # Remove leading spaces
        line = line.lstrip()
        return line, lines_to_skip, additional_notes

    @staticmethod
    def extract_note_title(note_path: str, cap_words: bool = True) -> str:
        """Extract the note title from the path.

        Args:
            note_path (str): The path to the note or just the note name.
            cap_words (bool, optional): If `True` each word of the title will have its first letter capitalized. Defaults to True.

        Returns:
            str: The note title.
        """
        # Convert to fwd slashes
        note_path = str(pathlib.Path(note_path).as_posix())
        # Get the file name
        note_title = note_path.split("/")[-1].replace("_", " ")
        if note_title.endswith(".txt"):
            note_title = note_title.replace(".txt", "")
        elif note_title.endswith(".md"):
            note_title = note_title.replace(".md", "")
        return note_title.title() if cap_words else note_title

    @staticmethod
    def replace_md_headers(line: str) -> Tuple[str, bool]:
        """Replace markdown header with latex section/subsection/subsubsection.

        Args:
            line (str): The line to transform.

        Returns:
            Tuple[str, bool]: Return the transformed line and a boolean indicating if it's a section/subsection/subsubsection or none of them.
        """
        is_section = False
        lstrip_line_space = line.lstrip()
        lstrip_line_hashtag = line.lstrip("#")
        if lstrip_line_space.startswith("#"):
            count_lead_hashtags = len(line) - len(lstrip_line_hashtag)
            # Empty str means that it's not an hastag
            if lstrip_line_hashtag[0] == " ":
                if count_lead_hashtags == 5:
                    line = (
                        f"\\mysubparagraph{{{lstrip_line_space.replace('##### ', '')}}}".replace(
                            "\n", ""
                        )
                        + "\n"
                    )
                    is_section = True
                elif count_lead_hashtags == 4:
                    line = (
                        f"\\myparagraph{{{lstrip_line_space.replace('#### ', '')}}}".replace(
                            "\n", ""
                        )
                        + "\n"
                    )
                    is_section = True
                elif count_lead_hashtags == 3:
                    line = (
                        f"\\subsubsection{{{lstrip_line_space.replace('### ', '')}}}".replace(
                            "\n", ""
                        )
                        + "\n"
                    )
                    is_section = True
                elif count_lead_hashtags == 2:
                    line = (
                        f"\\subsection{{{lstrip_line_space.replace('## ', '')}}}".replace(
                            "\n", ""
                        )
                        + "\n"
                    )
                    is_section = True
                elif count_lead_hashtags == 1:
                    line = (
                        f"\\section{{{lstrip_line_space.replace('# ', '')}}}".replace(
                            "\n", ""
                        )
                        + "\n"
                    )
                    is_section = True
        return line, is_section

    def keep_math(
        self, line: str, current_line_idx: int, lines: list
    ) -> Tuple[str, list, bool]:
        """Keep math formulas in latex syntax.

        Args:
            line (str): Current line.
            current_line_idx (int): The current line number.
            lines (list): List of lines in the note.

        Returns:
            Tuple[str, list, bool]: Return the transformed line, a list of lines to skip
                and a boolean indicating if it's a math formula or not.
        """
        lsline = line.lstrip()
        lines_to_skip = []
        # Check whether we have the start of a math formula
        if (lsline.startswith("$$")) and (lsline.count("$$") == 1):
            math_start_line = copy.copy(current_line_idx)
            for ln, line_after_line in enumerate(
                lines[current_line_idx + 1 :], current_line_idx + 1
            ):
                lines_to_skip.append(ln)
                logger.debug(f"line_after_line: {line_after_line}")
                lsline_after_line = line_after_line.lstrip()
                if "$$" in lsline_after_line:
                    line = "".join(lines[math_start_line : ln + 1])
                    return line, lines_to_skip, True
        else:
            return line, lines_to_skip, False

    def replace_md_code_block(
        self, line: str, current_line_idx: int, lines: list
    ) -> Tuple[str, list, bool]:
        """Replace markdown code block with latex code block.

        Args:
            line (str): The current line.
            current_line_idx (int): The current line number.
            lines (list): List of lines in the note.

        Returns:
            Tuple[str, list, bool]: Return the transformed line, a list of lines to skip,
                boolean indicating if it's a code block or not.
        """
        ticks_counter = 0
        lsline = line.lstrip()
        lines_to_skip = []
        # Check whether we have the start of a code block
        if lsline.startswith("```"):
            language = lsline.replace("```", "").replace(" ", "").replace("\n", "")
            ticks_counter += 1
            logger.debug(f"ticks_counter: {ticks_counter}")
            code_start_line = current_line_idx + 1
            # Find the next ticks and the end of the code block
            for ln, line_after_line in enumerate(
                lines[current_line_idx + 1 :], current_line_idx + 1
            ):
                logger.debug(f"line_after_line: {line_after_line}")
                lsline_after_line = line_after_line.lstrip()
                if lsline_after_line.startswith("```"):
                    # Increase tick counter since it was found
                    ticks_counter += 1
                    logger.debug(f"ticks_counter-after increasing: {ticks_counter}")
                if ticks_counter == 2:
                    # This has to be the end of the code block
                    logger.debug(f"line (before join): {lines[code_start_line: ln]}")
                    line = "".join(lines[code_start_line:ln])
                    # Remove last blank line in line
                    line = line[: line.rfind("\n")]
                    # These are the lines we do not want to add to the note anymore
                    logger.debug(f"line (after join): {line}")
                    logger.debug(f"language: {language}.")
                    lines_to_skip += [i for i in range(code_start_line, ln + 1)]
                    line = self.convert_to_latex_code(line, language)
                    return line, lines_to_skip, True
        else:
            return line, lines_to_skip, False

    def replace_md_bullet_point(
        self, line: str, current_line_idx: int, lines: list, indent: int = 4
    ) -> Tuple[str, list, bool]:
        """Replaces markdown bullet points with latex bullet points.

        Args:
            line (str): The current line.
            current_line_idx (int): The current line number.
            lines (list): List of lines in the note.
            indent (int, optional): The number of spaces that correspond to an indent. Defaults to 4.

        Returns:
            Tuple[str, list, bool]: Return the transformed line, a list of lines to skip, and boolean indicating if it's a bullet point or not.
        """
        logger.debug(f"current_line_idx = {current_line_idx}")
        lsline = line.lstrip()
        pre_space_diff = len(line) - len(lsline)
        space_diff = None
        lines_to_skip = []
        # Check whether we have the start of a code block
        if lsline.startswith("-"):
            line = "\\begin{itemize}\n" + "\\item " + line.lstrip("- ")
            for ln, line_after_line in enumerate(
                lines[current_line_idx + 1 :], current_line_idx + 1
            ):
                logger.debug(f"ln = {ln}")
                line_after_line = self.replace_text_style(line_after_line)
                if line_after_line.lstrip().startswith("-"):
                    ls_line_after_line = line_after_line.lstrip()
                    space_diff = len(line_after_line) - len(ls_line_after_line)
                    if line_after_line.startswith("\t"):
                        space_diff = (
                            len(line_after_line) - len(line_after_line.lstrip("\t"))
                        ) * indent
                        line_after_line = line_after_line.lstrip("\t")
                    if space_diff == pre_space_diff:
                        line += "\\item " + line_after_line.lstrip("- ") + "\n"
                    elif space_diff > pre_space_diff:
                        line += (
                            "\\begin{itemize}\n"
                            + "\\item "
                            + line_after_line.lstrip("- ")
                            + "\n"
                        )
                    elif space_diff < pre_space_diff:
                        for _ in range((pre_space_diff - space_diff) // indent):
                            line += "\\end{itemize}\n"
                        line += "\\item " + line_after_line.lstrip("- ") + "\n"
                    pre_space_diff = space_diff
                    lines_to_skip.append(ln)
                    # Handle cases where the last line is a bullet point
                    if ln == len(lines) - 1:
                        line += "\\end{itemize}\n"
                        for _ in range(space_diff // indent):
                            line += "\\end{itemize}\n"
                        return line, lines_to_skip, True
                else:
                    line += "\\end{itemize}\n"
                    current_space_diff = space_diff if space_diff else pre_space_diff
                    for _ in range(current_space_diff // indent):
                        line += "\\end{itemize}\n"
                    return line, lines_to_skip, True
        else:
            # Skip the line
            return line, lines_to_skip, False

    @staticmethod
    def convert_to_latex_table(
        line: str, current_line_idx: int, lines: list
    ) -> Tuple[str, list, bool]:
        """Convert a markdown table to a latex table

        Args:
            line (str): The current line.
            current_line_idx (int): The current line number.
            lines (list): List of lines in the note.

        Returns:
            Tuple[str, list, bool]: Return the transformed line, a list of lines to skip, and boolean indicating if it's a table or not.
        """
        lines_to_skip = []
        if line.startswith("|"):
            # This is a table
            # Get the number of columns
            num_cols = line.count("|") - 1
            # Get the number of rows
            num_rows = 1
            for line_after_line in lines[current_line_idx:]:
                if line_after_line.startswith("|"):
                    num_rows += 1
                else:
                    break
            lines_to_skip = [
                i for i in range(current_line_idx + 1, current_line_idx + num_rows - 1)
            ]
            logger.debug(f"lines_to_skip: {lines_to_skip}")

            # Create the latex table
            latex_table = "\\begin{tabular}{|"
            for _ in range(num_cols):
                latex_table += "c|"
            latex_table += "}\n"
            latex_table += "\\hline\n"
            for row in range(current_line_idx, current_line_idx + num_rows - 1):
                line_splitted = lines[row].split("|")
                bool_md_separation = all(
                    [True if "---" in i else False for i in line_splitted[1:-1]]
                )
                if bool_md_separation:
                    continue
                for col in range(num_cols + 1):
                    logger.debug(f"line={lines[row]}")
                    latex_table += line_splitted[col].strip()
                    if col not in [0, num_cols]:
                        latex_table += " & "

                latex_table += "\\\\ \\hline\n"
            latex_table += "\\end{tabular}\n"
            return latex_table, lines_to_skip, True
        else:
            return line, lines_to_skip, False

    @staticmethod
    def convert_to_latex_code(line: str, language: str) -> str:
        """Convert a markdown code block to a latex code block

        Args:
            line (str): The current line.
            language (str): The language of the code block.

        Returns:
            str: Return the transformed line.
        """
        python3 = "true" if language.lower() == "python" else "false"
        if (language != "") and (language.lower() != "plaintext"):
            label = CONFIG["code"]["label"]
            if label:
                label = language
            else:
                label = "none"
            line = f"""
\\begin{{minted}}[
frame=lines,
framesep=2mm,
label={label},
framerule={CONFIG["code"]["frame rule"]},
python3={python3},
baselinestretch=1.2,
breaklines=true,
bgcolor=LightGray,
fontsize=\\footnotesize,
fontfamily={CONFIG["code"]["font family"]},
linenos
]{{{language}}}
{line}
\\end{{minted}}
            """
        else:
            line = f"""
\\begin{{minted}}[
frame=lines,
framesep=2mm,
baselinestretch=1.2,
framerule={CONFIG["code"]["frame rule"]},
fontfamily={CONFIG["code"]["font family"]},
breaklines=true,
bgcolor=LightGray,
fontsize=\\footnotesize,
linenos
]{{text}}
{line}
\\end{{minted}}
            """
        return line

    @staticmethod
    def replace_md_inline_code(txt: str) -> str:
        """Replace inline code with latex code

        Args:
            txt (str): The text to replace.

        Returns:
            str: Return the transformed text.
        """
        inline_code_lang = CONFIG["inline code"]["default language"]
        return "\\mintinline{{" + inline_code_lang + "}}{{" + txt + "}}"

    def save(self, path: str = "./notes.tex"):
        """Create the notes.tex file.

        Args:
            path (str, optional): The name (or path) of the latex file to create. Defaults to "./notes.tex".
        """
        # Insert notes
        self.document = self.document.format(self.note_tex)
        logger.debug(self.document)
        # Save file
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.document)

    @staticmethod
    def find_replace_footnotes(
        line: str, lines: list, current_line_idx: int
    ) -> Tuple[str, list]:
        """Find all footnotes in the text and return the text without the footnotes and the list of footnotes.

        Args:
            line (str): Line to search for footnotes.
            lines (list): List containing line to search for footnotes
            current_line_idx (int): Index of the current line in the list of lines.

        Returns:
            Tuple[str, list]: Text with replaced footnotes, and list of lines to skip.
        """
        footnotes = re.findall(r"\[\^(\d+)\]", line)
        lines_to_skip = []
        for footnote in footnotes:
            foot_note_in_line = f"[^{footnote}]"
            logger.debug(f"foot_note_in_line: {foot_note_in_line}")
            # Search through the lines after the current line for the footnote definition
            # Manage when the next line is the last line
            length_lines = (
                len(lines) if current_line_idx + 1 < len(lines) else len(lines) + 1
            )
            for line_idx in range(current_line_idx + 1, length_lines):
                if (length_lines > len(lines)) and (line_idx >= len(lines)):
                    continue
                check_text = f"{foot_note_in_line}:"
                if check_text in lines[line_idx]:
                    # Extract the footnote definition
                    footnote_definition = (
                        lines[line_idx].lstrip(f"{check_text}").lstrip()
                    )
                    lines_to_skip.append(line_idx)
                    line = line.replace(
                        foot_note_in_line,
                        f"\\footnote[{footnote}]{{{footnote_definition}}}",
                    )
                    break
        return line, lines_to_skip

    @staticmethod
    def generate_pdf(
        path: str = "./notes.tex",
        clear: bool = False,
        toc: bool = False,
        quiet: bool = True,
        use_same_directory: bool = True,
    ):
        """Generate the pdf file using `pdflatex`.

        Args:
            path (str, optional): Path or name of the latex file that will be transformed to a pdf. Defaults to "./notes.tex".
            clear (bool, optional): If `True`, folders and files created by `pdflatex` will be automatically deleted. Defaults to False.
            toc (bool, optional): If `True`, the Table of Content will be included in the pdf. Defaults to False.
            quiet (bool, optional): If `True`, `pdflatex` will not print in the console (this works only on some versions of Latex). Defaults to True.
            use_same_directory (bool, optional): If `True`, the pdf is generated in the same directory as the latex file.
                Otherwise, it is generated in the current directory from which the code was ran. Defaults to True.
        """
        parent_dir = str(pathlib.Path(path).parent)
        file_name = str(pathlib.Path(path).name)
        # Convert paths to forward slashes
        path = str(pathlib.Path(path).as_posix())
        # Generate pdf
        logger.debug(f"Generating pdf: {path}")
        if quiet:
            cmd_line = [
                "pdflatex",
                "-quiet",
                "-interaction",
                "nonstopmode",
                "-shell-escape",
                path,
            ]
        else:
            cmd_line = [
                "pdflatex",
                "-interaction",
                "nonstopmode",
                "-shell-escape",
                path,
            ]
        subprocess.run(cmd_line)
        # A Second pass is necessary to generate the table of contents https://tex.stackexchange.com/questions/301103/empty-table-of-contents
        if toc:
            subprocess.run(cmd_line)
        if clear:
            logger.debug(f"Removing {file_name}")
            try:
                os.remove(path)
            except FileNotFoundError:
                logger.debug(f"File {file_name} not found")

            for file_type in [".aux", ".log", ".toc", ".out", ".pyg"]:
                logger.debug(f'Removing {file_name.replace(".tex", file_type)}')
                try:
                    os.remove(file_name.replace(".tex", file_type))
                except FileNotFoundError:
                    logger.debug(f"File {file_type} not found when removing")
        if use_same_directory:
            for file_type in [".pdf", ".tex", ".aux", ".log", ".toc", ".out", ".pyg"]:
                logger.debug(
                    f"Moving {file_name.replace('.tex', file_type)} to {parent_dir}"
                )
                # Move file to parent directory
                try:
                    shutil.move(
                        file_name.replace(".tex", file_type),
                        path.replace(".tex", file_type),
                    )
                except FileNotFoundError:
                    logger.debug(
                        f"File {file_type} not found when moving to {parent_dir}"
                    )

        current_folder_files = os.listdir()
        for file_or_folder in current_folder_files:
            if "_minted-" in file_or_folder:
                logger.debug(f"Removing {file_or_folder}")
                shutil.rmtree(file_or_folder)

    @staticmethod
    def check_for_linked_notes(line: str) -> str:
        """Checks whether there are any linked notes in the line. If so, it will
        find the path to the new note. If not, it will return the original line.

        Args:
            line (str): The line to check.

        Returns:
            str: Saved paths for linked notes.
        """
        # Find all the links in the line
        links = re.findall(r"\[\[(.*?)\]\]", line)
        saved_paths = []
        accepted_media_types = CONFIG["supported media"]
        for link in links:
            # Make sure to keep text before any |
            link = link.split("|")[0]
            for media_type in accepted_media_types:
                if any(
                    [
                        True if accepted_type in link else False
                        for accepted_type in accepted_media_types
                    ]
                ):
                    link_file = link
                else:
                    link_file = link + media_type
                actual_path = get_media_path(link_file)
                logger.debug(f"actual_path: {actual_path}")
                if actual_path is not None:
                    saved_paths.append(actual_path)
                    return saved_paths
        return saved_paths

    @staticmethod
    def _include_graphic(file_path: str, img_width: float) -> str:
        """Includes a graphic into latex document.

        Args:
            file_path (str): String corresponding to the path of the file.
            img_width (float, optional): Image width in inches.

        Returns:
            str: Returned string with latex code.
        """
        # Convert backward slashes to forward ones
        file_path = str(pathlib.Path(file_path).as_posix())
        file_path = f'"{file_path}"'
        line = (
            "\\begin{figure}[H]\\centering\n\t\\includegraphics"
            + f"[width={img_width}"
            + "\\linewidth]{"
            + file_path
            + "}\n"
        )
        line += "\\end{figure}"

        return line


def _return_bool_value(value: str) -> bool:
    """Utility functions used to return a boolean value from a string.

    Args:
        value (str): String that will be converted to a boolean.

    Returns:
        bool: Boolean value.
    """
    logger.debug(f"Value: {value} (type: {type(value)}")
    if isinstance(value, str):
        return True if value.lower() == "true" else False
    else:
        return value


def main():
    # Get the inputs
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--note", type=str, default=None, help="String to convert (depecrated)"
    )
    parser.add_argument(
        "--note_paths",
        type=str,
        default=None,
        help="Path (or name of note) to notes to convert",
    )
    parser.add_argument(
        "-n", type=str, default=None, help="Note (or path to note) to convert"
    )
    parser.add_argument(
        "--ch", type=str, default="False", help="Create colorful headings"
    )
    parser.add_argument("--output", type=str, default=None, help="Output file name")
    parser.add_argument(
        "--clear",
        type=str,
        default="False",
        help="Clear the temporary files after generation",
    )
    parser.add_argument(
        "--quiet",
        type=str,
        default="True",
        help="Run pdflatex in quiet mode (does not work on all OS)",
    )
    parser.add_argument(
        "--toc", type=str, default="False", help="Include table of contents"
    )
    parser.add_argument(
        "--use_chapters", type=str, default="True", help="Use chapters in the pdf"
    )
    parser.add_argument(
        "--include_linked_notes", type=str, default=None, help="Include linked notes"
    )
    parser.add_argument("--iln", type=str, default="True", help="Include linked notes")
    parser.add_argument(
        "-o", type=str, default="False", help="Open the pdf file after generation"
    )
    # Params for setting up config file vault
    parser.add_argument(
        "--vault",
        type=str,
        default=None,
        help="Set the default vault of the config file",
    )
    parser.add_argument(
        "--reset-vault",
        default=False,
        action="store_true",
        help="Reset the default vault of the config file",
    )
    # Get the default image width
    parser.add_argument(
        "--img-width",
        default=1,
        type=float,
        help="Default width for images embedded in the pdf (in inches)",
    )
    # For version of package
    parser.add_argument(
        "--version",
        default=False,
        action="store_true",
        help="Show installed version of the obsidian_pdf_gen package",
    )

    args = parser.parse_args()

    ch = _return_bool_value(args.ch)
    clear = _return_bool_value(args.clear)
    toc = _return_bool_value(args.toc)
    use_chapters = _return_bool_value(args.use_chapters)
    quiet = _return_bool_value(args.quiet)
    include_linked_notes = (
        _return_bool_value(args.include_linked_notes)
        if args.include_linked_notes
        else _return_bool_value(args.iln)
    )
    img_width = args.img_width
    if isinstance(img_width, str):
        img_width = float(img_width)

    if args.version:
        print(
            f"Obsidian PDF Generator version: {pkg_resources.get_distribution('obsidian_pdf_gen').version}"
        )

    note_path = args.note_paths if args.note_paths else args.n
    open_pdf = _return_bool_value(args.o)

    # If there is a note path, then we are using the command line to generate a pdf
    if note_path:
        tex = ObsiPdfGenerator(ch, toc, img_width)
        # If specified, change to vault directory
        change_to_vault_directory()
        tex.add_note(args.note, note_path, use_chapters, include_linked_notes)
        try:
            # fix output path if there is an issue
            output_path = args.output
            if output_path is None:
                # Get original note path
                parent_dir = pathlib.Path(note_path).parent
                # Modify the name
                output_path = str(parent_dir / pathlib.Path(note_path).name)
            pathlib_path = pathlib.Path(output_path)
            if pathlib_path.suffix != ".tex":
                if pathlib_path.suffix == "":
                    output_path += ".tex"
                else:
                    output_path = output_path.replace(pathlib_path.suffix, ".tex")
            tex.save(output_path)
        except UnicodeEncodeError as e:
            logger.error(e)
            # For debuging
            logger.error(tex.note_tex)
            with open("tmp_debug.txt", "w", encoding="utf-8") as f:
                f.write(tex.note_tex)
        else:
            tex.generate_pdf(output_path, clear, toc, quiet)

            # open pdf if True
            if open_pdf:
                # Check the OS
                current_platform = platform.system()
                if current_platform.lower() == "windows":
                    subprocess.run(
                        ["explorer.exe", output_path.replace(".tex", ".pdf")]
                    )
                else:
                    subprocess.run(["open", output_path.replace(".tex", ".pdf")])
    else:
        # Case where setup the config file
        if args.vault is not None:
            logger.info(
                f"Setting up the default Obsidian vault location to '{args.vault}'!"
            )
            # Modify config/note_configs.yaml to include path to vault
            CONFIG["Obsidian Vault"] = args.vault
        if args.reset_vault:
            # Reset config/note_configs.yaml to default
            CONFIG["Obsidian Vault"] = ""
        with open(path_to_config, "w") as f:
            yaml.safe_dump(CONFIG, f)


if __name__ == "__main__":
    main()
