from os import getenv, chdir
from os.path import dirname
from tempfile import gettempdir
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# switch to the project directory
PROJECT_PATH = dirname(__file__)
chdir(PROJECT_PATH)

# load environment variables
DEFAULT_MODEL_LANGUAGE = getenv("DEFAULT_MODEL_LANGUAGE")
DEFAULT_MODEL = getenv("DEFAULT_MODEL")
DEFAULT_LANGUAGE = getenv("DEFAULT_LANGUAGE")
DOWNLOAD_PATH = Path(getenv("DOWNLOAD_PATH"))
RECORDING_PATH = Path(getenv("RECORDING_PATH"))
TEMP_PATH = Path(gettempdir())
OUTPUT_PATH = Path(getenv("OUTPUT_PATH"))
YT_SAVE_AUDIO = True if getenv("OUTPUT_PATH") in \
    ["True", "true", "1"] else False
YT_USE_CACHE = True if getenv("YT_USE_CACHE") in \
    ["True", "true", "1"] else False
CACHE_FILE = "cache.tsv"
