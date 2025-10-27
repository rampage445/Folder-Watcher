from logs import get_logger
from folder_watcher import start_watcher
import os

logger = get_logger("Main")

WATCH_DIR = os.path.join(os.getcwd(), "MyFiles")
STATE_FILE = os.path.join(WATCH_DIR, "state.json")

def main():
    os.remove(STATE_FILE)
    logger.info("Starting File Sync Watcher...")
    start_watcher()

main()
