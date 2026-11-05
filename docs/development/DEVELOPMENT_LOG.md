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

### DL-#501 · Constrain the Right Hand to the Bar With a 6-D Loop Closure in Forward Dynamics

- **State:** in_review
- **Owner:** unassigned
- **Issue:** #501
- **Branch:** fix/501-right-hand-loop-closure
- **PR:** #502
- **Paths:** see #502
- **Started:** 2026-11-05
- **Last verified:** 2026-11-05 (`a3cd6ad0`; collated from changes/501-constrain-the-right-hand-to-the-bar-with.md)
- **Summary:** Constrain the right hand to the bar with a 6-D loop closure in forward dynamics
- **Next step:** Merge the PR.

### DL-#451 · Set Bench Frame Mass to 1E-4 to Match Cross-Engine Parity Standard

- **State:** in_review
- **Owner:** unassigned
- **Issue:** #451
- **Branch:** fix/451-bench-mass
- **PR:** #499
- **Paths:** see #499
- **Started:** 2026-11-05
- **Last verified:** 2026-11-05 (`4c700e39`; collated from changes/451-set-bench-frame-mass-to-1e-4-to-match-cr.md)
- **Summary:** Set bench frame mass to 1e-4 to match cross-engine parity standard
- **Next step:** Merge the PR.

### DL-#438 · Add Headless Record_Rollout That Records an Exercise Rollout as a Self-Contained Meshcat HTML Animation

- **State:** in_review
- **Owner:** unassigned
- **Issue:** #438
- **Branch:** feat/438-record
- **PR:** #493, #498
- **Paths:** see #493
- **Started:** 2026-11-05
- **Last verified:** 2026-11-05 (`a0fb6798`; collated from changes/438-prettier-format-the-collate-generated-sp.md)
- **Summary:** Add headless record_rollout that records an exercise rollout as a self-contained Meshcat HTML animation
- **Next step:** Merge the PR.

### DL-#433 · Resolve Ledgered Joint Limits Under Standard V2 Axis Conventions

- **State:** in_review
- **Owner:** unassigned
- **Issue:** #433
- **Branch:** fix/433-standard-v2-joint-limits
- **PR:** #500
- **Paths:** see #500
- **Started:** 2026-11-05
- **Last verified:** 2026-11-05 (`7d3d60fa`; collated from changes/433-resolve-ledgered-joint-limits-standard-v2.md)
- **Summary:** Resolve ledgered joint limits under standard v2 axis conventions
- **Next step:** Merge the PR.

### DL-#437 · Add Cross-Engine Test That Loads the URDF in MuJoCo and Drake

- **State:** in_review
- **Owner:** unassigned
- **Issue:** #437
- **Branch:** feat/437-cross-engine-urdf-test
- **PR:** #486
- **Paths:** see #486
- **Started:** 2026-10-13
- **Last verified:** 2026-10-13 (`9a6268dc`; collated from changes/437-add-cross-engine-test-that-loads-the-urd.md)
- **Summary:** Add cross-engine test that loads the URDF in MuJoCo and Drake
- **Next step:** Merge the PR.

### DL-#436 · Rename Elbow_L, Knee_L and Neck to Canonical Joint Names

- **State:** in_review
- **Owner:** unassigned
- **Issue:** #436
- **Branch:** feat/436-rename-canonical-joints
- **PR:** #484
- **Paths:** see #484
- **Started:** 2026-10-13
- **Last verified:** 2026-10-13 (`478af846`; collated from changes/436-rename-elbow-l-knee-l-and-neck-to-canoni.md)
- **Summary:** Rename elbow_l, knee_l and neck to canonical joint names
- **Next step:** Merge the PR.

### DL-#466 · Weld the Bench-Press Root at the Standard V2.0 Via-Pose

- **State:** in_review
- **Owner:** unassigned
- **Issue:** #466
- **Branch:** fix/466-bench-press-root-weld
- **PR:** #476
- **Paths:** see #476
- **Started:** 2026-10-13
- **Last verified:** 2026-10-13 (`f7f232a5`; collated from changes/466-weld-the-bench-press-root-at-the-standar.md)
- **Summary:** Weld the Bench-Press Root at the Standard v2.0 Via-Pose
- **Next step:** Merge the PR.

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
- **PR:** #472, #482
- **Paths:** see #472
- **Started:** 2026-10-12
- **Last verified:** 2026-10-13 (`fa036be2`; collated from changes/450-ground-pelvis-so-foot-soles-rest-on-floo.md)
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

### DL-#514 · Unblock Collate Change Fragments on Main: Drop the Stale in_Review State From the #497 Fragment for Shipped DL-#425

- **State:** shipped
- **Owner:** unassigned
- **Issue:** #514
- **Branch:** merged via #515
- **PR:** #515
- **Paths:** see #515
- **Started:** 2026-11-05
- **Last verified:** 2026-11-05 (`649529e3`; collated from changes/514-unblock-collate-change-fragments-on-main.md)
- **Summary:** Unblock Collate Change Fragments on main: drop the stale in_review state from the #497 fragment for shipped DL-#425
- **Next step:** Shipped in PR #515.

### DL-#512 · Register the Requires_Pinocchio Pytest Marker so Pytest 9.2 Accepts the CI -m Expression

- **State:** shipped
- **Owner:** unassigned
- **Issue:** #512
- **Branch:** merged via #513
- **PR:** #513
- **Paths:** see #513
- **Started:** 2026-11-05
- **Last verified:** 2026-11-05 (`d754a89d`; collated from changes/512-register-the-requires-pinocchio-pytest-m.md)
- **Summary:** Register the requires_pinocchio pytest marker so pytest 9.2 accepts the CI -m expression
- **Next step:** Shipped in PR #513.

### DL-#430 · Add Aba Forward-Dynamics API With Penalty Ground Contact and Real Crocoddyl OCP Tests (Fix OCP for Crocoddyl >= 2)

- **State:** shipped
- **Owner:** unassigned
- **Issue:** #430
- **Branch:** merged via #494
- **PR:** #494
- **Paths:** see #494
- **Started:** 2026-11-05
- **Last verified:** 2026-11-05 (`ffec35c7`; collated from changes/430-add-aba-forward-dynamics-api-with-penalt.md)
- **Summary:** Add aba forward-dynamics API with penalty ground contact and real Crocoddyl OCP tests (fix OCP for Crocoddyl >= 2)
- **Next step:** Shipped in PR #494.

### DL-#2567 · Delete the Legacy .agent/ Skill and Workflow Copies; Agy and Codex Read .agents/ (Repository_Management#2567)

- **State:** shipped
- **Owner:** unassigned
- **Issue:** #2567
- **Branch:** merged via #511
- **PR:** #511
- **Paths:** see #511
- **Started:** 2026-11-05
- **Last verified:** 2026-11-05 (`c7680b45`; collated from changes/2567-delete-the-legacy-agent-skill-and-workfl.md)
- **Summary:** Delete the legacy .agent/ skill and workflow copies; agy and Codex read .agents/ (Repository_Management#2567)
- **Next step:** Shipped in PR #511.

### DL-#425 · Re-Sync Vendored Model-Parity Bundle to Repository_Management Main (Standard V2.1, assemble.py Phase_Names From RM#2089)

- **State:** shipped
- **Owner:** unassigned
- **Issue:** #425
- **Branch:** merged via #495
- **PR:** #495, #497
- **Paths:** see #495
- **Started:** 2026-10-13
- **Last verified:** 2026-11-05 (`9183a5b6`; collated from changes/425-fingerprint-reports-the-standard-s-order.md)
- **Summary:** Re-sync vendored model-parity bundle to Repository_Management main (standard v2.1, assemble.py phase_names from RM#2089)
- **Next step:** Shipped in PR #495.

### DL-#432 · Add Constrained Contact Dynamics GRF/CoP API (Ground_Reaction_Forces) With Real-Pinocchio Standing Test

- **State:** shipped
- **Owner:** unassigned
- **Issue:** #432
- **Branch:** merged via #487
- **PR:** #487
- **Paths:** see #487
- **Started:** 2026-10-13
- **Last verified:** 2026-10-13 (`f8291479`; collated from changes/432-add-constrained-contact-dynamics-grf-cop.md)
- **Summary:** Add constrained contact dynamics GRF/CoP API (ground_reaction_forces) with real-Pinocchio standing test
- **Next step:** Shipped in PR #487.

### DL-#429 · Real Pink IK Tests With Frame and Ground Targets

- **State:** shipped
- **Owner:** claude
- **Issue:** #429
- **Branch:** feat/429-pink-real
- **PR:** #491
- **Paths:** src/pinocchio_models/addons/pink,tests/integration/test_pink_ik_real.py,model_pack.yaml,pyproject.toml
- **Started:** 2026-10-13
- **Last verified:** 2026-10-13 (`650ef388`; collated from changes/429-real-pink-tests-solve-hand-bar-and-foot.md)
- **Summary:** Real-pink tests solve hand, bar and foot-height targets on the squat URDF under 1 cm; fixed the wrapper (pink.solve_ik with a QP backend, ground targets plant soles at sole depth, unknown frames rejected); IK capability raised to full.
- **Next step:** Shipped in PR #491.

### DL-#449 · Set Bilateral Right-Limb Targets in Sit-to-Stand Objective Phases

- **State:** shipped
- **Owner:** unassigned
- **Issue:** #449
- **Branch:** merged via #480
- **PR:** #480
- **Paths:** see #480
- **Started:** 2026-10-13
- **Last verified:** 2026-10-13 (`ed0dea59`; collated from changes/449-set-bilateral-right-limb-targets-in-sit.md)
- **Summary:** Set bilateral right-limb targets in sit-to-stand objective phases
- **Next step:** Shipped in PR #480.

### DL-#471 · Place-Foot-Contacts-and-Sole-Collision-Foot.Length-Below-the-Ankle-per-the-Parity-Standard

- **State:** shipped
- **Owner:** unassigned
- **Issue:** #471
- **Branch:** merged via #477
- **PR:** #477
- **Paths:** see #477
- **Started:** 2026-10-12
- **Last verified:** 2026-10-12 (`159194e7`; collated from changes/471-place-foot-contacts-and-sole-collision-f.md)
- **Summary:** Place-foot-contacts-and-sole-collision-foot.length-below-the-ankle-per-the-parity-standard
- **Next step:** Shipped in PR #477.

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
