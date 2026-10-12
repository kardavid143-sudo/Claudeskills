# SQLite ledger operation

Use Python 3.9+ and a local filesystem. Resolve `scripts/pmu_state.py` relative to this skill directory. Substitute concrete paths for the examples below. All JSON input goes through stdin; do not build shell commands from untrusted task text. IDs accept letters, digits, underscores, and hyphens. Every command returns JSON, and errors return exit code 1. Call `--help` for syntax.

## Initialization and tasks

Initialize at a path whose parent directory does not exist, such as `<workspace>/pmu-runs/<unique-id>/state.sqlite`. Do not place run data in the installed skill or publish private task artifacts in the plugin repository.

```sh
python3 <skill>/scripts/pmu_state.py --db <new-run>/state.sqlite init --call-limit 12 < brief-input.json
```

Brief input:

```json
{
  "goal": "Produce the requested deliverable",
  "intent": "Support the intended audience's decision",
  "inputs": [{"path": "input-path", "version": "version-or-date"}],
  "sources": {"web": false, "memory": "relevant available context only", "local": ["input-path"]},
  "constraints": ["User requirements"],
  "acceptance": ["Concrete completion check"],
  "assumptions": []
}
```

The script freezes exact normalized brief bytes and SHA-256. Verify current source versions separately. Changing the brief requires a successor run, not direct edits.

Add tasks in dependency order (`add` reads this JSON from stdin):

```json
{"id":"draft","pmu":"A","role":"Analyst","title":"Build result","acceptance":["Matches brief"],"kind":"work","dependencies":[],"required":true,"max_attempts":3}
```

Supported kinds: `plan`, `work`, `review`, `final`. Dependencies must already exist. Ordinary tasks require accepted dependencies; review tasks may depend on submitted artifacts, avoiding an acceptance deadlock.

## One work/review cycle

1. `claim draft --worker author-1 --ttl 900 --model host-default` reserves one call. Keep the returned token and task scope. Dispatch exactly once for that claim. A fresh follow-up is another task/attempt and another claim.
2. Author writes a nonempty artifact inside returned scope. `submit draft --worker author-1 --token <token> --artifact <absolute-file>` snapshots it. Heartbeat with the same owner/token before expiry if the worker remains alive. `fail` records a failed attempt and requeues or blocks it.
3. Add task `check-draft`, kind `review`, dependencies `["draft"]`. Claim with a different worker. This reserves the review call and records exact input hashes. The reviewer reads the submitted snapshot and brief, writes findings into its own scope, then submits `check-draft`.
4. First, the director adjudicates `check-draft`: `review check-draft --reviewer director --decision accept` with a note/unresolved list on stdin. This closes review reports without recursive reviews-of-reviews. Then accept or request revision of `draft` using `review draft --reviewer reviewer-1 --report check-draft --decision accept` and stdin `{"note":"Verified against source and requirements","unresolved":[]}`. For each unresolved finding provide `severity` (`critical`, `major`, `minor`) and `description`. Critical/major findings block acceptance. `revise` requeues within attempt limits; `reject` blocks. A revised artifact requires a new review task/hash-matched report.
5. Director adjudication is bookkeeping, not a new model call. Validate report quality and actual independent provenance; a different identity string alone is not proof. Rejected or not-yet-accepted reports cannot authorize target acceptance.
6. Add dependent assembly/final tasks only as needed; run a separate review of the final assembly. Do not create a recursive infinity of reviews-of-reviews: director adjudication closes review reports.

Current limitations: state transitions and hashes are deterministic, but content quality, rubric arithmetic, reviewer provenance, and model invocation remain the host's responsibility. Trusted collaborators can call the CLI; it is not an authorization boundary against malicious local users.

## Recovery and audit

- `status`: state, calls, tasks, expiry flags, current artifacts; hides tokens.
- `events`: ordered append-only coordination audit (no tokens).
- `pause`: invalidates running leases and requeues within attempt limits. Interrupt host agents separately.
- `resume`: reactivates a paused run; does not restore obsolete tokens.
- `cancel`: makes run terminal. Interrupt host agents separately.
- `complete`: reads `{"passed":true,"note":"Acceptance checks passed","unresolved":[]}` from stdin; requires every required task accepted and valid artifact hashes, with no live workers.

Expiration is swept and committed before each claim transaction. A competing claim cannot steal a live task. Failed claims roll back without consuming calls; expired tokens cannot submit. Failed dispatched calls and paused attempts remain counted. Ceilings are fixed per run; stop rather than silently inflating them. The tracker handles call reservations, not measured token billing. Store actual model usage separately when exposed by the host.

Submitted snapshots are unique files under `submissions/<task>/`; later changes to a working draft do not alter a submission. Direct snapshot changes cause hash failure at acceptance/completion. Crashes can leave unreferenced snapshot files; preserve them for diagnosis, but only ledger-referenced files count as submitted. Reinitialize rather than reuse a half-created run after initialization failure.

Stop writers before backup. Use Python `sqlite3.Connection.backup()` for the database and copy the brief/artifacts with their relative layout. Do not copy only `state.sqlite` while WAL writers are live. If moving the run, absolute artifact paths require an explicit validated migration; ordinary resume expects the original run path.
