"""
Miscellaneous Utilities

author: officialcryptomaster@gmail.com
"""
import time
from datetime import datetime


def now_epoch_secs():
    """integer seconds epoch of current time"""
    return int(time.time())


def now_epoch_msecs():
    """integer milliseconds epoch of current time"""
    return int(time.time() * 1e3)


def now_epoch_usecs():
    """integer micro-seconds epoch of current time"""
    return int(time.time() * 1e6)


def epoch_secs_to_local_time_str(epoch_secs):
    """Get a string of local time representation from integer epoch in seconds"""
    return datetime.fromtimestamp(epoch_secs).strftime("%Y-%m-%d %H:%M:%S")


def epoch_msecs_to_local_time_str(epoch_msecs):
    """Get a string of local time representation from integer epoch in milliseconds"""
    return datetime.fromtimestamp(epoch_msecs/1000).strftime("%Y-%m-%d %H:%M:%S")


def try_(func, *args, **kwargs):
    """Try to call a function and return _default_val if it fails"""
    _default_val = kwargs.pop("_default_val", None)
    try:
        return func(*args, **kwargs)
    except Exception:  # pylint: disable=broad-except
        return None


def paginate(arr, page=1, per_page=20):
    """Given an ordered iterable like a list and a page number, return
    a slice of the iterable which whose elements make up the page.

    Keyword arguments:
    arr -- an ordered iterable like a list
    page -- postive integer number of page to retrieve elements for. Note that
        Pages start at 1 (default: 1)
    per_age -- positive integer number of elements per page
    """
    page_idx = page - 1
    return arr[page_idx: page_idx+per_page]
