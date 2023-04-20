from setuptools import setup


setup(
    name="obsidian_pdf_gen",
    version="1.6.1",
    author="Marc-Henri Bleu-Laine",
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
    # package_dir={"": "obsidian_pdf_gen"},
    install_requires=["pytest", "pyyaml"],
)
