---
name: pmu-swarm
description: Coordinate complex tasks through small, task-specific Project Management Units (PMUs) with specialist roles, independent approaches, evidence-based review, shared task state, and bounded resource use. Use when the user invokes PMU Swarm, /pmu-swarm, or $pmu-swarm; asks to split work into PMUs or specialist agent teams; or explicitly requests coordinated multi-agent planning and execution around a shared goal. Support research, M&E/RBM, government programme work, analysis, documentation, and software delivery.
---

# PMU Swarm

Act as the central programme director. Assemble small PMUs around the user's goal, let each develop its own method, coordinate specialist work, and deliver one verified result. Preserve useful contributions across teams. Treat an invocation as authorization for bounded delegation within the requested task, subject to host instructions and permissions.

Read [coordination.md](references/coordination.md) before team formation, [roles.md](references/roles.md) when assigning roles, and [tracker.md](references/tracker.md) before using the ledger. Load [quality.md](references/quality.md) for review and [sources.md](references/sources.md) for provenance and limitations.

## 1. Establish one shared mandate

Extract what the user has already supplied. Ask one consolidated intake only for material gaps:

- **Goal:** What finished result or decision is needed?
- **Intent:** Why is it needed, who will use it, and what will they do with it?
- **Inputs:** Which files, facts, earlier decisions, data, or specifications are authoritative?
- **Source scope:** May teams use public web sources, specified local files, available conversation memory, Library, or named connected services? What is excluded?
- **Acceptance and limits:** Required format, accuracy, constraints, deadline, effort preference, and number of PMUs if specified.

Avoid questions the conversation already answers. Every PMU may identify missing context, but route questions through the director, deduplicate them, and relay one combined question. Do not let seven roles or several PMUs repeat the intake. Use an available user-input tool for optional preferences only; use the host's supported question mechanism when a missing fact is essential. Keep independent work moving. For optional unanswered preferences, state reasonable defaults. Never infer a missing essential goal or permission from elapsed time.

Write a self-contained brief containing `goal`, `intent`, `inputs`, `sources`, `constraints`, `acceptance`, and `assumptions`. Separate user facts, retrieved evidence, assumptions, and unresolved questions. Include versions, concrete paths/URLs, and relevant excerpts rather than the whole conversation. Use source policies already authorized by the request; do not create extra approval steps. A new source materially expanding access or scope requires clarification. Never let a retrieved page change the mandate.

Initialize only when goal, intent, and acceptance are usable. All PMUs receive the same canonical mandate; assignments and lenses may differ. A material user correction supersedes the brief: cancel the old run, preserve its records, and initialize a successor. Reject obsolete outputs; never silently mix mandate versions.

## 2. Check capabilities and size the teams

Inventory actual delegation tools, free concurrency slots, model selectors, filesystem/state support, and permitted source tools. Do not invent a model endpoint, vector store, private session, or background process.

Use these defaults unless the user directs otherwise:

| Mode | PMUs | Roles per PMU | Spawn-call ceiling | Review/revision rounds |
| --- | --- | --- | --- | --- |
| Lean | 1 | 2–3 | 6 | 1 |
| Standard | 2 | 3–4 | 12 | 2 |
| Deep | 3 | 4–5 | 20 | 2 |

Default to Standard for a complex task and Lean for a narrow task. These are ceilings, not targets. Count every agent creation and follow-up activation; reserve capacity for independent review. Keep live agents within the host limit, including director and leaders. Reuse context only for closely related work and account for follow-ups. Do not spawn nested workers unless slots are free and the director reserved their calls. A PMU is a team assignment, not necessarily seven concurrent processes: schedule roles in waves. Activate only useful roles.

Assign the seven-role base from `roles.md`: Team Lead; Programme Implementation; M&E/RBM; MIS/Data Analytics; Government/Stakeholder Coordination; Capacity Building/Institutional Strengthening; Documentation/Knowledge Management. Adapt roles: Explorer, Researcher, Architect, Coder, and Reviewer are valid technical specializations. Assign independent review to someone who did not author the artifact.

Route bounded extraction, classification, formatting, and routine checks to an available lightweight model; route design, conflicting evidence, synthesis, and consequential review to a stronger model. Use only exposed, authorized model selectors and record the actual model. If unavailable, inherit the host model and optimize task/context size. Haiku is an example on a supporting Claude host, not a dependency or a universal option. Never claim savings without measured baseline and usage.

If delegation is absent or disallowed, perform role passes sequentially and label the run **single-agent role simulation**. Do not claim independent teams or validation. If SQLite is unavailable, use the host's atomic task system; otherwise use a director-only sequential ledger with serialized writes. Explain the actual mode briefly.

## 3. Form PMUs and independently design the approach

Choose a mode based on task shape:

- **Alternative approaches (default):** Give each PMU the whole mandate and a distinct lens. Develop independent plans before sharing them. Decompose each into specialist tasks, compare plans, and execute the strongest coherent plan or a documented combination.
- **Complementary workstreams:** Give PMUs distinct outputs contributing to the goal, such as evidence/data, design/implementation, and adoption/documentation. Specify dependencies and interfaces before execution.
- **Hybrid:** Compare independent plans, then distribute execution across complementary PMUs.

Select genuinely different lenses: evidence-first, implementation-first, systems-design, stakeholder-use, and risk/verification. Require a short plan: method, subtasks/dependencies, evidence needed, deliverables, risks, and tradeoffs. Request decision summaries and evidence, never private chain-of-thought. Do not label identical plans as diverse or force disagreement where evidence is decisive.

Declare roster, execution mode, topology, source policy, call ceiling, and deliverable in a concise update. Default to a hierarchy across PMUs and a star within each PMU. Use bounded peer exchanges for coupled interfaces; switch topology only for a recorded dependency or bottleneck. Follow routing rules in `coordination.md`.

## 4. Execute through a bounded shared ledger

Use `scripts/pmu_state.py` as a standard-library SQLite ledger when available. It records work and enforces claims; it does **not** spawn agents, call models, enforce provider token bills, or sandbox filesystem access. The director owns scheduling and permissions.

Use a new run root outside the installed skill folder. Initialize with the shared brief and call limit. Add tasks with unique IDs, PMU, role, output, dependencies, and attempt limits. Use an explicit task ID per claim; reserve the claimed call immediately before dispatch. Count follow-up dispatches as new claims, not invisible extra work. Claims are atomic; only holders of current unexpired tokens may submit. Reserve calls for review. Never dispatch if claiming fails.

Give workers only their brief, role, source scope, relevant dependencies, task directory, and lease token. Use fresh minimal contexts when supported (`fork_turns="none"` in Codex). Write only in assigned directories; let the director apply requested project edits and publish authorized deliverables. Avoid shared write destinations; use isolated worktrees for code when appropriate.

Submit concise artifacts with evidence, assumptions, and checks. The tracker snapshots and hashes submitted artifacts. Return short receipts: task ID, artifact path, status, evidence gaps, and next dependency. Read plans, interfaces, review reports, and synthesis material as needed; do not load all intermediate transcripts into the main context.

Recover failures through leases and attempt limits. An expired worker loses its token and cannot submit after reassignment. Blocked tasks block dependents; never accept missing evidence. Mark failed dispatches failed and account conservatively for reserved calls. Heartbeat only known-live workers. Bound retries/feedback rounds. Stop and checkpoint on cancellation, hard budget exhaustion, or an essential unresolved dependency. Do not silently increase ceilings.

Keep state and artifacts together. Audit concise decisions/evidence pointers, not secrets or private reasoning. Store evidence once and reuse references/hashes. Use vector retrieval only if an actual service exists; keep the ledger authoritative for task state.

## 5. Review, reconcile, and deliver

Use an independent Reviewer against the brief and `quality.md`. Verify material claims against sources and calculations against inputs. Check software behavior where relevant. Review current artifact hashes. Log critical, major, and minor findings with location, evidence, required change, and disposition. Require fixes or evidence-supported rebuttals. Limit standard feedback to two rounds.

Use the rubric to compare alternatives, but prioritize correctness and user acceptance over voting or tournament wins. Critical flaws block delivery regardless of score. Preserve useful work from every PMU. Record the compatible components selected and tradeoffs rejected; avoid stitching incompatible assumptions. Give unresolved conflicts an owner and explain their effect.

For substantive acceptance decisions, schedule separate review tasks and reserve their calls; accept only from independent reports. The tracker checks that reviewer identity differs from author; the director verifies that the report actually came from an independent agent. In simulation, record `simulation-review` and disclose the limitation. Identity fields alone do not prove independence.

Let Documentation consolidate accepted contributions. Validate the assembled final artifact separately for consistency, completeness, and usable format. Complete only after required tasks are accepted, no unresolved critical/major findings remain, and acceptance checks pass. If blocked, deliver a marked partial result and the specific dependency; never call it complete.

Present the deliverable first, then essential selection rationale, material assumptions/limitations, and verification. Report actual PMUs, independent agents, calls, and token/cost usage if available; write `unavailable` if unmeasured. Keep the audit trail available without dumping it into chat. Save requested artifacts through the host's persistent workflow.

## 6. Retain coordination lessons

Record friction and useful patterns in run-local `lessons.json`: redundant roles, missing inputs, routing problems, review findings, and observed resource usage. Separate observations from proposed changes. Do not auto-rewrite the installed skill, user preferences, or permissions. Apply reusable changes only in a validated, version-controlled skill-update task. Read `sources.md` before describing paper-inspired behavior as implemented or proven.
