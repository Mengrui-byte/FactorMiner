# Reproducibility

Every experiment records the exact close-series fingerprint, split boundaries,
RSI window and thresholds, horizon, transaction cost, trial index, generation,
evidence pack ID, knowledge snapshot hash, novelty hash, skill version, planner
version, operator registry hash, frozen trial-family hash, selection rule, and
alpha cost.

Validation selects the candidate. Test metrics are reported only after the
pre-declared family is complete. Each split only includes entries whose complete
forward label remains inside that split; this purges horizon overlap at the
boundaries. Missing prices reset the Wilder warm-up and are excluded from return
metrics. Real datasets should remain outside Git unless their license and
provenance are documented.
