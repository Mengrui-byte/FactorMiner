# Experiment Spec

Experiment ID: {{experiment_id}}
Initial revision: {{revision}}
Created at: {{created_at}}
Lanes: {{lanes}}
Objective: {{objective}}

## Hypothesis

State the research hypothesis before running the experiment.

## Offline Boundary

- No live trading.
- No broker API access.
- No secret or auth file reads.
- Large data stays in place; only fingerprints are recorded.

## Planned Command

```bash
{{command}}
```

## Data Sources

List paths, time ranges, schemas, and any known caveats.

## Success Criteria

Define metrics, acceptance thresholds, and failure conditions.

## Audit Notes

Record leakage checks, overfitting risks, reproducibility gaps, and data changes.
