"""Characterization tests for optional dependency helper builders."""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import numpy as np


class _FakeFrameTask:
    def __init__(
        self,
        frame_name: str,
        *,
        position_cost: float,
        orientation_cost: float,
    ) -> None:
        self.frame_name = frame_name
        self.position_cost = position_cost
        self.orientation_cost = orientation_cost
        self.target = None
        self._error = np.zeros(3)

    def set_target(self, target: object) -> None:
        self.target = target

    def compute_error(self, _configuration: object) -> np.ndarray:
        return self._error


class _FakeConfiguration:
    def __init__(self, model: object, data: object, q: np.ndarray) -> None:
        self.model = model
        self.data = data
        self.q = q

    def solve_ik(self, tasks: list[object], dt: float) -> np.ndarray:
        self.last_tasks = tasks
        self.last_dt = dt
        return np.array([0.5, -0.25, 0.25])


class _FakeSE3:
    def __init__(self, rotation: np.ndarray, translation: np.ndarray) -> None:
        self.rotation = rotation
        self.translation = translation

    @staticmethod
    def Identity() -> str:
        return "identity-se3"


class _FakeModel:
    def __init__(self) -> None:
        self.nv = 3

    def getFrameId(self, name: str) -> int:  # noqa: N802 - third-party API shape
        return {"foot_l": 11, "foot_r": 22}[name]


class _FakeStateMultibody:
    def __init__(self, model: _FakeModel) -> None:
        self.model = model


class _FakeActuationModelFloatingBase:
    def __init__(self, state: _FakeStateMultibody) -> None:
        self.state = state


class _FakeCostModelSum:
    def __init__(self, state: _FakeStateMultibody) -> None:
        self.state = state
        self.costs: list[tuple[str, object, float]] = []

    def addCost(self, name: str, cost: object, weight: float) -> None:  # noqa: N802
        self.costs.append((name, cost, weight))


@dataclass
class _FakeResidualModelControl:
    state: object


@dataclass
class _FakeResidualModelState:
    state: object
    xref: object | None = None


@dataclass
class _FakeCostModelResidual:
    state: object
    residual: object


@dataclass
class _FakeContactModel3D:
    state: object
    frame_id: int
    reference: np.ndarray
    nv: int
    gains: np.ndarray


class _FakeContactModelMultiple:
    def __init__(self, state: _FakeStateMultibody, nv: int) -> None:
        self.state = state
        self.nv = nv
        self.contacts: list[tuple[str, _FakeContactModel3D]] = []

    def addContact(self, name: str, contact: _FakeContactModel3D) -> None:  # noqa: N802
        self.contacts.append((name, contact))


@dataclass
class _FakeFrictionCone:
    rotation: np.ndarray
    mu: float
    facets: int
    inner_appr: bool


@dataclass
class _FakeResidualModelContactFrictionCone:
    state: object
    frame_id: int
    cone: object
    nv: int


@dataclass
class _FakeDifferentialActionModelContactFwdDynamics:
    state: object
    actuation: object
    contacts: object
    cost_model: object


@dataclass
class _FakeDifferentialActionModelFreeFwdDynamics:
    state: object
    actuation: object
    cost_model: object


@dataclass
class _FakeIntegratedActionModelEuler:
    differential_model: object
    dt: float


@dataclass
class _FakeShootingProblem:
    x0: np.ndarray
    running_models: list[object]
    terminal_model: object


def _fake_pink_module() -> tuple[ModuleType, ModuleType]:
    fake_pink = ModuleType("pink")
    fake_pink.tasks = SimpleNamespace(FrameTask=_FakeFrameTask)
    fake_pink.Configuration = _FakeConfiguration

    fake_pin = ModuleType("pinocchio")
    fake_pin.SE3 = _FakeSE3
    fake_pin.integrate = lambda _model, q, delta: q + delta

    return fake_pink, fake_pin


def _fake_crocoddyl_module() -> tuple[ModuleType, ModuleType]:
    fake_crocoddyl = ModuleType("crocoddyl")
    fake_crocoddyl.StateMultibody = _FakeStateMultibody
    fake_crocoddyl.ActuationModelFloatingBase = _FakeActuationModelFloatingBase
    fake_crocoddyl.CostModelSum = _FakeCostModelSum
    fake_crocoddyl.ResidualModelControl = _FakeResidualModelControl
    fake_crocoddyl.ResidualModelState = _FakeResidualModelState
    fake_crocoddyl.CostModelResidual = _FakeCostModelResidual
    fake_crocoddyl.ContactModelMultiple = _FakeContactModelMultiple
    fake_crocoddyl.ContactModel3D = _FakeContactModel3D
    fake_crocoddyl.FrictionCone = _FakeFrictionCone
    fake_crocoddyl.ResidualModelContactFrictionCone = (
        _FakeResidualModelContactFrictionCone
    )
    fake_crocoddyl.DifferentialActionModelContactFwdDynamics = (
        _FakeDifferentialActionModelContactFwdDynamics
    )
    fake_crocoddyl.DifferentialActionModelFreeFwdDynamics = (
        _FakeDifferentialActionModelFreeFwdDynamics
    )
    fake_crocoddyl.IntegratedActionModelEuler = _FakeIntegratedActionModelEuler
    fake_crocoddyl.ShootingProblem = _FakeShootingProblem

    fake_pin = ModuleType("pinocchio")
    fake_pin.JointModelFreeFlyer = lambda: "freeflyer"
    fake_pin.buildModelFromXML = lambda _urdf, _joint: _FakeModel()
    fake_pin.neutral = lambda _model: np.array([0.25, -0.5, 0.75])

    return fake_crocoddyl, fake_pin


class TestPinkHelperBuilders:
    def test_builds_target_and_ground_tasks_and_integrates_one_step(self) -> None:
        fake_pink, fake_pin = _fake_pink_module()

        with patch.dict(sys.modules, {"pink": fake_pink, "pinocchio": fake_pin}):
            import pinocchio_models.addons.pink.ik_solver_tasks as task_mod

            task_mod = importlib.reload(task_mod)

            target_pose = np.eye(4)
            target_pose[:3, 3] = [1.0, 2.0, 3.0]
            target_tasks = task_mod._build_target_tasks({"hand": target_pose})

            assert len(target_tasks) == 1
            task = target_tasks[0]
            assert task.frame_name == "hand"
            assert task.position_cost == 1.0
            assert task.orientation_cost == 1.0
            assert isinstance(task.target, _FakeSE3)
            np.testing.assert_array_equal(
                task.target.translation, np.array([1.0, 2.0, 3.0])
            )

            ground_tasks = task_mod._build_ground_tasks()
            assert [task.frame_name for task in ground_tasks] == ["foot_l", "foot_r"]
            assert all(task.target == "identity-se3" for task in ground_tasks)

            configuration = _FakeConfiguration(
                object(), object(), np.array([1.0, 2.0, 3.0])
            )
            next_configuration = task_mod._ik_step(
                configuration,
                object(),
                object(),
                target_tasks + ground_tasks,
            )
            np.testing.assert_allclose(
                next_configuration.q, np.array([1.005, 1.9975, 3.0025])
            )

            target_tasks[0]._error = np.array([1e-6, 0.0, 0.0])
            ground_tasks[0]._error = np.array([2e-6, 0.0, 0.0])
            ground_tasks[1]._error = np.array([3e-6, 0.0, 0.0])
            assert task_mod._check_convergence(
                configuration, target_tasks + ground_tasks, 1e-4
            )

            ground_tasks[1]._error = np.array([1e-2, 0.0, 0.0])
            assert not task_mod._check_convergence(
                configuration,
                target_tasks + ground_tasks,
                1e-4,
            )

        import pinocchio_models.addons.pink.ik_solver_tasks as task_mod

        importlib.reload(task_mod)


class TestCrocoddylHelperBuilders:
    def test_builders_create_contact_and_shooting_problem_components(self) -> None:
        fake_crocoddyl, fake_pin = _fake_crocoddyl_module()

        with patch.dict(
            sys.modules,
            {"crocoddyl": fake_crocoddyl, "pinocchio": fake_pin},
        ):
            import pinocchio_models.addons.crocoddyl.optimal_control_builders as builder_mod

            builder_mod = importlib.reload(builder_mod)

            model = _FakeModel()
            state = _FakeStateMultibody(model)
            contacts = builder_mod._build_contact_models(
                model, state, ["foot_l", "foot_r"]
            )
            assert [name for name, _ in contacts.contacts] == [
                "foot_l_contact",
                "foot_r_contact",
            ]
            assert [contact.frame_id for _, contact in contacts.contacts] == [11, 22]

            components = builder_mod._build_ocp_common(
                "<robot name='test'/>",
                "back_squat",
                dt=0.02,
                n_steps=5,
                use_contacts=True,
            )
            assert components.model.nv == 3
            assert len(components.running_cost_model.costs) == 4
            assert [name for name, _, _ in components.running_cost_model.costs] == [
                "effort",
                "state_reg",
                "foot_l_friction",
                "foot_r_friction",
            ]
            assert [name for name, _, _ in components.terminal_cost_model.costs] == [
                "state_reg"
            ]
            np.testing.assert_allclose(
                components.x0,
                np.array([0.25, -0.5, 0.75, 0.0, 0.0, 0.0]),
            )

            assembled = builder_mod._assemble_shooting_problem(
                components, dt=0.02, n_steps=5
            )
            assert len(assembled.running_models) == 5
            assert assembled.running_models[0].dt == 0.02
            assert assembled.terminal_model.dt == 0.0
            assert isinstance(
                assembled.running_models[0].differential_model,
                _FakeDifferentialActionModelContactFwdDynamics,
            )

            free_components = builder_mod._OCPComponents(
                model=model,
                state=state,
                actuation=_FakeActuationModelFloatingBase(state),
                running_cost_model=_FakeCostModelSum(state),
                terminal_cost_model=_FakeCostModelSum(state),
                contacts=None,
                x0=np.zeros(6),
            )
            assembled_free = builder_mod._assemble_shooting_problem(
                free_components,
                dt=0.01,
                n_steps=2,
            )
            assert isinstance(
                assembled_free.running_models[0].differential_model,
                _FakeDifferentialActionModelFreeFwdDynamics,
            )

        import pinocchio_models.addons.crocoddyl.optimal_control_builders as builder_mod

        importlib.reload(builder_mod)
