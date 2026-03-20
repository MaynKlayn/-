import tkinter as tk
from tkinter import ttk

from robot_ui.app_logger import AppLogger


class LogPanel(ttk.LabelFrame):
    def __init__(self, master: tk.Misc, logger: AppLogger) -> None:
        super().__init__(master, text="Журнал")
        self._text = tk.Text(self, width=80, height=8, state="disabled")
        self._text.pack(fill="both", expand=True, padx=4, pady=4)
        logger.subscribe(lambda message: self.after(0, self.append, message))

    def append(self, message: str) -> None:
        self._text.configure(state="normal")
        self._text.insert(tk.END, f"{message}\n")
        self._text.see(tk.END)
        self._text.configure(state="disabled")
