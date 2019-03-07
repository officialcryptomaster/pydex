"""
Unit tests for Web3Client

author: officialcryptomaster@gmail.com
"""

import pytest
from utils.zeroexutils import ZxWeb3Client


@pytest.fixture(scope="module")
def zx_client():
    """ZeroWeb3Client instance for testing"""
    return ZxWeb3Client(
        network_id=50,
        web3_rpc_url="http://127.0.0.1:8545",
    )


def test_account_address(zx_client):  # pylint: disable=redefined-outer-name
    """Make sure public key is created correctly from private key

    Uses the account from 0x ganache-cli (bundled with 0x-starter-kit)
    mnemonic = "concert load couple harbor equip island argue ramp clarify fence smart topic"
    private_key = "f2f48ee19680706196e2e339e5da3491186e0c4c5030670656b0e0164837257d"
    public_key = "0x5409ed021d9299bf6814279a6a1411a7e866a631"
    """
    zx_client.private_key = "f2f48ee19680706196e2e339e5da3491186e0c4c5030670656b0e0164837257d"
    expected_public_key = "0x5409ed021d9299bf6814279a6a1411a7e866a631"
    assert zx_client.account_address == expected_public_key


def test_sign_hash(zx_client):  # pylint: disable=redefined-outer-name
    """Make sure signing a valid hash give correct result"""
    # hash of an empty order
    hash_hex = "0xfaa49b35faeb9197e9c3ba7a52075e6dad19739549f153b77dfcf59408a4b422"
    signature_0x = zx_client.sign_hash_0x_compat(hash_hex)
    expected_signature_0x = (
        "0x1bc5358e0855fc9352c64676765f80fcd3d1d235ef41e910c9a59b22fcbd573e5"
        "44caa9bce4c99c98a6e5da329375059e8202f71631c5a6e26738b79817161c9ac03")
    assert signature_0x == expected_signature_0x
