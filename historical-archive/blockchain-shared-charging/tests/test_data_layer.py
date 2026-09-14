"""Tests for the live-gas measurement path.

The RPC calls need a network. Decoding their answers does not, and that is
where the damage would be: hex wei read as decimal, or the 1e9 forgotten,
produces a gas price in the right shape and the wrong order of magnitude --
fatal, because the viability threshold this project reports is itself only
about an order of magnitude wide.
"""
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from data import datakit
from data.chains import (CHAINS, fee_history_source, gas_price_source,
                         parse_fee_history, parse_gas_price,
                         parse_token_prices, token_price_source)


def _rpc(result):
    return json.dumps({"jsonrpc": "2.0", "id": 1, "result": result}).encode()


def test_gas_price_decodes_hex_wei_to_gwei():
    # 0x3b9aca00 == 1,000,000,000 wei == exactly 1 gwei.
    assert parse_gas_price(_rpc("0x3b9aca00")) == pytest.approx(1.0)
    # 25 gwei
    assert parse_gas_price(_rpc(hex(25 * 10**9))) == pytest.approx(25.0)


def test_gas_price_handles_an_l2_sub_gwei_reading():
    """L2 gas is a small fraction of a gwei; truncating it to an int is wrong."""
    assert parse_gas_price(_rpc(hex(10**6))) == pytest.approx(0.001)


def test_rpc_errors_are_raised_not_parsed_as_zero():
    err = json.dumps({"jsonrpc": "2.0", "id": 1,
                      "error": {"code": -32601, "message": "not supported"}}).encode()
    with pytest.raises(ValueError, match="JSON-RPC error"):
        parse_gas_price(err)


def test_missing_result_raises():
    with pytest.raises(ValueError, match="no result"):
        parse_gas_price(json.dumps({"jsonrpc": "2.0", "id": 1}).encode())


def test_fee_history_reports_the_spread_a_spot_reading_hides():
    fees = [hex(int(g * 1e9)) for g in (8.0, 12.0, 40.0, 10.0, 9.5)]
    stats = parse_fee_history(_rpc({"baseFeePerGas": fees, "oldestBlock": "0x1"}))
    assert stats["n_blocks"] == 5
    assert stats["min_gwei"] == pytest.approx(8.0)
    assert stats["max_gwei"] == pytest.approx(40.0)
    assert stats["median_gwei"] == pytest.approx(10.0)
    # The headline number: a single reading could have been 5x off.
    assert stats["max_over_min"] == pytest.approx(5.0)


def test_fee_history_without_base_fees_is_an_explicit_failure():
    with pytest.raises(ValueError, match="baseFeePerGas"):
        parse_fee_history(_rpc({"oldestBlock": "0x1"}))


def test_token_prices_parse_and_missing_usd_raises():
    raw = json.dumps({"ethereum": {"usd": 3120.44},
                      "matic-network": {"usd": 0.41}}).encode()
    assert parse_token_prices(raw)["ethereum"] == pytest.approx(3120.44)
    with pytest.raises(ValueError, match="no usd price"):
        parse_token_prices(json.dumps({"ethereum": {"eur": 1.0}}).encode())


def test_every_chain_has_a_price_source_for_its_native_token():
    """A chain whose token has no USD price would report cost in gas units."""
    ids = token_price_source().url
    for _, _, cg in CHAINS.values():
        assert cg in ids


def test_rpc_sources_are_post_requests_with_distinct_bodies():
    g = gas_price_source("Ethereum L1")
    h = fee_history_source("Ethereum L1")
    assert g.body["method"] == "eth_gasPrice"
    assert h.body["method"] == "eth_feeHistory"
    # Same URL, different question: the cache must key on the body too.
    assert g.url == h.url
    assert datakit._fingerprint(g) != datakit._fingerprint(h)


# --- the end-to-end real path ---------------------------------------------

def test_load_chain_costs_refuses_an_empty_cache(tmp_path):
    from data.load import load_chain_costs
    with pytest.raises(datakit.FetchError, match="no chain data cached"):
        load_chain_costs(root=tmp_path)


def _seed(tmp_path, gwei=None, with_prices=True):
    gwei = gwei or {"Ethereum L1": 24.0, "Arbitrum One": 0.012, "Base": 0.008,
                    "Optimism": 0.001, "Polygon PoS": 31.0}
    f = datakit.Fetcher(tmp_path)
    man = f.load_manifest()
    (f.raw / "chains").mkdir(parents=True, exist_ok=True)

    def put(dest, payload, url):
        (f.raw / dest).write_bytes(payload)
        man["files"][dest] = {
            "source": dest, "url": url, "publisher": "test", "terms": "test",
            "sha256": datakit.sha256_file(f.raw / dest), "bytes": len(payload),
            "retrieved_utc": datakit.utc_now(), "request_fingerprint": "x"}

    for chain, g in gwei.items():
        slug = chain.lower().replace(" ", "-")
        put(f"chains/{slug}-gasprice.json", _rpc(hex(int(g * 1e9))),
            CHAINS[chain][0])
        fees = [hex(int(g * 1e9 * m)) for m in (0.8, 1.0, 1.6)]
        put(f"chains/{slug}-feehistory.json",
            _rpc({"baseFeePerGas": fees, "oldestBlock": "0x1"}), CHAINS[chain][0])
    if with_prices:
        put("chains/token-prices.json",
            json.dumps({"ethereum": {"usd": 3000.0},
                        "matic-network": {"usd": 0.40}}).encode(),
            "https://api.coingecko.com/")
    f._write_manifest(man)
    return f


def test_missing_token_price_is_refused_rather_than_priced_in_gas_units(tmp_path):
    _seed(tmp_path, with_prices=False)
    from data.load import load_chain_costs
    with pytest.raises(datakit.FetchError, match="no USD price"):
        load_chain_costs(root=tmp_path)


def test_chain_costs_carry_the_retrieval_time(tmp_path):
    """A gas price is a fact about a minute, so the minute must travel with it."""
    _seed(tmp_path)
    from data.load import load_chain_costs
    out = load_chain_costs(root=tmp_path)
    ok = [p for p in out["provenance"] if p["status"] == "ok"]
    assert len(ok) == len(CHAINS)
    assert all(p["retrieved_utc"] for p in ok)
    assert all(p["endpoint"].startswith("https://") for p in ok)


def test_l1_is_uneconomic_and_l2_is_viable_on_real_shaped_gas(tmp_path):
    """The project's central claim, recomputed from measured prices."""
    _seed(tmp_path)
    from data.load import load_chain_costs
    from src import economics as ec

    out = load_chain_costs(root=tmp_path)
    value = ec.session_value_usd(22.0, 0.48)
    gas = ec.gas_per_session()
    by = {v["name"]: ec.cost_usd(gas, v["gas_price_gwei"], v["token_usd"]) / value
          for v in out["venues"]}

    assert by["Ethereum L1"] > 0.05, "L1 settlement should swamp session value"
    assert by["Base"] < 0.05, "an L2 should leave settlement a small overhead"
    assert by["Arbitrum One"] < by["Ethereum L1"]
    # Polygon's high gwei is priced in a cheap token, so unit-mixing would
    # rank it wrongly.
    assert by["Polygon PoS"] < by["Ethereum L1"]


def test_afdc_pricing_parser_handles_the_free_text_it_really_gets(tmp_path):
    f = datakit.Fetcher(tmp_path)
    (f.raw / "afdc").mkdir(parents=True, exist_ok=True)
    stations = {"fuel_stations": [
        {"ev_pricing": "$0.48/kWh"},
        {"ev_pricing": "0.56 per kWh"},
        {"ev_pricing": "$0.31 /kWh; $1.00 session fee"},
        {"ev_pricing": "Free"},
        {"ev_pricing": "Variable pricing, see network app"},
        {"ev_pricing": ""},
        {"ev_pricing": "$48/kWh"},          # a stray decimal, not a tariff
    ]}
    (f.raw / "afdc" / "stations-ca.json").write_bytes(json.dumps(stations).encode())

    from data.load import load_session_value
    median, detail = load_session_value(root=tmp_path)
    assert detail["n_priced_per_kwh"] == 3
    assert detail["n_free"] == 1
    assert detail["n_unparsed"] == 3        # variable, empty, and the $48 outlier
    assert median == pytest.approx(0.48)


def test_no_parseable_price_returns_none_rather_than_a_guess(tmp_path):
    f = datakit.Fetcher(tmp_path)
    (f.raw / "afdc").mkdir(parents=True, exist_ok=True)
    (f.raw / "afdc" / "stations-ca.json").write_bytes(
        json.dumps({"fuel_stations": [{"ev_pricing": "Free"}]}).encode())
    from data.load import load_session_value
    median, detail = load_session_value(root=tmp_path)
    assert median is None
    assert detail["status"] == "no parseable per-kWh prices"
