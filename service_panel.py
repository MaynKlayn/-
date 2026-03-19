import tkinter as tk
from tkinter import ttk

from robot_ui.async_action_executor import AsyncActionExecutor
from robot_ui.robot_controller import RobotController


class ServicePanel(ttk.LabelFrame):
    def __init__(self, master: tk.Misc, controller: RobotController, executor: AsyncActionExecutor) -> None:
        super().__init__(master, text="Сервис")
        self._controller = controller
        self._executor = executor
        self._buttons: list[ttk.Button] = []
        self._build()

    def _build(self) -> None:
        actions = [
            ("Эрозия ON", lambda: self._controller.set_erosion(True)),
            ("Эрозия OFF", lambda: self._controller.set_erosion(False)),
            ("Вода ON", lambda: self._controller.set_water(True)),
            ("Вода OFF", lambda: self._controller.set_water(False)),
            ("Помпа IN", self._controller.toggle_pump_in),
            ("Помпа OUT", self._controller.toggle_pump_out),
        ]
        for row, (title, action) in enumerate(actions):
            button = ttk.Button(self, text=title, command=lambda a=action: self._run(a))
            button.grid(row=row, column=0, padx=4, pady=3, sticky="ew")
            self._buttons.append(button)
        self._status = ttk.Label(self, text="Готово")
        self._status.grid(row=len(actions), column=0, padx=4, pady=6, sticky="w")

    def _run(self, action) -> None:
        self._set_buttons("disabled")
        self._executor.submit(action, lambda error: self.after(0, self._finish, error))

    def _finish(self, error: BaseException | None) -> None:
        self._set_buttons("normal")
        self._status.configure(text=str(error) if error else "Команда выполнена")

    def _set_buttons(self, state: str) -> None:
        for button in self._buttons:
            button.configure(state=state)
