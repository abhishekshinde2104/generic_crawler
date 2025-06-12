import logging
from datetime import datetime


def start_logging(log_filename):
    """
    Log the current date and time when logging is started.
    """
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info(f"Logging started at {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
