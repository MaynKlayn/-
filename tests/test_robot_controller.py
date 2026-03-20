from pathlib import Path

from robot_ui.app_logger import AppLogger
from robot_ui.erosion_parameters import ErosionParameters
from robot_ui.gcode_parser import GCodeParser
from robot_ui.robot_controller import RobotController


class FakeHardware:
    def __init__(self) -> None:
        self.xyz = None
        self.joints = None
        self.erosion = None
        self.water = None
        self.pump_in = False
        self.pump_out = False
        self.erosion_run = None

    def move_xyz(self, x, y, z):
        self.xyz = (x, y, z)

    def move_joints(self, joints):
        self.joints = list(joints)

    def set_erosion(self, enabled):
        self.erosion = enabled

    def set_water(self, enabled):
        self.water = enabled

    def toggle_pump_in(self):
        self.pump_in = not self.pump_in
        return self.pump_in

    def toggle_pump_out(self):
        self.pump_out = not self.pump_out
        return self.pump_out

    def run_erosion(self, file_path, params):
        self.erosion_run = (file_path, params.mode)


def test_controller_updates_state(tmp_path: Path) -> None:
    file_path = tmp_path / "demo.gcode"
    file_path.write_text("G1 X1 Y2 Z3\n", encoding="utf-8")
    hardware = FakeHardware()
    controller = RobotController(hardware, GCodeParser(), AppLogger("test"))
    controller.move_xyz(1, 2, 3)
    controller.move_joint(2, 45)
    controller.set_erosion(True)
    controller.set_water(True)
    assert controller.toggle_pump_in() is True
    assert controller.toggle_pump_out() is True
    controller.start_erosion(str(file_path), ErosionParameters())
    assert hardware.xyz == (1, 2, 3)
    assert hardware.joints[2] == 45
    assert controller.state.erosion_enabled is True
    assert controller.state.water_enabled is True
    assert hardware.erosion_run == (str(file_path), "test")
