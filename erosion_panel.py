import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from robot_ui.async_action_executor import AsyncActionExecutor
from robot_ui.erosion_parameters import ErosionParameters
from robot_ui.robot_controller import RobotController


class ErosionPanel(ttk.LabelFrame):
    def __init__(self, master: tk.Misc, controller: RobotController, executor: AsyncActionExecutor) -> None:
        super().__init__(master, text="Процесс эрозии")
        self._controller = controller
        self._executor = executor
        self._file_path = tk.StringVar()
        self._buttons: list[ttk.Button] = []
        self._build()

    def _build(self) -> None:
        ttk.Entry(self, textvariable=self._file_path, width=50).grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        browse = ttk.Button(self, text="Обзор", command=self._browse)
        browse.grid(row=0, column=1, padx=4, pady=4)
        start = ttk.Button(self, text="Запуск", command=self._start)
        start.grid(row=1, column=0, padx=4, pady=4, sticky="w")
        self._buttons.extend([browse, start])
        self._text = tk.Text(self, width=60, height=10)
        self._text.grid(row=2, column=0, columnspan=2, padx=4, pady=4)

    def _browse(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("G-code", "*.gcode *.nc"), ("All files", "*.*")])
        if path:
            self._file_path.set(path)
            try:
                self._text.delete("1.0", tk.END)
                self._text.insert(tk.END, self._controller.gcode_summary(path))
            except Exception as error:
                messagebox.showerror("Ошибка", str(error))

    def _start(self) -> None:
        path = self._file_path.get().strip()
        if not path:
            messagebox.showerror("Ошибка", "Сначала выберите G-code файл")
            return
        self._set_buttons("disabled")
        params = ErosionParameters()
        self._executor.submit(lambda: self._controller.start_erosion(path, params), lambda e: self.after(0, self._finish, e))

    def _finish(self, error: BaseException | None) -> None:
        self._set_buttons("normal")
        if error:
            messagebox.showerror("Ошибка", str(error))
            return
        self._text.insert(tk.END, "\nПроцесс завершён")

    def _set_buttons(self, state: str) -> None:
        for button in self._buttons:
            button.configure(state=state)
