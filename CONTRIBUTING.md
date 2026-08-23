# Contributing

Keep changes inside the independent `rsi_harness` contracts. Do not copy code,
tests, data, or documentation from another repository. Reuse a public algorithm
only by writing an independent implementation and recording its source or
mathematical definition in the owning document.

Before submitting a change:

```bash
uv run ruff check rsi_harness
uv run pytest
git diff --check
```

Do not add broker integrations, credentials, live execution, or test-period
selection logic.
