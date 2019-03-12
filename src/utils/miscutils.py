"""
Miscellaneous Utilities

author: officialcryptomaster@gmail.com
"""
import time
from datetime import datetime
from decimal import Decimal


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
    """Try to call a function and return _default if it fails
    Note: be careful that in order to have a fallback, you can supply
    the keyword argument `_default`. If you supply anything other
    than a keyword arg, it will result in it being passed to the wrapped
    function and could cause unexpected behavior including always failing
    with default value of None.
    """
    _default_val = kwargs.pop("_default", None)
    try:
        return func(*args, **kwargs)
    except Exception:  # pylint: disable=broad-except
        return _default_val


def assert_like_integer(value):
    """Assert value is representing an integer"""
    decimal_val = Decimal(value)
    assert decimal_val == round(decimal_val), "value not like an integer"


def paginate(arr, page=1, per_page=20):
    """Given an ordered iterable like a list and a page number, return
    a slice of the iterable which whose elements make up the page.

    Keyword arguments:
    arr -- an ordered iterable like a list
    page -- postive integer number of page to retrieve elements for. Note that
        Pages start at 1 (default: 1)
    per_page -- positive integer number of elements per page (default: 20)
    """
    page_idx = page - 1
    return arr[page_idx: page_idx+per_page]


def normalize_query_param(query_param):
    """Normalize query parameter to lower case"""
    return query_param.lower() if query_param else None


def to_api_order(signed_order_json):
    """Given a signed order json, make compatible with 0x API Order Schema"""
    return {"metaData": {}, "order": signed_order_json}
