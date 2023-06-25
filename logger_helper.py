import logging
import os

# --------------------------------------------------------
# Set global level of debugging
# True = every logger is by default set to debug logging
# False = every logger is by default set not to debug logging
GLOBAL_DEBUG = True
GLOBAL_LOG_FILENAME = "log.log"
GLOBAL_DEBUG_FILENAME = "debug.log"
LOGGING_LEVEL = logging.INFO

# Local logging
DEBUG = None
LOG_FILENAME = None
DEBUG_FILENAME = None

# --------------------------------------------------------


str_file_format = "[%(levelname)s - %(name)s] %(asctime)s - %(message)s"
str_console_format = "[%(levelname)s - %(name)s] - %(message)s"
date_format = "%H:%M:%S"
file_formatter = logging.Formatter(str_file_format, datefmt=date_format)
console_formatter = logging.Formatter(str_console_format, datefmt=date_format)
# List of every file loggers are writing to
logging_filelist = set()


def setup_logger(name: str, log_filename: str | None, debug: bool | None, debug_filename: str | None) -> logging.Logger:
    if debug is None:
        debug = GLOBAL_DEBUG
    if log_filename is None:
        log_filename = GLOBAL_LOG_FILENAME
    if debug_filename is None:
        debug_filename = GLOBAL_DEBUG_FILENAME
    # If the logging file haven't been set yet but it already exists, we wipe it before opening the file stream
    if log_filename not in logging_filelist:
        if os.path.exists(log_filename):
            os.remove(log_filename)
        logging_filelist.add(log_filename)
    if debug_filename not in logging_filelist:
        if os.path.exists(debug_filename):
            os.remove(debug_filename)
        logging_filelist.add(debug_filename)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # Always add a standard streamhandler for high priority messages (warning++)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    # Always add a standard filehandler that logs to log_filename
    handler = logging.FileHandler(log_filename)
    handler.setLevel(LOGGING_LEVEL)
    handler.setFormatter(file_formatter)
    logger.addHandler(handler)
    # If debugging is enabled, add a debugging file handler
    if debug:
        debug_handler = logging.FileHandler(debug_filename)
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(file_formatter)
        logger.addHandler(debug_handler)
    log_message = "Logger activated with debug " + ("ON" if debug else "OFF")
    logger.info(log_message)
    return logger


# Set up logging
logger = setup_logger(__name__, LOG_FILENAME, DEBUG, DEBUG_FILENAME)

if __name__ == "__main__":
    logger.debug("DEBUG Message")
    logger.info("INFO Message")
    logger.warning("WARNING Message")
    logger.error("ERROR Message")
