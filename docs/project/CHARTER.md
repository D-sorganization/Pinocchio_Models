# Project Charter

> Drafted 2026-09-25 by the fleet charter sweep (Gemini) from README, git history, and open issues/PRs.
> The project-steward role keeps this current; owners should correct feature statuses.

## End Goal

Pinocchio_Models provides a deterministic, contract-validated multibody dynamics model generator for Pinocchio, assembling URDF representations for five classical barbell exercises (back squat, bench press, deadlift, snatch, clean and jerk) alongside gait and sit-to-stand movements using Winter (2009) anthropometrics and regulation barbell specifications. "Done" means a robust, fully tested library that reliably exports valid URDF models, publishes an UpstreamDrift model pack manifest, and provides optional, cleanly isolated integrations for Gepetto-viewer visualization, Pink inverse kinematics, and Crocoddyl trajectory optimization without external runtime dependencies.

## Non-Goals

- Acting as a general-purpose robotics simulation engine or physics solver (URDFs are loaded externally by Pinocchio).
- Internal physics simulation runtime or numerical integration.
- Mandatory runtime dependencies on optional addons (Gepetto, Pink, and Crocoddyl must remain optional).
- Direct encoding of gravity inside generated URDF XML (configured programmatically in Pinocchio).
- Arbitrary exercise mechanics beyond barbell, bodyweight, and gait configurations.

## Features

| ID | Feature | Status | Tracking | Notes |
| --- | --- | --- | --- | --- |
| F1 | Core barbell exercise URDF models | shipped | #171 | Builds squat, bench press, deadlift, snatch, and clean and jerk models |
| F2 | Gait and sit-to-stand kinematics | shipped | - | Lower-limb kinematic models for locomotion and chair rise |
| F3 | Anthropometric body segment model | shipped | #120 | Winter 2009 proportional segment table and link inertia construction |
| F4 | Regulation Olympic barbell model | shipped | - | Configurable IWF and IPF barbell specifications with plates |
| F5 | Initial pose configuration extraction | shipped | - | Translates initial_position joint attributes into Pinocchio poses |
| F6 | CLI model generation interface | shipped | #229 | Generates URDF models via CLI with optional JSON output |
| F7 | UpstreamDrift model pack integration | shipped | #282 | Publishes model_pack.yaml and entry point for launcher discovery |
| F8 | Design by Contract error validation | shipped | #179 | Precondition and postcondition guards using PMxxx error codes |
| F9 | Gepetto-viewer visualization addon | shipped | - | Optional visualization integration with gepetto-viewer-corba |
| F10 | Pink inverse kinematics addon | shipped | #124 | Task-based IK solver integration for target pose generation |
| F11 | Crocoddyl optimal control addon | shipped | #116 | Optimal control problem formulation and trajectory optimization |
| F12 | Mermaid C4 architecture contract | shipped | #382 | Architectural context and container boundaries enforced by contract |
| F13 | High-performance URDF serialization | shipped | #402 | Micro-optimized XML escaping and ElementTree serialization |
| F14 | Fleet testing and quality standards | shipped | #278 | Unit, integration, and benchmark tests with strict CI coverage |

## Links

- Status (generated): [`STATUS.md`](STATUS.md)
- Steward playbook: Repository_Management `docs/fleet-project-steward.md`
