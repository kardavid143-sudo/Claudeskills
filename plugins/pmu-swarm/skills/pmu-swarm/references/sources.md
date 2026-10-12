# Provenance and limits

- Jake Schincariol, Arena: https://github.com/Jakeschincariol/arena-skill ; inspected README and `skills/arena/SKILL.md` on 2026-10-12. Use its general patterns of independent strategies, critique/revision, written rubric, isolated artifacts, and resumable bookkeeping. Replace tournament elimination with specialist coordination/synthesis. Instructions and code here are original; no Arena code/cards are copied.
- openJiuwen Team and Gaoling School of Artificial Intelligence, *Swarm Skills: A Portable, Self-Evolving Multi-Agent System Specification for Coordination Engineering*, arXiv:2605.10052v1, 11 May 2026: https://arxiv.org/html/2605.10052v1 . Relevant: sections 5 (roles/workflows/bounds/dependencies), 5.3 (runtime responsibilities), 6 (evolution), 7 (compatibility/degradation). Its cross-runtime claims use architecture and a qualitative case; section 7.2 leaves large-scale empirical conformance to future work.

Treat the paper as design input, not proof this works on every host. Keep standard name/description frontmatter; express coordination in body/references. This is an adaptation, not a certified full Swarm Skills schema implementation. Keep run-local lessons rather than automatically applying self-evolving patches.

Implemented: instructions, roles, topology/routing policies, rubric, and local SQLite ledger with atomic claims, leases, dependency gates, bounded attempts/calls, audit events, snapshots/hashes.

Runtime-dependent: spawning, peer messaging, model overrides, token/cost measurements, filesystem sandboxing, persistent runs, vector memory. Do not claim these merely because described. Use SQLite on one host/local filesystem, not a live WAL database across machines/network mounts. Persist run state with SQLite backup after stopping writers.
