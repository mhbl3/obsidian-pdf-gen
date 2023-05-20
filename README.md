[![ObsidianPDFGenCI](https://github.com/mhbl3/obsidian-pdf-gen/actions/workflows/python-app.yml/badge.svg)](https://github.com/mhbl3/obsidian-pdf-gen/actions/workflows/python-app.yml)
# obsidian_pdf_gen
 Python PDF generator of Obsidian notes
# Basic setup and pdf generation Pc/Mac/Linux
## Installation
### GitHub
```shell
git clone https://github.com/mhbl3/obsidian_pdf_gen.git
```
Open the terminal/command line and change directory to the recently cloned repo
```shell
cd "path/to/obsidian_pdf_gen"
```
Then, install the package
```shell
pip install .
```
### Pip
```shell
pip install obsidian_pdf_gen
```
## Changing to vault directory
This package must be ran from the root directory of the vault. There are two ways to achieve this: 
1. In a terminal/command window, change to the root directory of the Obsidian vault
```shell
cd "path/to/my/Obsidian/vault/root"
```
Note that the quotes are only necessary if there are spaces in the path. This would need to be performed every time one wants to generate a pdf if no default directory is set
2. The second and more permanent option is to set a default directory using the `--vault` argument 
```shell
obsi_pdf --vault "path/to/my/Obsidian/vault/root"
```
This way `obsi_pdf` will always run from the specified vault's directory, independent of the directory the user is in when `obsi_pdf` is ran.
Note that if you update `obsidian-pdf-gen` you would need to reset a default vault. 
## Generate a pdf from the markdown notes
```shell
obsi_pdf -n "mynote" --clear true
```
- `n` argument is used to specify to the file name (or the path. When the path is not specified the software will automatically file with the vault) corresponding to the markdown note. 
- `clear` is used to remove all auxilary files created during the pdf generation, including a `.tex` file.
# Basic Setup and pdf generation for iOS
Make sure to have the [a-shell](https://apps.apple.com/us/app/a-shell/id1473805438) app downloaded from the Appstore, it's **free**!
## Install the python package in a-shell
Using this [shortcut](https://www.icloud.com/shortcuts/6bca6376fa49422885d8972bb9ea4a46), you can install the package. There will be two options either installing through PIP or installing by downloading the release of this repo, and then PIP installing in the app
## Setting your default vault and select it.
On iOS you need to setup your default vault. You can use this [shortcut](https://www.icloud.com/shortcuts/4b22c1fc8afd47ccb1d088a3f951f9b9) to `pickFolder` a folder outside of the a-shell folder. Use this to navigate to your vault
## Generating a pdf
When in Obsidian use the share sheet to generate a pdf of the note that you're on by selecting **Generate Obsidian Note PDF**. This should be an option in your share sheet after downloading this [shortcuts](https://www.icloud.com/shortcuts/a28954ec37c34e778f6047912761983f)