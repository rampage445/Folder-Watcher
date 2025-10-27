import logging
from pathlib import Path
import os
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR,"activity.log")

def get_logger(name="FileSync"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(LOG_FILE)
        fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %I:%M %p")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger
