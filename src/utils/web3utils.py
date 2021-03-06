"""
Web3 Utilities

author: officialcryptomaster@gmail.com
"""
import re
from decimal import Decimal
from hexbytes import HexBytes
from web3 import Web3, HTTPProvider
from eth_account.messages import defunct_hash_message
from zero_ex.contract_addresses import NetworkId

ETH_BASE_UNIT_DECIMALS = 18
NULL_ADDRESS = "0x0000000000000000000000000000000000000000"

RE_ADDRESS = re.compile("^(0x)?[0-9a-f]{40}$")


def assert_valid_address(address):
    """Assert address is valid hex string"""
    assert RE_ADDRESS.match(address.lower()), "address invalid format"


def assert_valid_address_or_none(address):
    """Assert address is a valid hex string or None"""
    assert address is None or RE_ADDRESS.match(address.lower()), \
        "address valid format"


def get_clean_address_or_throw(address):
    """Get a clean 42 character address with leading '0x' throw

    Keyword argument:
    address: hex-like address
    """
    if not isinstance(address, str):
        address = HexBytes(address).rjust(10, b"\0").hex()
    if not RE_ADDRESS.match(address.lower()):
        raise TypeError("address looks invalid: '{}'".format(address))
    if not address.startswith("0x"):
        address = "0x" + address
    return address


def to_base_unit_amount(amount, decimals=ETH_BASE_UNIT_DECIMALS):
    """convert an amount to base unit amount string

    Keyword arguments:
    amount -- numeric or string which can be converted to numeric
    decimals -- integer number of decimal places in the base unit
    """
    return "{:.0f}".format(Decimal(amount) * 10 ** int(decimals))


def from_base_unit_amount(base_amount, decimals=ETH_BASE_UNIT_DECIMALS):
    """convert an amount from base unit amount to regular units

    Keyword arguments:
    base_amount -- numeric or string which can be converted to numeric
    decimals -- integer number of decimal places in the base unit
    """
    return float(Decimal(base_amount) / 10 ** int(decimals))


class Web3Client:
    """Client for interacting with Web3 using a private key"""

    __name__ = "Web3Client"

    def __init__(
        self,
        network_id,
        web3_rpc_url,
        private_key=None,
    ):
        """Create an instance of the Web3Client with a private key

        Keyword arguments:
        network_id -- numerable id of networkId convertible to `constants.NetworkId`
        web3_rpc_url -- string of the URL of the Web3 service
        private_key -- hex bytes or hex string of private key for signing transactions
            (must be convertible to `HexBytes`) (default: None)
        """
        self._network_id = NetworkId(int(network_id)).value
        self._web3_rpc_url = web3_rpc_url
        self._private_key = None
        self._web3_provider = None
        self._web3_instance = None
        self._web3_eth = None
        self._account = None
        self._account_address = None
        self._markets = None
        if private_key:
            self.private_key = private_key

    def __str__(self):
        return (
            f"[{self.__name__}]"
            f"(network:{self._network_id}"
            f", web_3rpc_url={self._web3_rpc_url}"
            f", account_addres={self.account_address}"
            f"{self._str_arg_append()})"
        )

    __repr__ = __str__

    def _str_arg_append(self):  # pylint: disable=no-self-use
        """String to append to list of params for `__str__`"""
        return ""

    @property
    def private_key(self):
        """Get the private key as `HexBytes` object"""
        if not self._private_key:
            return ""
        # equivalent of binascii.hexlify(self._private_key).decode("utf-8").lower()
        return self._private_key.hex()

    @private_key.setter
    def private_key(self, value):
        """Set the private key as a `HexBytes` object and update the account

        Keyword argument:
        value -- hex bytes or hex string of private key for signing transactions
            (must be convertible to `HexBytes`)
        """
        # Use HexBytes instead of binascii.a2b_hex for convenience
        self._private_key = HexBytes(value)
        self._account_address = self.account_address

    @property
    def web3_provider(self):
        """Get a Web3 HTTPProvider instance with lazy instantiation"""
        if not self._web3_provider:
            if self._web3_rpc_url:
                self._web3_provider = HTTPProvider(self._web3_rpc_url)
        return self._web3_provider

    @property
    def web3_instance(self):
        """Get a Web3 instance with lazy instantiation"""
        if not self._web3_instance:
            web3_provider = self.web3_provider
            if self.web3_provider:
                self._web3_instance = Web3(web3_provider)
                self._web3_eth = self._web3_instance.eth  # pylint: disable=no-member
        return self._web3_instance

    @property
    def web3_eth(self):
        """Get the eth member of the Web3 instance with lazy instantiation"""
        if not self._web3_eth:
            web3_instance = self.web3_instance
            if web3_instance:
                self._web3_eth = web3_instance.eth  # pylint: disable=no-member
        return self._web3_eth

    @property
    def account(self):
        """Get the Web3 account object associated with the private key"""
        if not self._account:
            if self._private_key:
                web3_eth = self.web3_eth
                self._account = web3_eth.account.privateKeyToAccount(
                    self._private_key)
                self._account_address = self._account.address.lower()
        return self._account

    @property
    def account_address(self):
        """Get the account address as a hexstr"""
        if not self._account_address:
            account = self.account
            if account:
                self._account_address = account.address.lower()
        return self._account_address

    @account_address.setter
    def account_address(self, addr_str):
        """Set the account address to something other than the main one
        This may be useful if you used anything other than the first account
        controlled by your private key.
        """
        self._account_address = addr_str.lower()

    @property
    def account_address_checksumed(self):
        """Get the account address as a checksumable hexstr"""
        return self.get_checksum_address(self.account_address)

    def sign_hash(self, hash_hex):
        """Returns the ec_signature from signing the hash_hex with eth-sign
        Note: If you need to sign for 0x, then use `ZxWeb3Client.sign_hash_zx_compat`


        Keyword argument:
        hash_hex -- hex bytes or hex str of a hash to sign
            (must be convertile to `HexBytes`)
        """
        if not self._private_key:
            raise Exception("Please set the private_key for signing hash_hex")
        msg_hash_hexbytes = defunct_hash_message(HexBytes(hash_hex))
        ec_signature = self.web3_eth.account.signHash(
            msg_hash_hexbytes,
            private_key=self._private_key,
        )
        return ec_signature

    @classmethod
    def get_checksum_address(cls, addr):
        """Get a checksum address from a regular address"""
        return Web3.toChecksumAddress(addr.lower())

    def get_eth_balance(self):
        """Get ether balance associated with client address"""
        return self.web3_eth.getBalance(
            self.account_address_checksumed) / 10**ETH_BASE_UNIT_DECIMALS
