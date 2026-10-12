# Development Log — Pinocchio_Models

State table for every feature in flight in this repository. Update
entries **in place**; never append dated sections. One entry per
feature, from proposal to ship. See the `development-logs` section of
`AGENTS.md` for the binding rules and
`shared_scripts/development_log.py` for the validator.

- **Portfolio:** work
- **WIP limit:** 5
- **Last audited:** 2026-08-28 by bootstrap

## States

`proposed` → `in_progress` → `in_review` → `shipped`, with `parked`
reachable from any live state and `abandoned` from `parked`.
`shipped` never returns to `in_progress`; open a new entry instead.

## Active

### DL-#467 · \ Name Gait and Sit-to-Stand Phases per Standard V2.0\

- **State:** in_review
- **Owner:** unassigned
- **Issue:** #467
- **Branch:** fix/467-gait-sts-phases
- **PR:** #474
- **Paths:** see #474
- **Started:** 2026-10-12
- **Last verified:** 2026-10-12 (`6b1ba04d`; collated from changes/467-name-gait-and-sit-to-stand-phases-per-st.md)
- **Summary:** \ Name Gait and Sit-to-Stand Phases per Standard v2.0\
- **Next step:** \Merge the PR.\

### DL-#450 · Lifts Start at the Spec Start Via-Pose (LIFT-3)

- **State:** in_review
- **Owner:** unassigned
- **Issue:** #450
- **Branch:** claude/lift-3-spec-start-poses
- **PR:** #472
- **Paths:** see #472
- **Started:** 2026-10-12
- **Last verified:** 2026-10-12 (`dbbf2513`; collated from changes/450-lift-3-barbell-lifts-start-at-the-spec-v.md)
- **Summary:** LIFT-3: barbell lifts start at the spec v2.1 start via-pose (joints, pelvis root, bar); mass and CoM checks
- **Next step:** Merge the PR; then #470 (bench ankle limit), #471 (sole contacts), #466 (bench weld root).

### DL-#459 · Fix Shoulder Adduction/Abduction Joint-Limit Sign Convention so the Snatch's Wide-Grip Start Pose Is Within Limits

- **State:** in_review
- **Owner:** claude
- **Issue:** #459
- **Branch:** claude/shoulder-rom-459
- **PR:** #461
- **Paths:** see #461
- **Started:** 2026-10-10
- **Last verified:** 2026-10-10 (`c35aa381`; collated from changes/459-fix-shoulder-adduction-abduction-joint-l.md)
- **Summary:** Fix shoulder adduction/abduction joint-limit sign convention so the snatch's wide-grip start pose is within limits
- **Next step:** Open PR for review

### DL-#443 · Grip Geometry: Shoulder Abduction Closes the Barbell Loop

- **State:** in_review
- **Owner:** claude
- **Issue:** #443
- **Branch:** claude/grip-geometry-443
- **PR:** #458
- **Paths:** src/pinocchio_models/shared/body/canonical_topology.py, src/pinocchio_models/exercises/base.py, tests/parity/test_grip_geometry.py
- **Started:** 2026-10-10
- **Last verified:** 2026-10-10 (`6eaded00`; collated from changes/443-derive-grip-width-from-shoulder-abductio.md)
- **Summary:** Derive grip width from shoulder abduction so both hands reach the barbell at the midline
- **Next step:** Merge the PR.

### DL-#435 · Canonical Topology: Left at Plus Y and Standard Joint Axes

- **State:** in_review
- **Owner:** unassigned
- **Issue:** #435
- **Branch:** fix/issue-435-canonical-topology
- **PR:** #444
- **Paths:** see #444
- **Started:** 2026-10-06
- **Last verified:** 2026-10-06 (`00ee8d8e`; collated from changes/435-canonical-topology.md)
- **Summary:** Migrate the model to the standard v2 topology: left segments at +Y, canonical joint axes and joint origins read from the vendored standard (hip and shoulder widths, shoulder height), supine bench press on a bench root link, barbell left sleeve at +Y; the fingerprint measures axes, pelvis rotation and test-pose origins in the real engine, with zero axis, side, origin and pose divergences.
- **Next step:** Merge the PR.

### DL-#1607 · Adopt Mermaid C4 Architecture Map Contract

- **Issue:** #1607 (https://github.com/D-sorganization/Repository_Management/issues/1607)
- **State:** in_progress
- **Owner:** local (agent session bd082424-e57d-40ba-9962-3bf4420a5b33)
- **Branch:** docs/1607-c4-architecture-map
- **PR:** not created
- **Paths:** docs/architecture/C4.md, scripts/architecture_map_contract.py, tests/scripts/test_architecture_map_contract.py, .github/workflows/architecture-map-contract.yml
- **Started:** 2026-09-10
- **Last verified:** 2026-09-10
- **Next step:** Open PR and merge with passing architecture map contract workflow.
- **Summary:** Establish and enforce the maintainable Mermaid C4 architecture-map contract for Pinocchio_Models per Repository_Management Epic #1594.

## Shipped (Last 90 Days)

### DL-#434 · Lift Objectives Consume the Standard V2.0 Exercise Spec (Phase Names, Timing, Start/Catch/Lockout Via-Poses); Deadlift Now Has the Spec's 5 Phases (LIFT-2, UpstreamDrift#11742)

- **State:** shipped
- **Owner:** unassigned
- **Issue:** #434
- **Branch:** claude/lift-2-standard-v2
- **PR:** #468
- **Paths:** see #468
- **Started:** 2026-10-11
- **Last verified:** 2026-10-11 (`8b4d2198`; collated from changes/434-lift-objectives-consume-the-standard-v2.md)
- **Summary:** Lift objectives consume the standard v2.0 exercise spec (phase names, timing, start/catch/lockout via-poses); deadlift now has the spec's 5 phases (LIFT-2, UpstreamDrift#11742)
- **Next step:** Shipped in PR #468.

### DL-#1917 · Sync the Agent-Identity Managed Block: The Owner's Personal Token Is an Approved Agent Identity

- **State:** shipped
- **Owner:** unassigned
- **Issue:** #1917
- **Branch:** merged via #463
- **PR:** #463
- **Paths:** see #463
- **Started:** 2026-10-11
- **Last verified:** 2026-10-11 (`9ece74a1`; collated from changes/1917-sync-the-agent-identity-managed-block-th.md)
- **Summary:** Sync the agent-identity managed block: the owner's personal token is an approved agent identity
- **Next step:** Shipped in PR #463.

### DL-#439 · Remove Stray Pr251.Json From Repo Root

- **State:** shipped
- **Owner:** unassigned
- **Issue:** #439
- **Branch:** merged via #456
- **PR:** #456
- **Paths:** see #456
- **Started:** 2026-10-10
- **Last verified:** 2026-10-10 (`140b8b85`; collated from changes/439-remove-stray-pr251-json-from-repo-root.md)
- **Summary:** Remove stray pr251.json from repo root
- **Next step:** Shipped in PR #456.

### DL-#428 · Add Public Forward_Kinematics API With Real-Pinocchio Test

- **State:** shipped
- **Owner:** unassigned
- **Issue:** #428
- **Branch:** merged via #454
- **PR:** #454
- **Paths:** see #454
- **Started:** 2026-10-09
- **Last verified:** 2026-10-09 (`66aa7fbc`; collated from changes/428-add-public-forward-kinematics-api-with-r.md)
- **Summary:** Add public forward_kinematics API with real-Pinocchio test
- **Next step:** Shipped in PR #454.

### DL-#431 · Add Public Rnea Inverse_Dynamics API With Real-Pinocchio Test

- **State:** shipped
- **Owner:** unassigned
- **Issue:** #431
- **Branch:** merged via #452
- **PR:** #452
- **Paths:** see #452
- **Started:** 2026-10-09
- **Last verified:** 2026-10-09 (`d1dbfe5f`; collated from changes/431-add-public-rnea-inverse-dynamics-api-wit.md)
- **Summary:** Add public rnea inverse_dynamics API with real-Pinocchio test
- **Next step:** Shipped in PR #452.

### DL-#446 · SECURITY: Guard Fork PRs Off the Self-Hosted Fleet (RM#1989); Vendor Fork_Pr_Runner_Guard and Wire Into CI

- **State:** shipped
- **Owner:** unassigned
- **Issue:** #446
- **Branch:** merged via #447
- **PR:** #447
- **Paths:** see #447
- **Started:** 2026-10-07
- **Last verified:** 2026-10-07 (`f9f5b076`; collated from changes/446-security-guard-fork-prs-off-the-self-hos.md)
- **Summary:** SECURITY: guard fork PRs off the self-hosted fleet (RM#1989); vendor fork_pr_runner_guard and wire into CI
- **Next step:** Shipped in PR #447.

### DL-#2019 · Vendor RM-5 Change-Fragment Tooling and Test Suite

- **State:** shipped
- **Owner:** unassigned
- **Issue:** #2019
- **Branch:** feat/2019-vendor-rm-5-change-fragment-tooling
- **PR:** #440, #441
- **Paths:** see #440
- **Started:** 2026-10-05
- **Last verified:** 2026-10-05 (`d9cd00cd`; collated from changes/2019-wire-collate-changes-workflow-and-check.md)
- **Summary:** vendor RM-5 change-fragment tooling and test suite
- **Next step:** Shipped in PR #440.

Entries stay here for 90 days after merge, then move to the archive.

## Archive

Older entries live in `DEVELOPMENT_LOG_ARCHIVE_<year>.md`.
