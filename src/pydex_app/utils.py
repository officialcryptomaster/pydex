"""
Utilities

author: officialcryptomaster@gmail.com
"""

from decimal import Decimal


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
