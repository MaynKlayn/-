import tkinter as tk
from tkinter import ttk

from robot_ui.async_action_executor import AsyncActionExecutor
from robot_ui.axis_panel import AxisPanel
from robot_ui.erosion_panel import ErosionPanel
from robot_ui.robot_controller import RobotController
from robot_ui.service_panel import ServicePanel


class MainWindow(tk.Tk):
    def __init__(self, controller: RobotController, executor: AsyncActionExecutor) -> None:
        super().__init__()
        self.title("Управление роботом")
        self.geometry("900x500")
        self._executor = executor
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)
        notebook.add(ErosionPanel(notebook, controller, executor), text="Процесс")
        notebook.add(AxisPanel(notebook, controller, executor), text="XYZ")
        notebook.add(ServicePanel(notebook, controller, executor), text="Сервис")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self) -> None:
        self._executor.shutdown()
        self.destroy()
