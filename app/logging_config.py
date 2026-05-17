import logging
import os


def setup_logging() -> None:
    log_file = os.environ["LOG_FILE"]
    log_level = os.environ["LOG_LEVEL"]
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file),
        ],
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
