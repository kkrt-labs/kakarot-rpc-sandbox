from typing import Optional

from starknet_py.contract import Contract
from starknet_py.net import AccountClient
from starknet_py.net.client import Client
from starknet_py.net.client_models import Call
from starknet_py.net.gateway_client import GatewayClient
from starknet_py.net.models import Address
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.proxy.contract_abi_resolver import ProxyConfig
from starknet_py.proxy.proxy_check import ProxyCheck
from starkware.starknet.public.abi import get_selector_from_name

from ethjsonrpc.constants import (
    ACCOUNT_ADDRESS,
    ETH_TOKEN_ADDRESS,
    GATEWAY_CLIENT,
    GATEWAY_URL,
    KAKAROT_ADDRESS,
    PRIVATE_KEY,
    STARKNET_CHAIN_ID,
    STARKNET_NETWORK,
    STARKSCAN_URL,
)


async def get_eth_contract(client=GATEWAY_CLIENT) -> Contract:
    class EthProxyCheck(ProxyCheck):
        """
        See https://github.com/software-mansion/starknet.py/issues/856
        """

        async def implementation_address(
            self, address: Address, client: Client
        ) -> Optional[int]:
            return await self.get_implementation(address, client)

        async def implementation_hash(
            self, address: Address, client: Client
        ) -> Optional[int]:
            return await self.get_implementation(address, client)

        @staticmethod
        async def get_implementation(address: Address, client: Client) -> Optional[int]:
            call = Call(
                to_addr=address,
                selector=get_selector_from_name("implementation"),
                calldata=[],
            )
            (implementation,) = await client.call_contract(call=call)
            return implementation

    proxy_config = (
        ProxyConfig(proxy_checks=[EthProxyCheck()])
        if STARKNET_NETWORK != "devnet"
        else False
    )
    return await Contract.from_address(
        ETH_TOKEN_ADDRESS, client, proxy_config=proxy_config
    )


async def get_kakarot_contract(client=GATEWAY_CLIENT) -> Contract:
    return await Contract.from_address(KAKAROT_ADDRESS, client)


def get_account(address=None, private_key=None):
    if (address is None and private_key is not None) or (
        address is not None and private_key is None
    ):
        raise ValueError("address and private_key should both None or not None")
    return AccountClient(
        address=address or ACCOUNT_ADDRESS,
        client=GatewayClient(net=GATEWAY_URL),
        supported_tx_version=1,
        chain=STARKNET_CHAIN_ID,
        key_pair=KeyPair.from_private_key(int(private_key or PRIVATE_KEY, 16)),
    )


def get_explorer_url(path: str, _hash: int) -> str:
    return f"{STARKSCAN_URL}/{path}/0x{_hash:064x}"
