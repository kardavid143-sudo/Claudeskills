# Coordination and resource control

## Topology

| Topology | Use | Route | Bound |
| --- | --- | --- | --- |
| Hierarchical | Multiple PMUs/dependent streams | Worker → Lead → Director; decisions back down | Default across PMUs; Lead consolidates blockers |
| Star | Small unit, separable specialties | Lead ↔ each specialist | Default within PMUs; no uncontrolled broadcasts |
| Mesh | Coupled design/data interfaces | Named peers exchange interface note and response | One exchange per named pair per review round; log unresolved conflicts |
| Adaptive | Stalled dependency/redundant coordination | Director changes routing | Log old/new topology, trigger, scope, expected benefit; preserve task IDs and permissions |

A topology is an orchestration policy, not a network created by naming it. Without peer tools, relay compact notes through the director and disclose that. Avoid all-to-all transcripts. Keep initial independent plans separate; share evidence/interfaces afterward to avoid repeated retrieval.

## Team and model selection

Use Lean for one tractable output, Standard for multiple plausible approaches, and Deep/user-defined units for separable evidence, build, and handover streams. Each lens must change real sequencing or tradeoffs: evidence-first, implementation-first, systems-design, stakeholder-use, or risk/verification. Do not execute the full task redundantly after independent plans if shared execution suffices.

Create a run-local model table: task, complexity, error consequence, available/selected model, escalation trigger, actual usage. Lightweight: extraction, conversion, deduplication, bookkeeping. Stronger: architecture, conflicting evidence, causal/indicator design, final review, synthesis. Honor user-selected providers. Use host defaults where overrides are unavailable. Do not create subscriptions/accounts. Verify pricing only if computing cost. Token estimates are planning aids, not provider-enforced limits. Aggregate actual units or report unknown; measured savings require a baseline.

Estimate calls as plans + implementation + reviews + bounded rework, including follow-ups/nesting. Reserve at least one final review call and generally 20–25% for review/rework. Reduce roles if the ceiling is insufficient. Stop at the hard limit; failures count unless no call is proven to have occurred.

## Context, sources, state

Keep one mandate/ledger per run. Source IDs include URL/path, version/date, excerpt/location, access time, and supported claims. Cache once when permitted. Read shared evidence concurrently but isolate artifact writes. Enforce filesystem permissions in the runtime where available; the tracker cannot stop arbitrary shell writes outside assigned paths.

The director alone mutates the graph and accepts outputs based on review receipts. Agents claim assigned tasks atomically, heartbeat live leases, and submit within scope. Do not edit SQLite manually. Dependencies must be accepted before execution. Hashes detect later changes; they do not prove truth.

Use receipts/accepted artifacts for shared context. Avoid whole-conversation forks by default. Never describe serial personas as independent agents or retain private chain-of-thought.

## Recovery

On user stop, interrupt live calls where supported, pause, preserve artifacts, and report state. Recheck authorization and brief freshness before resume. Pause invalidates running tokens and requeues tasks; attempts/calls remain counted. Cancelled/completed runs are terminal. Changed briefs require fresh runs and revalidation of reused work.

On failure, record it, retry within limits, or block; dependents remain pending. Carry source uncertainty into the final result. Ask essential input questions centrally while doing independent work.
