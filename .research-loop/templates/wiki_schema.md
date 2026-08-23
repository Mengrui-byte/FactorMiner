# Research Loop Wiki Schema

The wiki is a Markdown knowledge base maintained by Codex. Stable claims must have an experiment revision and raw evidence.

## Claim Levels

- `draft`: Useful observation without full evidence or reproduction.
- `candidate`: Evidence exists, but replication or audit is incomplete.
- `stable`: Backed by at least one experiment revision and raw evidence.
- `contradicted`: Conflicts with newer or stronger evidence.

## Stable Claim Format

Use one claim per line in `claims.md`:

```text
- status=stable evidence=experiment:<experiment_id>#rev:<revision> raw:<workdir>/raw/<experiment_id>/<revision>/<file> claim=<short claim>
```

## Required Evidence

- Experiment revision manifest exists.
- Raw evidence path exists and is immutable.
- Metrics or logs are linked from the revision manifest.
- Any contradiction is linked from `contradictions.md`.

## Audit Rule

`dl_loop wiki audit` reports stable claims without evidence. Use `--fix` to downgrade unsupported stable claims to draft.
