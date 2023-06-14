import io
import json
import os
import re
import zipfile
from enum import Enum
from pathlib import Path

import requests
from dotenv import load_dotenv
from starknet_py.net.full_node_client import FullNodeClient

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
    katana = int.from_bytes(b"KATANA", "big")


NETWORK = os.getenv("STARKNET_NETWORK", "katana")
NETWORK = (
    "testnet"
    if re.match(r".*(testnet|goerli)$", NETWORK, flags=re.I)
    else "testnet2"
    if re.match(r".*(testnet|goerli)-?2$", NETWORK, flags=re.I)
    else "mainnet"
    if re.match(r".*(mainnet).*", NETWORK, flags=re.I)
    else "sharingan"
    if re.match(r".*(sharingan).*", NETWORK, flags=re.I)
    else "katana"
    if re.match(r".*(katana).*", NETWORK, flags=re.I)
    else "madara"
    if re.match(r".*(madara).*", NETWORK, flags=re.I)
    else "devnet"
)

STARKSCAN_URLS = {
    "mainnet": "https://starkscan.co",
    "testnet": "https://testnet.starkscan.co",
    "testnet2": "https://testnet-2.starkscan.co",
    "devnet": "https://devnet.starkscan.co",
    "sharingan": "https://starknet-madara.netlify.app/#/explorer/query",
    "katana": "",
    "madara": "",
}
STARKSCAN_URL = STARKSCAN_URLS[NETWORK]

if not os.getenv("RPC_KEY") and NETWORK in ["mainnet", "testnet", "testnet2"]:
    raise ValueError(f"RPC_KEY env variable is required when targeting {NETWORK}")
RPC_URLS = {
    "mainnet": f"https://starknet-mainnet.infura.io/v3/{os.getenv('RPC_KEY')}",
    "testnet": f"https://starknet-goerli.infura.io/v3/{os.getenv('RPC_KEY')}",
    "testnet2": f"https://starknet-goerli2.infura.io/v3/{os.getenv('RPC_KEY')}",
    "devnet": "http://127.0.0.1:5050/rpc",
    "sharingan": os.getenv("SHARINGAN_RPC_URL"),
    "katana": "http://127.0.0.1:5050",
    "madara": "http://127.0.0.1:9944",
}
RPC_CLIENT = FullNodeClient(node_url=RPC_URLS[NETWORK])


class ChainId(Enum):
    mainnet = int.from_bytes(b"SN_MAIN", "big")
    testnet = int.from_bytes(b"SN_GOERLI", "big")
    testnet2 = int.from_bytes(b"SN_GOERLI2", "big")
    devnet = int.from_bytes(b"SN_GOERLI", "big")
    sharingan = int.from_bytes(b"SN_GOERLI", "big")
    katana = int.from_bytes(b"KATANA", "big")
    madara = int.from_bytes(b"SN_GOERLI", "big")


STARKNET_CHAIN_ID = getattr(ChainId, NETWORK)

ACCOUNT_ADDRESS = os.environ.get(
    f"{NETWORK.upper()}_ACCOUNT_ADDRESS"
) or os.environ.get("ACCOUNT_ADDRESS")
PRIVATE_KEY = os.environ.get(f"{NETWORK.upper()}_PRIVATE_KEY") or os.environ.get(
    "PRIVATE_KEY"
)

KAKAROT_ADDRESS = os.getenv("KAKAROT_ADDRESS")
if KAKAROT_ADDRESS is None:
    if (
        path := Path(__file__).absolute().parents[2]
        / "kakarot"
        / "deployments"
        / NETWORK
        / "deployments.json"
    ).is_file():
        KAKAROT_ADDRESS = json.loads(path.read_text())["kakarot"]["address"]
    else:
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
            (Path("deployments") / NETWORK / "deployments.json").read_text()
        )["kakarot"]["address"]
