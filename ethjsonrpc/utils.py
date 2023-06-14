import json
from pathlib import Path
from typing import Union

import requests
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.account.base_account import BaseAccount
from starknet_py.net.client import Client
from starknet_py.net.signer.stark_curve_signer import KeyPair

from ethjsonrpc.constants import (
    ACCOUNT_ADDRESS,
    ETH_TOKEN_ADDRESS,
    KAKAROT_ADDRESS,
    PRIVATE_KEY,
    RPC_CLIENT,
    STARKNET_CHAIN_ID,
    STARKSCAN_URL,
)


async def get_eth_contract(
    provider: Union[BaseAccount, Client] = RPC_CLIENT
) -> Contract:
    # TODO: re-use Contract.from_address when katana supports getClass
    return Contract(
        ETH_TOKEN_ADDRESS,
        json.loads((Path(__file__).parent / "erc20.json").read_text())["abi"],
        provider,
    )


async def get_kakarot_contract(
    provider: Union[BaseAccount, Client] = RPC_CLIENT
) -> Contract:
    # TODO: re-use Contract.from_address when katana supports getClass
    return Contract(
        KAKAROT_ADDRESS,
        json.loads((Path(__file__).parent / "kakarot.json").read_text())["abi"],
        provider,
    )


def get_account(address=None, private_key=None):
    if (address is None and private_key is not None) or (
        address is not None and private_key is None
    ):
        raise ValueError("address and private_key should both None or not None")
    return Account(
        address=address or ACCOUNT_ADDRESS,
        client=RPC_CLIENT,
        chain=STARKNET_CHAIN_ID,
        key_pair=KeyPair.from_private_key(int(private_key or PRIVATE_KEY, 16)),
    )


def get_explorer_url(path: str, _hash: int) -> str:
    return f"{STARKSCAN_URL}/{path}/0x{_hash:064x}"


def chain_id():
    return bytes.fromhex(
        json.loads(
            requests.post(
                RPC_CLIENT.url,
                json={
                    "jsonrpc": "2.0",
                    "method": f"starknet_chainId",
                    "params": {},
                    "id": 0,
                },
            ).text
        )["result"][2:]
    )
