"""Custom exception that records where an error happened.

Usage::

    import sys
    from src.exception import CustomException

    try:
        risky_step()
    except Exception as error:
        raise CustomException(error, sys) from error
"""
from __future__ import annotations

from types import ModuleType

from src.logger import logging


def error_message_detail(error: object, error_detail: ModuleType) -> str:
    """Build a readable message with the file name and line of the error.

    Parameters
    ----------
    error : object
        The original exception (or any message) to describe.
    error_detail : module
        The ``sys`` module; its ``exc_info()`` gives the active traceback.

    Returns
    -------
    str
        Message such as "Error in [file.py] at line [12]: division by zero".
    """
    # exc_info() returns (type, value, traceback) of the error being handled.
    _, _, exc_tb = error_detail.exc_info()
    # Outside an "except" block there is no traceback to inspect.
    if exc_tb is None:
        return f"Error: {error}"
    # Walk to the last frame, i.e. the line where the error was raised.
    while exc_tb.tb_next is not None:
        exc_tb = exc_tb.tb_next
    # Name of the Python file that contains that line.
    file_name = exc_tb.tb_frame.f_code.co_filename
    return (f"Error in script [{file_name}] at line [{exc_tb.tb_lineno}]: "
            f"{error}")


class CustomException(Exception):
    """Exception whose text includes the file and line of the failure."""

    def __init__(self, error: object, error_detail: ModuleType) -> None:
        """Store a detailed message and write it to the log file."""
        # Keep the normal Exception behaviour (args, repr, etc.).
        super().__init__(str(error))
        # Detailed message with file name and line number.
        self.error_message = error_message_detail(error, error_detail)
        # Record the error in this run's log file.
        logging.error(self.error_message)

    def __str__(self) -> str:
        """Return the detailed message when the exception is printed."""
        return self.error_message
