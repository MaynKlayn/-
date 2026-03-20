from dataclasses import dataclass


@dataclass(frozen=True)
class ErosionParameters:
    electrode_diameter: float = 2.0
    electrode_length: float = 100.0
    erosion_time: float = 10.0
    erosion_up_time: float = 5.0
    erosion_depth: float = 0.1
    erosion_speed: float = 10.0
    mode: str = "test"
