import logging
import sys


def setup_logger(name: str = "dedupe_it") -> logging.Logger:
    """Create and configure logger"""
    logger = logging.getLogger(name)

    # Only add handlers if they haven't been added already
    if not logger.handlers:
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(module)s | %(message)s")
        )
        logger.addHandler(handler)

        # Set level
        logger.setLevel(logging.DEBUG)

        # Prevent propagation to root logger
        logger.propagate = False

    return logger


# Create default logger instance
logger = setup_logger()
