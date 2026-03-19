from robot_ui.app_logger import AppLogger
from robot_ui.erosion_parameters import ErosionParameters
from robot_ui.hardware_stubs import (
    zaglushka_erosion,
    zaglushka_move_joints,
    zaglushka_move_xyz,
    zaglushka_pump_in,
    zaglushka_pump_out,
    zaglushka_run_erosion,
    zaglushka_water,
)


class StubRobotHardware:
    def __init__(self, logger: AppLogger) -> None:
        self._logger = logger
        self._pump_in = False
        self._pump_out = False

    def move_xyz(self, x: float, y: float, z: float) -> None:
        self._logger.info(f"move_xyz({x}, {y}, {z})")
        zaglushka_move_xyz(x, y, z)

    def move_joints(self, joints: list[float]) -> None:
        self._logger.info(f"move_joints({joints})")
        zaglushka_move_joints(joints)

    def set_erosion(self, enabled: bool) -> None:
        self._logger.info(f"set_erosion({enabled})")
        zaglushka_erosion(enabled)

    def set_water(self, enabled: bool) -> None:
        self._logger.info(f"set_water({enabled})")
        zaglushka_water(enabled)

    def toggle_pump_in(self) -> bool:
        self._pump_in = not self._pump_in
        self._logger.info(f"toggle_pump_in -> {self._pump_in}")
        zaglushka_pump_in()
        return self._pump_in

    def toggle_pump_out(self) -> bool:
        self._pump_out = not self._pump_out
        self._logger.info(f"toggle_pump_out -> {self._pump_out}")
        zaglushka_pump_out()
        return self._pump_out

    def run_erosion(self, file_path: str, params: ErosionParameters) -> None:
        self._logger.info(f"run_erosion(file={file_path}, mode={params.mode})")
        zaglushka_run_erosion(file_path, params.mode)
