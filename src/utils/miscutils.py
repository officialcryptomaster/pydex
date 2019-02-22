"""
Miscellaneous Utilities

author: officialcryptomaster@gmail.com
"""

from pydex_app.constants import DEFAULT_PAGE, DEFAULT_PER_PAGE


def paginate(arr, page=DEFAULT_PAGE, per_page=DEFAULT_PER_PAGE):
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


def to_api_order(signed_order_json):
    """Given a signed order json, make compatible with 0x API Order Schema"""
    return {"metaData": {}, "order": signed_order_json}
