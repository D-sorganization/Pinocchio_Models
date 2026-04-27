"""Olympic barbell model for Pinocchio (URDF format).

Standard Olympic barbell dimensions (IWF / IPF regulations):
- Men's bar: 2.20 m total length, 1.31 m between collars, 28 mm shaft
  diameter, 50 mm sleeve diameter, 20 kg unloaded.
- Women's bar: 2.01 m total length, 1.31 m between collars, 25 mm shaft
  diameter, 50 mm sleeve diameter, 15 kg unloaded.

The barbell is modelled as three rigid bodies (left_sleeve, shaft, right_sleeve)
connected by fixed joints. Plates are added as additional mass on the sleeves.

Law of Demeter: callers interact only with BarbellSpec and create_barbell_links;
internal geometry details remain encapsulated.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from pinocchio_models.shared.contracts.preconditions import (
    require_non_negative,
    require_positive,
)
from pinocchio_models.shared.utils.geometry import (
    cylinder_inertia,
    hollow_cylinder_inertia,
)
from pinocchio_models.shared.utils.urdf_helpers import (
from pinocchio_models.exceptions import GeometryError
    add_fixed_joint,
    add_link,
    make_cylinder_geometry,
)

# --- Named constants for barbell plate geometry ---
# Standard Olympic plate outer radius (450 mm diameter / 2).
PLATE_OUTER_RADIUS_M: float = 0.225

# Minimum plate thickness in metres (prevents degenerate geometry at low mass).
MIN_PLATE_THICKNESS_M: float = 0.01

# Linear scaling factor: plate thickness = max(MIN, mass * this factor).
PLATE_THICKNESS_PER_KG: float = 0.002


@dataclass(frozen=True)
class BarbellSpec:
    """Immutable specification for a barbell.

    All lengths in meters, masses in kg, diameters in meters.
    """

    total_length: float = 2.20
    shaft_length: float = 1.31
    shaft_diameter: float = 0.028
    sleeve_diameter: float = 0.050
    bar_mass: float = 20.0
    plate_mass_per_side: float = 0.0

    def __post_init__(self) -> None:
        """Validate barbell specification dimensions and masses."""
        require_positive(self.total_length, "total_length")
        require_positive(self.shaft_length, "shaft_length")
        require_positive(self.shaft_diameter, "shaft_diameter")
        require_positive(self.sleeve_diameter, "sleeve_diameter")
        require_positive(self.bar_mass, "bar_mass")
        require_non_negative(self.plate_mass_per_side, "plate_mass_per_side")
        if self.shaft_length >= self.total_length:
            raise GeometryError(
                f"shaft_length ({self.shaft_length}) must be < "
                f"total_length ({self.total_length})"
            )

    @property
    def sleeve_length(self) -> float:
        """Length of one sleeve (half of non-shaft portion)."""
        return (self.total_length - self.shaft_length) / 2.0

    @property
    def shaft_radius(self) -> float:
        """Shaft radius in meters (half the shaft diameter)."""
        return self.shaft_diameter / 2.0

    @property
    def sleeve_radius(self) -> float:
        """Sleeve radius in meters (half the sleeve diameter)."""
        return self.sleeve_diameter / 2.0

    @property
    def shaft_mass(self) -> float:
        """Mass attributed to the shaft (proportional to length)."""
        shaft_fraction = self.shaft_length / self.total_length
        return self.bar_mass * shaft_fraction

    @property
    def sleeve_mass(self) -> float:
        """Mass of one bare sleeve (no plates)."""
        sleeve_fraction = self.sleeve_length / self.total_length
        return self.bar_mass * sleeve_fraction

    @property
    def total_mass(self) -> float:
        """Total barbell mass including plates on both sides."""
        return self.bar_mass + 2.0 * self.plate_mass_per_side

    @classmethod
    def mens_olympic(cls, plate_mass_per_side: float = 0.0) -> BarbellSpec:
        """Standard men's Olympic barbell (20 kg, 2.20 m)."""
        return cls(plate_mass_per_side=plate_mass_per_side)

    @classmethod
    def womens_olympic(cls, plate_mass_per_side: float = 0.0) -> BarbellSpec:
        """Standard women's Olympic barbell (15 kg, 2.01 m)."""
        return cls(
            total_length=2.01,
            shaft_length=1.31,
            shaft_diameter=0.025,
            sleeve_diameter=0.050,
            bar_mass=15.0,
            plate_mass_per_side=plate_mass_per_side,
        )


def create_barbell_links(
    robot: ET.Element,
    spec: BarbellSpec,
    *,
    prefix: str = "barbell",
) -> dict[str, ET.Element]:
    """Add barbell links and fixed joints to a URDF <robot> element.

    Returns dict of created link elements keyed by name.

    The barbell shaft center is at the local origin. Sleeves extend
    symmetrically along the Y-axis (left = -Y, right = +Y).
    Z-up convention: barbell lies horizontally in the Y-axis.
    """
    # cylinder_inertia() assumes the cylinder axis is Z.
    # The barbell lies along Y (sleeves at ±Y offsets), so swap iyy and izz
    # to correct the axial vs. transverse inertia assignment.
    # After swap: iyy = 0.5·m·r²  (axial, Y), izz = (1/12)·m·(3r²+L²)  (transverse)
    _shaft_ixx, _shaft_iyy, _shaft_izz = cylinder_inertia(
        spec.shaft_mass, spec.shaft_radius, spec.shaft_length
    )
    _shaft_iyy, _shaft_izz = _shaft_izz, _shaft_iyy  # Y-axis cylinder correction

    # Compute bare sleeve inertia
    _slv_ixx, _slv_iyy, _slv_izz = cylinder_inertia(
        spec.sleeve_mass, spec.sleeve_radius, spec.sleeve_length
    )
    _slv_iyy, _slv_izz = _slv_izz, _slv_iyy  # Y-axis cylinder correction

    # Add plate inertia using correct plate radius (0.225 m), not sleeve radius
    if spec.plate_mass_per_side > 0:
        plate_thickness = max(
            MIN_PLATE_THICKNESS_M,
            spec.plate_mass_per_side * PLATE_THICKNESS_PER_KG,
        )
        _plt_ixx, _plt_iyy, _plt_izz = hollow_cylinder_inertia(
            spec.plate_mass_per_side,
            inner_radius=spec.sleeve_radius,
            outer_radius=PLATE_OUTER_RADIUS_M,
            length=plate_thickness,
        )
        _plt_iyy, _plt_izz = _plt_izz, _plt_iyy  # Y-axis cylinder correction
        _slv_ixx += _plt_ixx
        _slv_iyy += _plt_iyy
        _slv_izz += _plt_izz

    sleeve_total_mass = spec.sleeve_mass + spec.plate_mass_per_side

    # Rotate visual cylinders 90° about X so they render along Y (not Z).
    _barbell_visual_rpy = (math.pi / 2, 0.0, 0.0)

    shaft_name = f"{prefix}_shaft"
    left_name = f"{prefix}_left_sleeve"
    right_name = f"{prefix}_right_sleeve"

    shaft_link = add_link(
        robot,
        name=shaft_name,
        mass=spec.shaft_mass,
        origin_xyz=(0, 0, 0),
        ixx=_shaft_ixx,
        iyy=_shaft_iyy,
        izz=_shaft_izz,
        visual_geometry=make_cylinder_geometry(spec.shaft_radius, spec.shaft_length),
        visual_origin_rpy=_barbell_visual_rpy,
    )

    left_link = add_link(
        robot,
        name=left_name,
        mass=sleeve_total_mass,
        origin_xyz=(0, 0, 0),
        ixx=_slv_ixx,
        iyy=_slv_iyy,
        izz=_slv_izz,
        visual_geometry=make_cylinder_geometry(spec.sleeve_radius, spec.sleeve_length),
        visual_origin_rpy=_barbell_visual_rpy,
    )

    right_link = add_link(
        robot,
        name=right_name,
        mass=sleeve_total_mass,
        origin_xyz=(0, 0, 0),
        ixx=_slv_ixx,
        iyy=_slv_iyy,
        izz=_slv_izz,
        visual_geometry=make_cylinder_geometry(spec.sleeve_radius, spec.sleeve_length),
        visual_origin_rpy=_barbell_visual_rpy,
    )

    half_shaft = spec.shaft_length / 2.0
    half_sleeve = spec.sleeve_length / 2.0

    add_fixed_joint(
        robot,
        name=f"{prefix}_left_weld",
        parent=shaft_name,
        child=left_name,
        origin_xyz=(0, -(half_shaft + half_sleeve), 0),
    )

    add_fixed_joint(
        robot,
        name=f"{prefix}_right_weld",
        parent=shaft_name,
        child=right_name,
        origin_xyz=(0, (half_shaft + half_sleeve), 0),
    )

    return {
        shaft_name: shaft_link,
        left_name: left_link,
        right_name: right_link,
    }