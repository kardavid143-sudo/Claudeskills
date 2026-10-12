# PMU Swarm

An installable skill and plugin for **Claude Code and Codex** that organizes complex work into small Project Management Units. Each PMU has specialist responsibilities and a distinct approach to the user's goal. Teams compare plans, coordinate execution, and combine verified contributions into one usable result.

## How it works

1. Clarify missing goal, intent, inputs, allowed sources, and acceptance criteria once.
2. Form task-specific PMUs from a seven-role base: Team Lead, Programme Implementation, M&E/RBM, MIS/Data Analytics, Government/Stakeholder Coordination, Capacity Building, and Documentation.
3. Develop independent approaches, then divide execution into accountable subtasks.
4. Coordinate using hierarchical, star, bounded mesh, or adaptive communication.
5. Track atomic claims, dependencies, expiring leases, retries, call ceilings, artifact hashes, and audit events in local SQLite.
6. Review independently, resolve findings, and assemble a coherent final deliverable.

Use technical adaptations such as Explorer, Architect, Coder, Researcher, and Reviewer when the task calls for them. Activate only relevant roles; seven roles do not require seven concurrent agents.

Default modes: **Lean** — one PMU/up to 6 agent calls; **Standard** — two PMUs/up to 12 calls; **Deep** — three PMUs/up to 20 calls. Host concurrency limits still apply. Simple tasks use lightweight models only when the host exposes them. There are no extra API keys or Python packages required by this plugin.

## Install in Claude Code

Run inside Claude Code:

```text
/plugin marketplace add kardavid143-sudo/Claudeskills
/plugin install pmu-swarm@david-kar-skills
```

Start a new session or reload plugins, then invoke:

```text
/pmu-swarm:pmu-swarm Design a practical monitoring framework. First clarify any missing goal, intent, inputs, and allowed sources. Use two PMUs.
```

For an unnamespaced `/pmu-swarm`, install the standalone skill instead (see below).

## Install in Codex

Add this repository as a marketplace:

```sh
codex plugin marketplace add kardavid143-sudo/Claudeskills --ref main
```

In a supported local Codex/ChatGPT desktop client, select **David Kar Skills** in the Plugins directory and install **PMU Swarm**. Marketplace availability varies by client. The standalone skill is the fallback for a client without plugin installation.

Invoke the installed skill from the skill picker or ask:

```text
Use $pmu-swarm to complete this task with two small specialist PMUs. Goal: … Intent: … Inputs: … Allowed sources: … Acceptance criteria: …
```

## Standalone skill installation

Clone the repository, then copy `plugins/pmu-swarm/skills/pmu-swarm` into the appropriate user skill directory:

| Host | Destination |
| --- | --- |
| Claude Code | `~/.claude/skills/pmu-swarm` |
| Codex | `~/.agents/skills/pmu-swarm` |

On Windows, `~` means your user profile directory. Restart the host after copying. Choose either plugin installation or standalone installation to avoid duplicate skills. To update, pull the repository and replace the installed skill copy after preserving any local modifications.

## Requirements and limits

Python 3.9+ is required for the optional local SQLite ledger. Real parallel teams require native agent delegation in the host. Without it, the skill performs sequential role passes and labels them as a simulation. Model selection, messaging, web/local-memory access, and persistent storage depend on the host's actual tools and permissions. The ledger does not itself launch agents or enforce provider token billing. The skill does not contact external recipients without user authorization.

Run data stays outside the plugin installation and is excluded from this repository. Do not commit user inputs, private sources, or runtime databases. SQLite coordination assumes one host and a local filesystem.

## Verification

```sh
python -m unittest discover -s tests -v
```

Tests cover race-free claims, budgets, dependency gates, expired-worker fencing, pause/resume, independent review requirements, stale reports, snapshots, and completion. Package tests verify manifests and skill paths. Native installation in each user's Claude/Codex client remains a client-side smoke test; repository publication is not marketplace-directory approval.

## References

- [Arena](https://github.com/Jakeschincariol/arena-skill): independent approaches, critiques, and written review criteria inspired this design. This package contains original code and instructions, with cooperative synthesis replacing bracket elimination.
- [Swarm Skills paper](https://arxiv.org/html/2605.10052v1): role/workflow/bounds separation and progressive disclosure informed the architecture. This package does not claim full schema conformance or empirically proven cross-host equivalence.
- [Claude plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Codex skill locations](https://learn.chatgpt.com/docs/build-skills)

MIT License. Copyright 2026 David Kar.
