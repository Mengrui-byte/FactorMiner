# Research Loop Wiki

This wiki stores evidence-backed research knowledge for the current repository.

## Entry Points

- Claims: [claims.md](claims.md)
- Failures: [failures.md](failures.md)
- Contradictions: [contradictions.md](contradictions.md)
- Schema: [schema.md](schema.md)
- Drafts: [drafts/](drafts/)
- Active task queue: [../queue/tasks.json](../queue/tasks.json)
- Repo guidance suggestion: [../integrations/AGENTS.suggested.md](../integrations/AGENTS.suggested.md)

## Operating Rule

Stable conclusions require an experiment revision and raw evidence path. Use `dl_loop wiki audit` to verify that evidence chain.

## Agent Loop

The Research Loop slash command is LLM-driven. It should use this wiki and `queue/tasks.json` in the dedicated workdir to decide the next iteration, then record evidence under experiment revisions before promoting knowledge.
