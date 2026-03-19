from dataclasses import dataclass, field


@dataclass
class AppState:
    x: float = 430.0
    y: float = 0.0
    z: float = 277.0
    joints: list[float] = field(default_factory=lambda: [0.0] * 6)
    erosion_enabled: bool = False
    water_enabled: bool = False
    pump_in_enabled: bool = False
    pump_out_enabled: bool = False
