# Repository Guidelines

## Research Loop

This repository uses Research Loop for offline DL/Quant experiments.

- Start each loop with `/research-loop <natural-language objective>` when available, or `/research-loop:start <natural-language objective>` as the fallback.
- The slash command is an LLM-driven controller: it must understand the objective, inspect context, plan the next experiment, create a revision, run bounded checks, audit evidence, update wiki drafts, and decide the next iteration.
- Persist loop intent and iteration state in the dedicated workdir queue with `dl_loop loop-plan --repo . --workdir <workdir> --objective "<objective>"`.
- Keep `<workdir>/wiki/index.md` as the research knowledge entrypoint.
- Treat `<workdir>/wiki/claims.md` as evidence-gated: stable claims need experiment revision and raw evidence links.
- Store every experiment revision under `<workdir>/experiments/<experiment_id>/revisions/<revision>/`.
- Keep raw evidence under `<workdir>/raw/`; do not overwrite or delete it.
- Do not run live trading, broker APIs, secret reads, or long GPU jobs without explicit approval.
- Do not commit, push, tag, or apply rollback patches unless the user explicitly asks.

Useful local commands:

```bash
dl_loop doctor --repo . --workdir <workdir> --fix
dl_loop loop-plan --repo . --workdir <workdir> --objective "<objective>" --max-iterations 3
dl_loop run --repo . --workdir <workdir> --hours 8 --lanes dl,quant --dry-run
dl_loop review --repo . --workdir <workdir>
dl_loop wiki --repo . --workdir <workdir> audit
```
