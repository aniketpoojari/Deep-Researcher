import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
                logging.StreamHandler(),  # Console
                logging.FileHandler("assistant.log")
            ]
)


def get_logger(name: str):
    """Get a logger instance."""
    return logging.getLogger(name)