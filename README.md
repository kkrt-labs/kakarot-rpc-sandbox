# Kakarot RPC sandbox

Python client for Kakarot using the standard JSON-RPC interface. It implements
the most used RPC methods and raise otherwise. The main goal of this RPC is to
iterate fast and not to be used in production!

## Important note

The API is not yet stable, so please use caution when upgrading.

## How-to

Use `poetry` to install the project:

```bash
poetry install
```

Copy the `.env.example` file into a `.env` file and fill the corresponding env
variables. Especially, you need to get a personal `GITHUB_TOKEN` to be able to
download the deployment artifacts from the kakarot repository:

- open your [github settings](https://github.com/settings/tokens)
- generate a new token with "repo" scope

Run the node in watch mode with `uvicorn`:

```bash
uvicorn ethjsonrpc.main:app --reload
```

The node uses the `STARKNET_NETWORK` env variable to decides which network it's
based on:

- mainnet
- testnet
- testnet2
- devnet
- katana (default)

The default value requires a devnet to run locally. If you intend to run the
node using Katana as a backend,
[be sure to run it](https://book.dojoengine.org/framework/katana/overview.html)
and deploy kakarot following the doc in the
[Kakarot main repo](https://github.com/kkrt-labs/kakarot/blob/main/README.md#deploy).

VS-code users: the `.vscode` folder defines a `launch.json` config file that is
interpreter by VS Code. Simple go to the "Run and Debug" tab and it should
display the `Ethjsonrpc` configuration.

## Implemented JSON-RPC methods

- eth_chainId
- eth_gasPrice
- eth_maxPriorityFeePerGas
- eth_feeHistory
- eth_blockNumber
- eth_getBalance
- eth_getTransactionCount
- eth_sendRawTransaction
- eth_call
- eth_estimateGas
- eth_getBlockByHash
- eth_getBlockByNumber
- eth_getTransactionReceipt
- eth_getCode
- eth_getTransactionByHash
- eth_signTransaction
- eth_sendTransaction
- eth_accounts

A `/mint` route is added to mint ETH to the given EVM address when using a
devnet (katana or starknet-devnet) as the Starknet network:

```bash
curl http://127.0.0.1:8000/mint -H 'Content-Type: application/json' -d '{"address": "0xc0ffee", "amount": 1234}'
```

## Reference

- [JSON-RPC wiki](https://github.com/ethereum/wiki/wiki/JSON-RPC)
