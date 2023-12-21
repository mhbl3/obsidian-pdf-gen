from setuptools import setup


setup(
    name="obsidian_pdf_gen",
    version="1.6.3",
    author="Marc-Henri Bleu-Laine",
    url="https://github.com/mhbl3/obsidian-pdf-gen",
    description="A python package to convert Obsidian Markdown files into stylish PDFs",
    packages=[
        "obsidian_pdf_gen",
        "obsidian_pdf_gen.generate_pdf",
        "obsidian_pdf_gen.config",
        "obsidian_pdf_gen.media_retriever",
    ],
    entry_points={
        "console_scripts": [
            "obsi_pdf = obsidian_pdf_gen.generate_pdf.md_notes_pdf:main"
        ]
    },
    zip_safe=True,
    include_package_data=True,
    install_requires=["pytest", "pyyaml"],
)
