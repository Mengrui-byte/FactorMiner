# Research Loop Safety Policy

Research Loop defaults to offline, auditable experimentation.

## Always Allowed

- Create or update manifests, reports, task queues, and wiki drafts inside the dedicated Research Loop workdir.
- Fingerprint datasets by path, size, mtime, schema hints, and bounded hashes.
- Record Git commit, branch, dirty status, and dirty diff evidence.
- Generate rollback and reproduction plans.

## Requires Explicit User Approval

- Long GPU jobs.
- Applying rollback patches to user code.
- Committing, pushing, tagging, or publishing.
- Adding external services such as DVC remotes, MLflow tracking servers, or W&B projects.

## Disallowed Defaults

- Live trading or broker API calls.
- Reading secrets, `.env`, credential stores, or `auth.json`.
- Deleting workdir raw evidence, wiki history, or experiment revision records.
- Copying large datasets into Git by default.
