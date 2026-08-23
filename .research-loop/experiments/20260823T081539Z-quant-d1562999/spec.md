# Experiment Spec

Experiment ID: 20260823T081539Z-quant-d1562999
Initial revision: 1
Created at: 2026-08-23T08:15:39+00:00
Lanes: quant
Objective: Validate causal RSI evaluator and governed recursive campaign state

## Hypothesis

State the research hypothesis before running the experiment.

## Offline Boundary

- No live trading.
- No broker API access.
- No secret or auth file reads.
- Large data stays in place; only fingerprints are recorded.

## Planned Command

```bash
# planned offline research loop for 0.1h lanes=quant
```

## Data Sources

List paths, time ranges, schemas, and any known caveats.

## Success Criteria

Define metrics, acceptance thresholds, and failure conditions.

## Audit Notes

Record leakage checks, overfitting risks, reproducibility gaps, and data changes.
