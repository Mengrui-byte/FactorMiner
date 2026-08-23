# FactorMiner RSI Recursive Research

FactorMiner is an offline, research-only system for recursively improving an
RSI factor research workflow. It connects three explicit boundaries:

```text
DeepSeek Harness -> research planner / delegation
DigitalScholar   -> sourced knowledge, novelty, and orientation
RSI Harness      -> causal evaluation, evidence, budget, and generation ledger
```

The agent may propose a new operator, workflow, or skill, but it cannot promote
the change by itself. Promotion requires unit tests, no-lookahead checks, and a
blind benchmark against the parent generation. The system does not connect to
brokers, route orders, or perform live trading.

## Quick start

```bash
uv sync --extra mcp
uv run rsi-research start --dataset-hash local-demo-v1
uv run rsi-research status
```

Run a bounded experiment over a CSV with a `close` column:

```bash
uv run rsi-research run \
  --data data/example_close.csv \
  --train-end 6 \
  --validation-end 8 \
  --test-end 10
```

The run writes a JSON campaign ledger under `artifacts/campaign.json` and
content-addressed evidence packs under `artifacts/evidence/`. Selection uses
validation Sharpe only; the test split is reported after the family is frozen.
Signals at time `t` are applied to returns from `t` to `t+1`, and transaction
costs are explicit.

## Architecture

- `rsi_harness/backtest.py`: causal Wilder RSI, forward-return evaluation,
  costs, drawdown, turnover, and split metrics.
- `rsi_harness/campaign.py`: generation ledger, alpha budget, evidence links,
  capability proposals, and benchmark gate.
- `rsi_harness/agent.py`: deterministic bounded planner plus a JSON contract for
  delegating hypothesis generation to DeepSeek Harness.
- `rsi_harness/knowledge.py`: a deterministic knowledge-snapshot adapter. In
  production the snapshot is supplied by DigitalScholar through Harness.
- `rsi_harness/mcp_server.py`: MCP tools for campaign status, bounded RSI runs,
  and capability review.
- `factorminer/`: reusable typed factor DSL and numerical execution kernel.

## Harness integration

The portable overlay is [`cordis.patch.yml`](cordis.patch.yml). It is the one
production integration path: Harness starts both MCP servers and coordinates
their calls. Configure the paths in the Harness host environment before
applying it:

```bash
export FACTORMINER_ROOT="$PWD"
export DIGITALSCHOLAR_ROOT=/path/to/DigitalScholar
export DIGITALSCHOLAR_PYTHON=python
dsh web --patch "$PWD/cordis.patch.yml"
```

The Harness calls DigitalScholar's `search` and `novelty` tools first, then
passes their results as `knowledge_snapshot` and `novelty` to the RSI
Harness `run_rsi` tool. The RSI tool never starts a second DigitalScholar
client. `DEEPSEEK_HARNESS_COMMAND` can optionally point to a JSON-in/JSON-out
planner for hypothesis generation. Its input contains the generation, knowledge
results, dataset fingerprint, split boundaries, and cost assumptions. The output must be
`{"hypotheses": [{"hypothesis_id": ..., "window": ..., "lower": ..., "upper": ...}]}`.
If it is unset, the deterministic pre-declared RSI family is used.

## Research rules

Every campaign records the dataset fingerprint, timestamp split, trial count,
cost assumption, evidence IDs, anomalies, and remaining alpha budget. Failed
hypotheses remain in the ledger and can seed a capability proposal. Knowledge
claims remain drafts until their source and experiment evidence are reviewed.

This repository is for offline quantitative research only. It deliberately does
not contain live execution, broker credentials, order routing, or portfolio
deployment code.
