import logging
import colorlog


def setup_logger():
    """Set up a single logger for all modules."""

    # Logs to console
    console_log_handler = colorlog.StreamHandler()
    console_log_handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )
    logger = colorlog.getLogger("app_logger")

    # Log config
    logger.setLevel(logging.DEBUG)
    if not logger.hasHandlers():
        logger.addHandler(console_log_handler)  # Console

    return logger


# Create a global logger instance
logger = setup_logger()
