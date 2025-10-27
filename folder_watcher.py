import os
import time
import json
import hashlib
from datetime import datetime
from threading import Thread
from logs import get_logger
from google_drive import create_nested_folders, upload_file_to_drive, rename_file_on_drive, delete_file_from_drive

logger = get_logger("FolderWatcher")

WATCH_DIR = os.path.join(os.getcwd(), "MyFiles")
STATE_FILE = os.path.join(WATCH_DIR, "state.json")


def sha256sum(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


def load_state():
    if not os.path.exists(WATCH_DIR):
        os.makedirs(WATCH_DIR)
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as f:
            json.dump({"files": {}, "is_running": False}, f)
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def is_file_ready(file_path):
    try:
        mtime = os.path.getmtime(file_path)
        return (time.time() - mtime) >= 30 # Work with files which have more than 30 seconds of last modified time
    except Exception:
        return False


def organize_file(file_path):
    date_folder = datetime.now().strftime("%Y-%m-%d")
    ext = os.path.splitext(file_path)[1][1:].lower() or "unknown"
    target_dir = os.path.join(WATCH_DIR, date_folder, ext)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, os.path.basename(file_path))
    if file_path != target_path:
        os.rename(file_path, target_path)
    return target_path


def scan_and_sync(drive_parent):
    state = load_state()
    logger.info("Starting folder_watcher scan loop...")
    while state.get("is_running"):
        current_files = {}
        for root, _, files in os.walk(WATCH_DIR):
            for file in files:
                if file == "state.json":
                    continue
                path = os.path.join(root, file)
                if is_file_ready(path):
                    current_files[path] = sha256sum(path)
                else:
                    logger.info(f"Skipping recently modified file: {path}")

        prev_files = {p: info["sha"] for p, info in state["files"].items()}

        # New files
        new_files = set(current_files.keys()) - set(prev_files.keys())
        for f in new_files:
            logger.info(f"New file detected: {f}")
            organized = organize_file(f)
            rel_path = os.path.relpath(organized, WATCH_DIR)
            folder_path = os.path.dirname(rel_path).replace("\\", "/")
            folder_id = create_nested_folders(folder_path, drive_parent)
            fid = upload_file_to_drive(folder_id, organized)
            state["files"][organized] = {"sha": current_files[f], "id": fid, "state": "created_updated"}

        # Deleted files
        deleted_files = set(prev_files.keys()) - set(current_files.keys())
        for f in deleted_files:
            file_record = state["files"].get(f)
            if file_record and file_record.get("state") != "deleted":
                logger.info(f"File deleted locally: {f}")
                delete_file_from_drive(file_record["id"])
                state["files"][f]["state"] = "deleted"

        # Modified files
        for f, sha in current_files.items():
            if f in prev_files and sha != prev_files[f]:
                file_record = state["files"].get(f)
                if file_record:
                    logger.info(f"File modified: {f}")
                    delete_file_from_drive(file_record["id"])
                    rel_path = os.path.relpath(f, WATCH_DIR)
                    folder_path = os.path.dirname(rel_path).replace("\\", "/")
                    folder_id = create_nested_folders(folder_path, drive_parent)
                    fid = upload_file_to_drive(folder_id, f)
                    state["files"][f]["id"] = fid
                    state["files"][f]["sha"] = sha
                    state["files"][f]["state"] = "created_updated"

        save_state(state)
        time.sleep(10) # Scan each 10 seconds


def start_watcher():
    state = load_state()
    if state.get("is_running"):
        logger.warning("Watcher already running. Exiting.")
        return
    state["is_running"] = True
    save_state(state)
    logger.info(f"Starting watcher on {WATCH_DIR}")
    t = Thread(target=scan_and_sync, args=(os.environ["FOLDER_ID"],), daemon=True)
    t.start()
    try:
        while t.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        state["is_running"] = False
        save_state(state)
        logger.info("Watcher stopped manually.")
