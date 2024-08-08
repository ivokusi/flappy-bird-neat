from pygame.transform import scale2x
from pygame.image import load
import os

ROOT_DIRECTORY = "game_assets"

def add_asset(asset_name):

    """
    Helper function to scale and load asset from root_directory (i.e. game_assets)
    """

    # Scale and load asset from root directory

    path = os.path.join(ROOT_DIRECTORY, asset_name)
    asset = scale2x(load(path))

    return asset