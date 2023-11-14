import os
import logging
import time
from logging.handlers import RotatingFileHandler

def create_logger(function_name, log_level=logging.INFO):
    """
    Creates a logger with the specified function name and log level.

    Args:
        function_name (str): The name of the function.
        log_level (int): The log level (e.g., logging.DEBUG, logging.INFO).

    Returns:
        Logger: The created logger.
    """
    logger = logging.getLogger(function_name)
    
    if not logger.handlers:
        logger.setLevel(log_level)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        formatter.converter = time.gmtime

        logs_folder = 'logs'
        if not os.path.isdir(logs_folder):
            os.mkdir(logs_folder)

        log_file_path = os.path.join(logs_folder, f'{function_name}.log')

        file_handler = RotatingFileHandler(log_file_path, mode='a+', maxBytes=5*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        logger.propagate = False  

    return logger


def log_info(logger, message):
    """
    Log an informational message.
    """
    logger.info(message)


def log_error(logger, message):
    """
    Log an error message.
    """
    logger.error(message)


def log_debug(logger, message):
    """
    Log a debug message.
    """
    logger.debug(message)


def log_warning(logger, message):
    """
    Log a warning message.
    """
    logger.warning(message)


def log_critical(logger, message):
    """
    Log a critical message.
    """
    logger.critical(message)


def log_exception(logger, message):
    """
    Log an exception message.
    """
    logger.exception(message)


def log_traceback(logger):
    """
    Log the traceback of the current exception.
    """
    logger.exception('Traceback:')


def log_exception_and_traceback(logger, message):
    """
    Log an exception message and log the traceback of the current exception.
    """
    logger.exception(message)
    log_traceback(logger)

