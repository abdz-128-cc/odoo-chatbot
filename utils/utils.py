import logging
import os

from utils.constants import LOG_DIR


def create_logger(log_file):
    """
    Creates and configures a logger with file and stream handlers.

    Args:
        log_file: The log file name (will be placed in LOG_DIR).

    Returns:
        The configured logger instance.
    """
    log_dir = LOG_DIR
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        logging.info(f"Created directory: {log_dir}")

    log_file = os.path.join(log_dir, log_file)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger()
    return logger