import io
import json
import os
import re
import zipfile
from enum import Enum
from pathlib import Path

import requests
from dotenv import load_dotenv
from starknet_py.net.gateway_client import GatewayClient

load_dotenv()

CHAIN_ID = int.from_bytes(b"KKRT", "big")
ETH_TOKEN_ADDRESS = 0x49D36570D4E46F48E99674BD3FCC84644DDD6B96F7C741B1562B82F9E004DC7
GAS_PRICE = int(1e9)
PRIORITY_GAS_PRICE = GAS_PRICE * 10


class StarknetChainId(Enum):
    mainnet = int.from_bytes(b"SN_MAIN", "big")
    testnet = int.from_bytes(b"SN_GOERLI", "big")
    testnet2 = int.from_bytes(b"SN_GOERLI2", "big")
    devnet = int.from_bytes(b"SN_GOERLI", "big")


STARKNET_NETWORK = os.getenv("STARKNET_NETWORK", "starknet-devnet")
STARKNET_NETWORK = (
    "testnet"
    if re.match(r".*(testnet|goerli)$", STARKNET_NETWORK, flags=re.I)
    else "testnet2"
    if re.match(r".*(testnet|goerli)-?2$", STARKNET_NETWORK, flags=re.I)
    else "devnet"
    if re.match(r".*(devnet|local).*", STARKNET_NETWORK, flags=re.I)
    else "mainnet"
)
GATEWAY_URLS = {
    "mainnet": "alpha-mainnet",
    "testnet": "https://alpha4.starknet.io",
    "testnet2": "https://alpha4-2.starknet.io",
    "devnet": "http://127.0.0.1:5050",
}
GATEWAY_URL = GATEWAY_URLS[STARKNET_NETWORK]
GATEWAY_CLIENT = GatewayClient(net=GATEWAY_URL)
STARKNET_CHAIN_ID = getattr(StarknetChainId, STARKNET_NETWORK)

ACCOUNT_ADDRESS = (
    os.environ.get(f"{STARKNET_NETWORK.upper()}_ACCOUNT_ADDRESS")
    or os.environ["ACCOUNT_ADDRESS"]
)
PRIVATE_KEY = (
    os.environ.get(f"{STARKNET_NETWORK.upper()}_PRIVATE_KEY")
    or os.environ["PRIVATE_KEY"]
)
STARKSCAN_URLS = {
    "mainnet": "https://starkscan.co",
    "testnet": "https://testnet.starkscan.co",
    "testnet2": "https://testnet-2.starkscan.co",
    "devnet": "https://devnet.starkscan.co",
}
STARKSCAN_URL = STARKSCAN_URLS[STARKNET_NETWORK]


deployments = sorted(
    [
        a
        for a in requests.get(
            "https://api.github.com/repos/sayajin-labs/kakarot/actions/artifacts"
        ).json()["artifacts"]
        if a["name"] == "deployments"
    ],
    key=lambda a: a["created_at"],
    reverse=True,
)[0]
response = requests.get(
    deployments["archive_download_url"],
    headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"},
)

z = zipfile.ZipFile(io.BytesIO(response.content))
z.extractall("deployments")
KAKAROT_ADDRESS = json.loads(
    (Path("deployments") / STARKNET_NETWORK / "deployments.json").read_text()
)["kakarot"]["address"]
