# Reproducibility

Every experiment records the exact close-series fingerprint, split boundaries,
RSI window and thresholds, horizon, transaction cost, trial index, generation,
evidence pack ID, knowledge snapshot hash, and skill version.

Validation selects the candidate. Test metrics are reported only after the
pre-declared family is complete. Missing prices reset the Wilder warm-up and are
excluded from return metrics. Real datasets should remain outside Git unless
their license and provenance are documented.
