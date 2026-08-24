# Generation Protocol

Each campaign generation is identified by:

```json
{
  "campaign": "rsi-recursive",
  "generation": 0,
  "parent_generation": null,
  "knowledge_snapshot_hash": "sha256:...",
  "operator_registry_hash": "sha256:...",
  "skill_version": "rsi-research@1",
  "dataset_hash": "sha256:...",
  "trial_count": 0,
  "alpha_spent": 0.0,
  "alpha_budget_total": 0.01,
  "alpha_budget_remaining": 0.01,
  "result_ids": [],
  "anomalies": []
}
```

The next generation may change only after its parent has immutable result IDs and every capability proposal has a benchmark record. A candidate score is not valid if it was measured on the sealed test period while selecting the capability. Each trial must pass the alpha budget gate before computation, and every evidence pack must carry the knowledge snapshot hash, novelty hash, planner version, operator registry hash, frozen trial-family hash, and selection rule.
