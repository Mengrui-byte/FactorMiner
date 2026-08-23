# Architecture

The system has four independent boundaries:

1. **Harness orchestration**: DeepSeek Harness calls knowledge and research
   tools and holds the agent prompt/delegation policy.
2. **Knowledge snapshot**: DigitalScholar returns sourced search and novelty
   results. The RSI process receives data, not filesystem access to the KB.
3. **Research kernel**: `rsi_harness.backtest` computes causal Wilder RSI and
   split metrics over an explicitly supplied close series.
4. **Governance state**: `campaign` and `evidence` persist generations, budgets,
   hypotheses, failures, and immutable result IDs.

No boundary imports a third-party factor-mining engine. MCP only exposes the
bounded operations needed by this project: campaign status/start, RSI run,
capability proposal, and capability benchmark.
