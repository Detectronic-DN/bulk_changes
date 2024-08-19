import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

T = TypeVar("T")


class ColorFormatter(logging.Formatter):
    """
    Logging formatter supporting colored output.
    """

    COLOR_CODES: Dict[int, str] = {
        logging.DEBUG: "\033[36m",  # Cyan
        logging.INFO: "\033[32m",  # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[1;31m",  # Bold Red
    }
    RESET_CODE: str = "\033[0m"

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = "%",
        use_color: bool = True,
    ) -> None:
        """
        Initialize the ColorFormatter.

        Args:
            fmt (Optional[str]): The format string for the logger.
            datefmt (Optional[str]): The date format string for the logger.
            style (str): The style of the format string ('percent', 'string', or 'dollar').
            use_color (bool): Whether to use colored output.
        """
        super().__init__(fmt, datefmt, style)
        self.use_color: bool = use_color

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the specified record as text.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log record.
        """
        if self.use_color:
            record.color_on = self.COLOR_CODES.get(record.levelno, self.RESET_CODE)
            record.color_off = self.RESET_CODE
        else:
            record.color_on = record.color_off = ""
        return super().format(record)


class Logger:
    def __init__(self, name: str = __name__, log_level: int = logging.INFO) -> None:
        """
        Initialize the Logger.

        Args:
            name (str): The name of the logger.
            log_level (int): The logging level.
        """
        self.logger: logging.Logger = logging.getLogger(name)

        if not self.logger.handlers:
            self.logger.setLevel(log_level)

            formatter = ColorFormatter(
                "%(color_on)s[%(asctime)s] %(message)s%(color_off)s"
            )
            formatter.converter = time.gmtime  # Use GMT for timestamps

            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)

            self.logger.addHandler(stream_handler)
            self.logger.propagate = False  # Avoid duplicate logs

    def _log_with_context(self, level: int, message: str, **context: Any) -> None:
        """
        Log a message with context at the specified level.

        Args:
            level (int): The logging level.
            message (str): The message to log.
            **context: Additional context to include in the log message.
        """
        context_str = " ".join(f"{k}={v}" for k, v in context.items())
        full_message = f"{message} [{context_str}]" if context_str else message
        self.logger.log(level, full_message)

    def info(self, message: str, **context: Any) -> None:
        """
        Log an informational message.

        Args:
            message (str): The message to log.
            **context: Additional context to include in the log message.
        """
        self._log_with_context(logging.INFO, message, **context)

    def error(self, message: str, **context: Any) -> None:
        """
        Log an error message.

        Args:
            message (str): The message to log.
            **context: Additional context to include in the log message.
        """
        self._log_with_context(logging.ERROR, message, **context)

    def debug(self, message: str, **context: Any) -> None:
        """
        Log a debug message.

        Args:
            message (str): The message to log.
            **context: Additional context to include in the log message.
        """
        self._log_with_context(logging.DEBUG, message, **context)

    def warning(self, message: str, **context: Any) -> None:
        """
        Log a warning message.

        Args:
            message (str): The message to log.
            **context: Additional context to include in the log message.
        """
        self._log_with_context(logging.WARNING, message, **context)

    def critical(self, message: str, **context: Any) -> None:
        """
        Log a critical message.

        Args:
            message (str): The message to log.
            **context: Additional context to include in the log message.
        """
        self._log_with_context(logging.CRITICAL, message, **context)

    def exception(self, message: str, **context: Any) -> None:
        """
        Log an exception message.

        Args:
            message (str): The message to log.
            **context: Additional context to include in the log message.
        """
        self.logger.exception(message, extra=context)

    @staticmethod
    def log_execution(
        level: int = logging.INFO,
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """
        Decorator to log the execution of a function.

        Args:
            level (int): The logging level for the execution logs.

        Returns:
            Callable: A decorator function.
        """

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                logger = Logger(func.__module__)
                logger._log_with_context(level, f"Executing {func.__name__}")
                result = func(*args, **kwargs)
                logger._log_with_context(level, f"Finished executing {func.__name__}")
                return result

            return wrapper

        return decorator
