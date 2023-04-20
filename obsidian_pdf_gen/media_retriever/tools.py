import os
import yaml
import pathlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ObiPdfGen")
path_to_config = pathlib.Path(__file__).parent / "../config/note_configs.yaml"
with path_to_config.open("r") as f:
    CONFIG = yaml.safe_load(f)
ACCEPTED_MEDIA_TYPES = CONFIG["supported media"]


class MediaUnsupportedError(Exception):
    """Unsupported media type exception, supported ones are `.md`, `.png`, `.jpg`, and `csv`

    Args:
        Exception (object): Exception object.
    """

    def __init__(self):
        message = "Unsupported media type, supported ones are `.md`, `.png`, `.jpg`, and `csv`"
        super().__init__(message)


def get_media_path(media_name: str):
    """
    Get the path to the media folder of a note

    Args:
        media_name (str): Name of the media file
    """
    if not any(
        [media_name.endswith(media_type) for media_type in ACCEPTED_MEDIA_TYPES]
    ):
        raise MediaUnsupportedError()

    for root, dirs, files in os.walk("."):
        if media_name in files:
            logger.debug(f"Found {media_name} in {root}")
            return os.path.join(root, media_name)
    return None


def change_to_vault_directory():
    """Change the current working directory to the vault directory."""
    vault_abs_path = CONFIG["Obsidian Vault"]
    if vault_abs_path != "":
        logger.debug(f"Changing directory to {vault_abs_path}")
        os.chdir(vault_abs_path)
