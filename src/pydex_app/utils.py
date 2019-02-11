"""
Utilities

author: officialcryptomaster@gmail.com
"""
import logging
import os
from decimal import Decimal
import colorlog


def to_base_unit_amount(amount, decimals=18):
    """convert an amount to base unit amount string

    Keyword arguments:
    amount -- numeric or string which can be converted to numeric
    decimals -- integer number of decimal places in the base unit
    """
    return "{:.0f}".format(Decimal(amount) * 10 ** int(decimals))


def paginate(arr, page=1, per_page=20):
    """Given an ordered iterable like a list and a page number, return
    a slice of the iterable which whose elements make up the page.

    Keyword arguments
    arr -- an ordered iterable like a list
    page -- postive integer number of page to retrieve elements for. Note that
        Pages start at 1 (default: 1)
    per_age -- positive integer number of elements per page
    """
    page_idx = page - 1
    return arr[page_idx: page_idx+per_page]


def setup_logger(
    logger_name,
    file_name=None,
    log_to_stdout=True,
    level=logging.DEBUG,
    base_dir="./log",
):
    """Set up a logger which optionally also logs to file

    Keyword arguments:
    logger_name -- string name of logger
    file_name -- string name of logging file. If nothing provided, will not log
        to file
    log_to_std_out -- boolean of whether the log should be output to stdout
        (default: True)
    level -- integer log levels from logging libarary (default: logging.DEBUG)
    base_dir -- string directory of where to put the log file (default: "./log")
    """
    assert file_name or log_to_stdout, "logger without output is useless!"

    logger = logging.getLogger(logger_name)

    formatter_str = (
        "%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s.%(funcName)s():%(lineno)d"
        " - %(message)s")
    time_format_str = "%Y-%m-%d %H:%M:%S"

    if file_name:
        # make sure base_dir is the full dir and file_name is just the filename
        log_path = os.path.join(base_dir, file_name)
        file_name = os.path.basename(log_path)
        base_dir = os.path.dirname(log_path)
        # creat the full directory if it does not exist
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        file_handler = logging.FileHandler(log_path, mode='w+')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(  # pylint: disable=invalid-name
            formatter_str,
            time_format_str)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    if log_to_stdout:
        console_handler = logging.StreamHandler()  # pylint: disable=invalid-name
        console_handler.setLevel(logging.DEBUG)
        color_formatter = colorlog.ColoredFormatter(
            "%(log_color)s" + formatter_str,
            time_format_str,
        )
        console_handler.setFormatter(color_formatter)
        logger.addHandler(console_handler)

    logger.setLevel(level)

    return logger
