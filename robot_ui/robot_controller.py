from pathlib import Path

from robot_ui.app_logger import AppLogger
from robot_ui.app_state import AppState
from robot_ui.erosion_parameters import ErosionParameters
from robot_ui.gcode_parser import GCodeParser
from robot_ui.robot_hardware import RobotHardware


class RobotController:
    def __init__(self, hardware: RobotHardware, parser: GCodeParser, logger: AppLogger) -> None:
        self.state = AppState()
        self._hardware = hardware
        self._parser = parser
        self._logger = logger

    def move_xyz(self, x: float, y: float, z: float) -> None:
        self._hardware.move_xyz(x, y, z)
        self.state.x, self.state.y, self.state.z = x, y, z

    def move_joint(self, index: int, value: float) -> None:
        joints = self.state.joints.copy()
        joints[index] = value
        self._hardware.move_joints(joints)
        self.state.joints = joints

    def set_erosion(self, enabled: bool) -> None:
        self._hardware.set_erosion(enabled)
        self.state.erosion_enabled = enabled

    def set_water(self, enabled: bool) -> None:
        self._hardware.set_water(enabled)
        self.state.water_enabled = enabled

    def toggle_pump_in(self) -> bool:
        self.state.pump_in_enabled = self._hardware.toggle_pump_in()
        return self.state.pump_in_enabled

    def toggle_pump_out(self) -> bool:
        self.state.pump_out_enabled = self._hardware.toggle_pump_out()
        return self.state.pump_out_enabled

    def load_gcode(self, file_path: str) -> list[tuple[float, float, float]]:
        if not Path(file_path).exists():
            raise FileNotFoundError(file_path)
        points = self._parser.parse(file_path)
        self._logger.info(f"Loaded {len(points)} G-code points")
        return points

    def gcode_summary(self, file_path: str) -> str:
        points = self.load_gcode(file_path)
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        zs = [point[2] for point in points]
        return (
            f"Файл: {Path(file_path).name}\n"
            f"Количество точек: {len(points)}\n"
            f"X: {min(xs):.2f}..{max(xs):.2f}\n"
            f"Y: {min(ys):.2f}..{max(ys):.2f}\n"
            f"Z: {min(zs):.2f}..{max(zs):.2f}\n"
            f"Длина траектории: {self._parser.path_length(points):.2f}"
        )

    def start_erosion(self, file_path: str, params: ErosionParameters) -> None:
        if not Path(file_path).exists():
            raise FileNotFoundError(file_path)
        self._hardware.run_erosion(file_path, params)
