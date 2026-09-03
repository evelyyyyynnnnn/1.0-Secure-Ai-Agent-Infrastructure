"""Live gas prices from public JSON-RPC nodes, and what they cost in dollars.

The project's venue comparison is currently built on quoted typical gas prices.
Those are honest assumptions but they are assumptions, and they are the input
the whole viability conclusion turns on: whether per-session settlement works
is decided almost entirely by the gas price and the token price on the day.

Every endpoint here is a public node that needs no account, so the measurement
is reproducible by anyone. Each chain is asked two questions:

  eth_gasPrice   what a transaction submitted now would pay
  eth_feeHistory the base fee over recent blocks, which shows the spread a
                 single spot reading hides

The second matters because a viability claim built on one quiet-minute reading
is not a claim about the network, it is a claim about that minute.
"""
from __future__ import annotations

import json

from .datakit import Source

# name -> (rpc url, native token, coingecko id)
CHAINS = {
    "Ethereum L1": ("https://ethereum-rpc.publicnode.com", "ETH", "ethereum"),
    "Arbitrum One": ("https://arbitrum-one-rpc.publicnode.com", "ETH", "ethereum"),
    "Base": ("https://base-rpc.publicnode.com", "ETH", "ethereum"),
    "Optimism": ("https://optimism-rpc.publicnode.com", "ETH", "ethereum"),
    "Polygon PoS": ("https://polygon-bor-rpc.publicnode.com", "POL", "matic-network"),
}

TERMS = "public RPC endpoint, no account required"


def gas_price_source(chain: str) -> Source:
    url, token, _ = CHAINS[chain]
    return Source(
        name=f"{chain} eth_gasPrice", url=url,
        dest=f"chains/{_slug(chain)}-gasprice.json",
        publisher=f"public {chain} RPC", terms=TERMS,
        note=f"spot gas price, denominated in {token}",
        body={"jsonrpc": "2.0", "id": 1, "method": "eth_gasPrice", "params": []},
    )


def fee_history_source(chain: str, blocks: int = 64) -> Source:
    url, token, _ = CHAINS[chain]
    return Source(
        name=f"{chain} eth_feeHistory", url=url,
        dest=f"chains/{_slug(chain)}-feehistory.json",
        publisher=f"public {chain} RPC", terms=TERMS,
        note=f"base fee over the last {blocks} blocks, to show the spread",
        body={"jsonrpc": "2.0", "id": 1, "method": "eth_feeHistory",
              "params": [hex(blocks), "latest", [10, 50, 90]]},
    )


def _slug(name: str) -> str:
    return name.lower().replace(" ", "-")


# --- parsing ---------------------------------------------------------------

def _rpc_result(raw: bytes, method: str):
    d = json.loads(raw)
    if "error" in d:
        raise ValueError(f"{method} returned a JSON-RPC error: {d['error']}")
    if "result" not in d:
        raise ValueError(f"{method} response has no result: {sorted(d)[:5]}")
    return d["result"]


def parse_gas_price(raw: bytes) -> float:
    """Return the spot gas price in gwei.

    JSON-RPC answers in hex wei. Reading it as decimal, or forgetting the 1e9,
    is a mistake that produces a number in the right shape and the wrong order
    of magnitude -- which is fatal here, because the viability threshold is
    itself about an order of magnitude wide.
    """
    wei = int(_rpc_result(raw, "eth_gasPrice"), 16)
    return wei / 1e9


def parse_fee_history(raw: bytes) -> dict:
    """Return base-fee statistics in gwei across the requested block window."""
    res = _rpc_result(raw, "eth_feeHistory")
    fees = [int(x, 16) / 1e9 for x in res.get("baseFeePerGas", [])]
    if not fees:
        raise ValueError("eth_feeHistory returned no baseFeePerGas; the chain "
                         "may predate EIP-1559 or the node may not support it")
    ordered = sorted(fees)
    n = len(ordered)
    return {
        "n_blocks": n,
        "min_gwei": round(ordered[0], 6),
        "median_gwei": round(ordered[n // 2], 6),
        "max_gwei": round(ordered[-1], 6),
        "mean_gwei": round(sum(ordered) / n, 6),
        # The ratio is the honest headline: it says how much a single spot
        # reading could have flattered or damned the conclusion.
        "max_over_min": round(ordered[-1] / ordered[0], 3) if ordered[0] else None,
    }


def parse_token_prices(raw: bytes) -> dict:
    """Parse CoinGecko's simple/price response into {coingecko_id: usd}."""
    d = json.loads(raw)
    out = {}
    for coin, block in d.items():
        if "usd" not in block:
            raise ValueError(f"no usd price for {coin} in the CoinGecko response")
        out[coin] = float(block["usd"])
    if not out:
        raise ValueError("CoinGecko returned no prices")
    return out


def token_price_source() -> Source:
    ids = sorted({cg for _, _, cg in CHAINS.values()})
    return Source(
        name="CoinGecko native token prices",
        url="https://api.coingecko.com/api/v3/simple/price"
            f"?ids={','.join(ids)}&vs_currencies=usd",
        dest="chains/token-prices.json", publisher="CoinGecko",
        terms="free API tier, attribution requested",
        note="USD price of each chain's native token, needed to turn gas into cost",
    )
