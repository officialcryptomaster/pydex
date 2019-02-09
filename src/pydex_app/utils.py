from decimal import Decimal
import os
import logging
import colorlog

ZERO = Decimal(0)
ZERO_STR = "0"
MAX_INT = Decimal(2) ** 256
MAX_INT_STR = "{:.0f}".format(MAX_INT)


def to_base_unit_amount(amount, decimals=18):
    return "{:.0f}".format(Decimal(amount) * 10 ** decimals)

def paginate(arr, page=1, per_page=20):
    page_idx = page - 1
    return arr[page_idx: page_idx+per_page]


def setup_logger(logger_name, log_file, level=logging.DEBUG):
    l = logging.getLogger(logger_name)

    formatter = logging.Formatter('[%(name)s] %(asctime)s : %(message)s')

    logdir = "./log/"
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    fileHandler = logging.FileHandler(logdir + log_file, mode='w')
    fileHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)

    handler = colorlog.StreamHandler()
    colorformat = colorlog.ColoredFormatter('%(log_color)s[%(name)s] %(message)s - (%(asctime)s) %(lineno)d')
    handler.setFormatter(colorformat)

    l.addHandler(handler)
    return l
