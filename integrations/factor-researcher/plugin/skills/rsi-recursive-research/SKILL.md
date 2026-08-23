---
name: rsi-recursive-research
description: Run a guarded, recursively self-improving RSI research campaign across DigitalScholar and FactorMiner. Use when starting or advancing RSI research generations, turning failed RSI experiments into anomalies or capability proposals, validating new RSI operators or skills, or integrating evidence into the knowledge graph. Never use it to place trades or to bypass frozen test sets.
---

# RSI Recursive Research

Use RSI as a bounded research domain. The goal is not to optimize RSI(14), 30, and 70; it is to improve the research system from evidence while preserving an honest test boundary.

## Required order

1. Read the current campaign status and orientation.
2. Query DigitalScholar for `time-series-momentum-reversal`, regimes, liquidity, costs, and RSI-adjacent concepts.
3. Run novelty before spending experiment budget. `KNOWN` means reject or state a precise difference; `PARTIALLY-KNOWN` means attach the prior concept; `NOVEL` still requires a mechanism.
4. Write 1–3 falsifiable hypotheses. Each must specify the RSI formula, horizon, state condition, target, null model, cost, train period, test period, and expected failure mode.
5. Freeze the complete trial family before computation. Count every threshold, window, prompt, model, seed, universe, and restart as a trial.
6. Use FactorMiner's deterministic DSL and evidence protocol. RSI uses the verified Wilder `RSI`/`RMA` operators; do not implement a private indicator in a prompt or notebook.
7. Record both survivors and failures. A failure diagnosis is a research result and may seed the next generation.
8. For a missing capability, create a proposal only. A proposal is not active until unit tests, no-lookahead checks, and a blind benchmark against the parent pass.
9. Advance the generation only after the evidence pack, knowledge snapshot, operator registry, skill version, dataset hash, trial count, and alpha spend are recorded.

## Permitted recursive changes

- `knowledge`: add a sourced concept, anomaly, finding, or typed graph edge through the DigitalScholar research workflow.
- `operator`: propose a new DSL operator or a correction to an existing one. Require prefix invariance, missing-data tests, CPU/reference agreement, and a fixed benchmark.
- `skill`: propose a prompt/workflow change. Require a held-out task set and no regression on the parent benchmark.
- `workflow`: propose a change to retrieval, delegation, or budget policy. Require the same frozen campaign family and lower/equal cost.

The agent must not directly edit production operator code, alter the alpha budget, move the test period, change the evidence gate, or promote a discovery. Human approval remains required for repository-level promotion.

## RSI seed family

Start with the canonical Wilder implementation:

```text
RSI($close, 14)
```

Allowed first-generation variations are mechanism-driven, not an unconstrained grid:

```text
RSI($close, window)
Delta(RSI($close, window), lag)
duration spent below/above a threshold
RSI conditioned on a pre-declared volatility or liquidity regime
RSI combined with open-interest or order-flow state
```

Do not select the sign, threshold, or horizon on the held-out test period. Compare against buy-and-hold, raw momentum/reversal, and a cost-aware no-signal baseline.

## Stop conditions

Stop the campaign when the alpha budget is exhausted, no open anomaly remains, or the next capability proposal fails its benchmark. Emit a frontier report instead of manufacturing more hypotheses.

## MCP tools

Expected DigitalScholar tools: `search`, `inspire`, `novelty`, `orient`, `grade`, `promote`.

Expected FactorMiner tools: `recursive_campaign_start`, `recursive_campaign_status`, `recursive_capability_propose`, `recursive_capability_benchmark`, `recursive_generation_advance`, `helix_mine`, `evaluate_library`.

Read [generation-protocol.md](references/generation-protocol.md) for the JSON state contract and [rsi-operator-contract.md](references/rsi-operator-contract.md) for the deterministic RSI requirements.
