"""Builds website/ from the last demo run."""

from __future__ import annotations

import pathlib

from . import sitekit as sk

ROOT = pathlib.Path(__file__).resolve().parent.parent

META = {
    "name": "Blockchain Shared Charging",
    "slug": "blockchain-shared-charging",
    "repo": "1.0-Secure-Ai-Agent-Infrastructure",
    "pillar": "Secure Digital Infrastructure",
    "tagline": "Escrowed settlement for shared EV charging sessions, and the gas "
               "analysis that decides where it can actually run.",
    "tags": [("Solidity", ""), ("escrow + dispute window", ""),
             ("gas model", ""), ("estimates, not node measurements", "warn")],
    "banner": "The lifecycle results come from an off-chain model that mirrors the "
              "contract's state machine. Gas figures are opcode-level estimates from "
              "the storage layout, not measurements from a node — a real deployment "
              "would replace them with forge gas-report output. Prices are stated "
              "assumptions, not live quotes.",
}


def build_site(results: dict) -> pathlib.Path:
    g = results["gas"]
    a = results["assumptions"]
    lc = results["lifecycle"]
    venues = results["venues"]

    metrics = sk.metric_grid([
        ("Gas per session", f"{g['per_session']:,}", "open + report + settle"),
        ("With a dispute", f"{g['per_session_with_dispute']:,}", "adds one transaction"),
        ("Batched, n=50", f"{results['batching'][4]['gas_per_session_batched']:,}",
         f"{results['batching'][4]['saving_pct']:.0f}% saved"),
        ("Guards upheld", f"{sum(x['rejected'] for x in lc['guards'])}/"
                          f"{len(lc['guards'])}", "invalid operations rejected"),
    ])

    gas_tbl = sk.table(
        ["Call", "Gas (est.)", "What dominates it"],
        [["open", f"{g['open']:,}", "3 cold storage writes; the Session struct packs into 3 slots"],
         ["report", f"{g['report']:,}", "2 storage resets plus cold reads"],
         ["settle", f"{g['settle']:,}", "2 value-bearing calls at 9,000 each"],
         ["dispute", f"{g['dispute']:,}", "one storage reset; only on contested sessions"]],
        numeric_cols=(1,))

    via_tbl = sk.table(
        ["Gas price", "Settlement cost", "Session value", "Overhead", "Under 5%?"],
        [[f"{r['gas_price_gwei']} gwei", f"${r['settlement_cost_usd']:.4f}",
          f"${r['session_value_usd']:.2f}", f"{r['overhead_pct']:.2f}%",
          "yes" if r["viable_under_5pct"] else "no"]
         for r in results["viability"]],
        numeric_cols=(1, 2, 3))

    venue_tbl = sk.table(
        ["Execution layer", "Native", "Per session", "Batched (n=50)",
         "Overhead batched", "Viable"],
        [[r["venue"], r["native_asset"], f"${r['cost_per_session_usd']:.4f}",
          f"${r['cost_batched_usd']:.4f}", f"{r['overhead_batched_pct']:.2f}%",
          "yes" if r["viable_batched"] else "no"] for r in venues],
        numeric_cols=(2, 3, 4))

    batch_chart = sk.bar_chart(
        [(f"n={b['n_sessions']}", b["gas_per_session_batched"])
         for b in results["batching"]], fmt="{:,.0f}")

    guard_tbl = sk.table(
        ["Attempted operation", "Rejected", "Error"],
        [[x["attempt"], "yes" if x["rejected"] else "NO", x["error"]]
         for x in lc["guards"]])

    hp, dp = lc["happy_path"], lc["disputed"]

    body = f"""
<section>
  <h2>The design constraint</h2>
  <div class="stack">
    <p>A charge point is not trusted. It reports the meter reading, so the contract has
    to make an inflated reading either impossible or contestable. Three mechanisms do
    that: the driver's deposit <strong>bounds</strong> the maximum loss, a one-hour
    dispute window makes an over-report <strong>contestable</strong>, and an arbiter can
    correct a contested reading before settlement.</p>
    <p>Settlement writes state before it transfers value. Both parties may be contracts,
    so that ordering is what stops a re-entrant refund from reaching another session's
    escrow.</p>
  </div>
</section>

<section>
  <h2>This run</h2>
  <div class="stack-lg">
    {metrics}
    <p class="mono" style="color:var(--muted);font-size:12.5px">
      generated {sk.esc(results['generated_at'])} &middot;
      assumptions: ETH ${a['eth_usd']:,.0f} &middot; {a['session_kwh']} kWh session
      @ ${a['price_per_kwh_usd']}/kWh &middot; dispute window {a['dispute_window_s']}s
    </p>
  </div>
</section>

<section>
  <h2>Lifecycle</h2>
  <div class="stack-lg">
    {sk.table(["Scenario", "Reported", "Settled at", "Paid to point", "Refunded"],
              [["Happy path", f"{hp['drawn_wh']:,} Wh", f"{hp['drawn_wh']:,} Wh",
                f"{hp['paid_wei']:,} wei", f"{hp['refunded_wei']:,} wei"],
               ["Over-report, disputed", f"{dp['reported_wh']:,} Wh",
                f"{dp['resolved_wh']:,} Wh", f"{dp['paid_wei']:,} wei",
                f"{dp['refunded_wei']:,} wei"]],
              numeric_cols=(1, 2, 3, 4))}
    <p>In the disputed session the point reported {dp['reported_wh']:,} Wh against a
    40,000 Wh deposit. The driver contested inside the window, the arbiter corrected the
    reading to {dp['resolved_wh']:,} Wh, and settlement paid on the corrected figure.</p>
    {guard_tbl}
  </div>
</section>

<section>
  <h2>The finding: this does not work on L1</h2>
  <div class="stack-lg">
    {via_tbl}
    <div class="note">
      <h3>Read the last column</h3>
      <p>A 22 kWh session is worth about
      ${results['viability'][0]['session_value_usd']:.2f}. At 20 gwei, settling it on
      Ethereum mainnet costs
      <strong>${[r for r in results['viability'] if r['gas_price_gwei'] == 20][0]['settlement_cost_usd']:.2f}</strong>
      &mdash; more than the electricity. Even at 1 gwei the overhead is
      {results['viability'][0]['overhead_pct']:.1f}%, above any threshold a charging
      operator would accept.</p>
      <p>Per-session settlement on L1 is not viable at any realistic gas price. That is
      the useful result of this analysis, and it is a negative one.</p>
    </div>
  </div>
</section>

<section>
  <h2>Batching helps, but not enough on its own</h2>
  <div class="stack-lg">
    {batch_chart}
    <p>Batching amortises the 21,000-gas transaction base and the cold storage reads
    across a batch. It cannot amortise the storage writes or the two value transfers per
    session, which is why the saving flattens near
    {results['batching'][-1]['saving_pct']:.0f}% rather than scaling with batch size.
    Halving a cost that is 100% of session value still leaves it unviable.</p>
  </div>
</section>

<section>
  <h2>Where it does work</h2>
  <div class="stack-lg">
    {venue_tbl}
    <div class="note">
      <h3>The conclusion</h3>
      <p>Batched settlement on an L2 costs well under a cent per session &mdash; roughly
      0.03% of session value on Base. The design is sound; the execution layer was the
      problem. Any deployment of this contract belongs on an L2, and the L1 figures are
      kept on this page because the negative result is what justifies that choice.</p>
      <p>Polygon is priced in MATIC rather than ETH, which is why its nominally high gwei
      figure still lands cheap. Mixing the two units in one column without saying so
      would be exactly the kind of comparison that looks rigorous and is not.</p>
    </div>
  </div>
</section>

<section>
  <h2>Reproduce it</h2>
  <div class="stack">
    <pre>cd blockchain-shared-charging
pip install -r requirements.txt
python -m pytest tests/ -q     # 14 tests, including the viability finding
python -m src.demo</pre>
    <p>The contract is <code>contracts/SharedCharging.sol</code>. The Python model in
    <code>src/settlement.py</code> mirrors its state machine so the economics can be
    analysed without a node.</p>
  </div>
</section>

<section>
  <h2>What this does not establish</h2>
  <div class="stack">
    <ul class="tight">
      <li>Gas figures are opcode-level estimates derived from the storage layout. They
      have not been measured against a node, and a compiled contract will differ.</li>
      <li>The Solidity has not been audited, deployed, or fuzzed. The Python model
      passing does not mean the contract is correct.</li>
      <li>Prices are stated assumptions. The viability conclusion is robust to large
      moves in them; the individual dollar figures are not.</li>
      <li>The arbiter is a trusted party. Making dispute resolution trustless is a
      different and much harder design than the one here.</li>
    </ul>
  </div>
</section>
"""
    return sk.build(ROOT, META, body, results)
