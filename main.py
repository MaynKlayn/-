from robot_ui.app_logger import AppLogger
from robot_ui.async_action_executor import AsyncActionExecutor
from robot_ui.gcode_parser import GCodeParser
from robot_ui.main_window import MainWindow
from robot_ui.robot_controller import RobotController
from robot_ui.stub_robot_hardware import StubRobotHardware


def build_application() -> MainWindow:
    logger = AppLogger()
    controller = RobotController(StubRobotHardware(logger), GCodeParser(), logger)
    return MainWindow(controller, AsyncActionExecutor())


if __name__ == "__main__":
    build_application().mainloop()
