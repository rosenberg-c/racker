from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class RackConfig:
    top_bottom_x: float = 490.0
    top_bottom_y: float = 400.0
    top_bottom_z: float = 18.0
    side_x: float = 18.0
    side_y: float = 400.0
    unit_height: float = 44.45
    rail_thickness: float = 2.0
    rail_wood_width: float = 30.0
    rail_rack_width: float = 21.0
    rail_outset: float = 18.0
    hole_diameter: float = 7.1
    hole_offsets: Tuple[float, float, float] = (6.35, 22.225, 38.1)
