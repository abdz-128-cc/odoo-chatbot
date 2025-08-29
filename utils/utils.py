import logging
import os

from utils.constants import LOG_DIR


def create_logger(log_file):

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