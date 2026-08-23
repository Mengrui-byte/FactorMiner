# FactorMiner RSI

FactorMiner RSI is an independent, offline research controller for a recursively
self-improving RSI agent. It is coordinated by DeepSeek Harness and uses
DigitalScholar as a knowledge MCP service.

```text
DeepSeek Harness
  -> DigitalScholar: search / novelty / orient
  -> RSI Harness: knowledge snapshot + experiment request
  -> causal RSI evaluation + evidence pack + generation ledger
```

This repository does not contain live trading, broker access, order routing,
third-party factor catalogs, or copied factor-mining engines. It implements the
small research contract needed for the RSI campaign.

## Install and run

```bash
uv sync --extra dev --extra mcp
uv run rsi-research start --dataset-hash local-demo-v1
uv run rsi-research run --data data/example_close.csv --train-end 6 --validation-end 8 --test-end 10
```

Results are written to `artifacts/campaign.json` and content-addressed evidence
packs under `artifacts/evidence/`. The test period is never used to choose a
hypothesis. A signal observed at time `t` is applied only to the return from
`t` to `t+1`, with explicit transaction costs.

## Harness contract

Apply [`cordis.patch.yml`](cordis.patch.yml) in DeepSeek Harness. Harness owns
the only production integration path and starts two MCP servers:

1. DigitalScholar searches the knowledge base and performs novelty checks.
2. RSI Harness receives `knowledge_snapshot` and `novelty`, evaluates a bounded
   pre-declared RSI family, and records evidence.

The RSI process never starts a second DigitalScholar client. The optional
`DEEPSEEK_HARNESS_COMMAND` is a planner adapter with a versioned JSON contract;
when unset, the deterministic six-member RSI family is used.

## Research invariants

- Offline only; no exchange, broker, wallet, or production database calls.
- Timestamp splits, horizon, fees, trial count, and dataset hash are recorded.
- Evidence IDs are SHA-256 hashes of canonical JSON without the ID field.
- Failed hypotheses remain in the ledger as anomalies or capability proposals.
- A proposed capability is not active until checks pass and its score improves
  over the parent benchmark.

See [`docs/reuse-boundary.md`](docs/reuse-boundary.md) for the third-party
source audit and the rules separating reusable research ideas from copied code.
