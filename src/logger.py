"""Project-wide logging set-up.

Importing this module creates one log file per run inside the project's
``logs`` folder, for example ``logs/11_15_2026_14_05_33.log``.
Usage in any other module::

    from src.logger import logging
    logging.info("Data loaded")
"""
import logging
import os
from datetime import datetime

# File name built from the current date and time, so every run gets its own.
LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"

# Project root = the folder above "src" (this file lives in src/).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Folder that holds the log files (only the folder, not the file name).
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# Create the logs folder if it does not exist yet.
os.makedirs(LOGS_DIR, exist_ok=True)

# Full path of this run's log file: <project>/logs/<date_time>.log
LOG_FILE_PATH = os.path.join(LOGS_DIR, LOG_FILE)

# Send all messages of level INFO and above to the log file.
logging.basicConfig(
    filename=LOG_FILE_PATH,
    format=("[ %(asctime)s ] %(lineno)d %(name)s - "
            "%(levelname)s - %(message)s"),
    level=logging.INFO,
)


if __name__ == "__main__":
    # Quick self-test: run "python -m src.logger" from the project folder.
    logging.info("Logging has started")
    print(f"Log written to: {LOG_FILE_PATH}")
