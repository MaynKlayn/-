import tkinter as tk
from tkinter import ttk

from robot_ui.app_logger import AppLogger
from robot_ui.async_action_executor import AsyncActionExecutor
from robot_ui.robot_controller import RobotController


class AxisPanel(ttk.LabelFrame):
    def __init__(self, master: tk.Misc, controller: RobotController, executor: AsyncActionExecutor, logger: AppLogger) -> None:
        super().__init__(master, text="Управление XYZ")
        self._controller = controller
        self._executor = executor
        self._logger = logger
        self._buttons: list[ttk.Button] = []
        self._build()

    def _build(self) -> None:
        for row, axis in enumerate(("X", "Y", "Z")):
            ttk.Label(self, text=axis).grid(row=row, column=0, padx=4, pady=4)
            for column, delta in enumerate((-10.0, -1.0, 1.0, 10.0), start=1):
                button = ttk.Button(self, text=f"{delta:+g}", command=lambda a=axis, d=delta: self._move(a, d))
                button.grid(row=row, column=column, padx=2, pady=2)
                self._buttons.append(button)
        self._status = ttk.Label(self, text=self._status_text())
        self._status.grid(row=4, column=0, columnspan=5, sticky="w", padx=4, pady=6)

    def _move(self, axis: str, delta: float) -> None:
        state = self._controller.state
        target = {"X": state.x, "Y": state.y, "Z": state.z}
        target[axis] += delta
        self._set_buttons("disabled")
        self._status.configure(text=f"Движение по {axis} выполняется...")
        self._logger.info(f"Запущено перемещение по оси {axis} на {delta:+g}")
        self._executor.submit(
            lambda: self._controller.move_xyz(target["X"], target["Y"], target["Z"]),
            lambda error: self.after(0, self._finish_move, axis, delta, error),
        )

    def _finish_move(self, axis: str, delta: float, error: BaseException | None) -> None:
        self._set_buttons("normal")
        if error:
            self._status.configure(text=str(error))
            self._logger.error(f"Не удалось переместить ось {axis}: {error}")
            return
        self._status.configure(text=self._status_text())
        self._logger.info(f"Перемещение по оси {axis} на {delta:+g} завершено")

    def _status_text(self) -> str:
        state = self._controller.state
        return f"X={state.x:.1f}  Y={state.y:.1f}  Z={state.z:.1f}"

    def _set_buttons(self, state: str) -> None:
        for button in self._buttons:
            button.configure(state=state)
