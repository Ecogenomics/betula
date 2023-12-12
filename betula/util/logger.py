import logging
import sys
from pathlib import Path


def init_logger(out_dir: Path, debug=False):
    # Logger setup
    logger = logging.getLogger('betula')
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter('[%(asctime)s | %(levelname)s] - %(message)s', '%Y-%m-%d %H:%M:%S')

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(out_dir / 'betula.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
