# Review and synthesis

Set task-specific acceptance before comparing plans. Apply the same rubric to all alternatives; change only when the mandate changes.

| Criterion | Weight | Evidence |
| --- | --- | --- |
| Correctness and evidence | 30 | Source support, calculations/logic, behavior checks |
| Goal/intent and requirements | 25 | Material requirements and intended use |
| Feasibility and usable detail | 20 | Implementation, interfaces, resources/owners |
| Robustness and risks | 15 | Counterexamples, uncertainty, failure handling |
| Clarity and documentation | 10 | Audience fit, standalone, inspectable output |

Score each 0–5: absent/unusable; major flaws; material gaps; adequate with limits; strong/minor issues; supported/complete. Total = `sum(weight * score / 5)`. Scores aid selection; they are not confidence statistics or proofs.

Report artifact hash/version, location, disputed requirement/claim, evidence/counterexample, severity, fix, status. Critical means unusable core result; major means material gap; minor means nonblocking improvement. Resolve all critical/major findings before acceptance or explicitly change scope with the user. Authors mark fixed with evidence, rebutted with proof, or unresolved with owner/effect. Recheck fixes. Avoid irrelevant style critiques.

Verify reviewer independence from actual agent provenance, not role labels. Give neutral inputs: mandate, current artifacts, evidence, checks. Let reviewers inspect independently before reading author rationale. Preserve evidence-supported dissent.

Select compatible components from all PMUs. Critical flaws block components regardless of score. Reconcile contradictions using authoritative versions rather than votes. Recheck the assembled output for calculations, assumptions, terminology, dependency fit, faithful citations, format, and required outputs. Verify the requested flow end-to-end where possible. Do not claim exhaustive checks from role-play or tests not run.
