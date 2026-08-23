# DigitalScholar Bridge

Connect the DigitalScholar MCP server as `mcp__scholar__*`. Use `search` and `novelty` before FactorMiner spends any alpha budget. Use `inspire` only to generate mechanism-bearing ideas, not to accept its score as evidence.

After FactorMiner writes a verified Evidence Pack, call `ingest_factor_evidence` with its manifest path. The tool validates the content hash and stages a `result` in the external research workspace. Then use the existing `orient`, `grade`, `promote`, and `generalize` workflow. Curated scholar bundles remain read-only.
