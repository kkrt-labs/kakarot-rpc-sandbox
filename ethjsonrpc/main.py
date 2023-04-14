import json
import logging
import subprocess
import time
from typing import List, Optional, Union

import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ethjsonrpc.constants import GATEWAY_URL, STARKNET_NETWORK
from ethjsonrpc.eth_client import EthClient

load_dotenv()


# Set up custom logging formatter
class CustomFormatter(logging.Formatter):
    def format(self, record):
        level_color_map = {
            "INFO": "\033[32m",
            "WARNING": "\033[33m",
            "ERROR": "\033[31m",
            "CRITICAL": "\033[31;1m",
            "DEBUG": "\033[37m",
        }
        color_prefix = level_color_map.get(record.levelname, "")
        color_suffix = "\033[0m" if color_prefix else ""
        formatted_msg = (
            f"{color_prefix}{record.levelname: <9}{color_suffix} {record.getMessage()}"
        )
        return formatted_msg


handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
logger = logging.getLogger("uvicorn")
logger.handlers = [handler]
logger.setLevel(logging.INFO)

# Run a devnet if it is not already started elsewhere (e.g. docker)
if STARKNET_NETWORK == "devnet":
    try:
        response = requests.get(f"{GATEWAY_URL}/is_alive")
        if response.status_code != 200:
            raise ValueError(
                "Devnet port is used but devnet 'is_alive' is not returning 200"
            )
    except requests.exceptions.ConnectionError:
        logger.info(f"⏳ Starting devnet in background")
        devnet = subprocess.Popen(
            [
                "starknet-devnet",
                "--seed",
                "0",
                "--disable-rpc-request-validation",
                "--load-path",
                "deployments/devnet/devnet.pkl",
            ],
            stdout=subprocess.PIPE,
        )
        is_alive = False
        attempts = 0
        max_retries = 10
        while not is_alive and attempts < max_retries:
            try:
                response = requests.get(f"{GATEWAY_URL}/is_alive")
                is_alive = response.status_code == 200
            except:
                time.sleep(1)
            finally:
                attempts += 1
        if not is_alive:
            raise ValueError(f"starknet-devnet failed to initialize in {max_retries}s")
    logger.info(f"✅ Devnet running in background")


class RequestContextLogMiddleware(BaseHTTPMiddleware):
    async def set_body(self, request: Request):
        receive_ = await request._receive()

        async def receive():
            return receive_

        request._receive = receive

    async def dispatch(self, request: Request, call_next):
        await self.set_body(request)

        try:
            body = await request.json()
            logger.debug(f"RPC request:\n\t{body}")
        except:
            logger.warning("Cannot parse request")

        response = await call_next(request)

        try:
            response_body = [chunk async for chunk in response.body_iterator]
            response.body_iterator = iterate_in_threadpool(iter(response_body))
            logger.debug(f"RPC response:\n\t{json.loads(response_body[0].decode())}")
        except:
            logger.warning("Cannot parse response")

        return response


middleware = [
    Middleware(RequestContextLogMiddleware),
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ),
]
app = FastAPI(middleware=middleware)


@app.on_event("startup")
async def get_client():
    global eth_client
    eth_client = await EthClient.new(GATEWAY_URL)


class Payload(BaseModel):
    jsonrpc: str
    method: str
    params: Optional[list]
    id: Union[int, str]


class Result(BaseModel):
    id: Union[int, str]
    jsonrpc: str
    result: Optional[Union[dict, List[str], str, int]]


class MintRequest(BaseModel):
    address: str
    amount: int


class MintResponse(BaseModel):
    new_balance: int
    tx_hash: str
    unit: str


@app.post("/")
async def main(payload: Payload) -> Result:
    if not hasattr(eth_client, payload.method):
        raise NotImplementedError(f"{payload.method}({','.join(payload.params or [])})")
    return Result(
        id=payload.id,
        jsonrpc=payload.jsonrpc,
        result=await getattr(eth_client, payload.method)(*(payload.params or [])),
    )


@app.post("/mint")
async def mint(payload: MintRequest) -> MintResponse:
    starknet_address = await eth_client.compute_starknet_address(payload.address)
    response = requests.post(
        f"{eth_client.starknet_gateway.net}/mint",
        json={"address": hex(starknet_address), "amount": payload.amount},
    )
    return MintResponse(**response.json())


@app.options("/")
async def options(*args, **kwargs):
    return
