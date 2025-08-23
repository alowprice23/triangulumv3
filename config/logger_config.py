import logging
import sys

def setup_logging(level=logging.INFO):
    """
    Sets up a standardized logger for the application.
    """
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers to avoid duplicate logs
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Create a handler to write to stdout
    handler = logging.StreamHandler(sys.stdout)

    # Create a formatter and add it to the handler
    # Example format: [TIMESTAMP] LEVEL - (module.function): message
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s - (%(module)s.%(funcName)s): %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    # Add the handler to the root logger
    root_logger.addHandler(handler)

# You can call this once at the application's entry point.
# For example, in `cli/main.py` or `api/main.py`.
# setup_logging()
