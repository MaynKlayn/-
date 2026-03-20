import logging
from typing import Callable


class AppLogger:
    def __init__(self, name: str = "robot_ui") -> None:
        self._logger = logging.getLogger(name)
        self._subscribers: list[Callable[[str], None]] = []
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    def subscribe(self, callback: Callable[[str], None]) -> None:
        self._subscribers.append(callback)

    def info(self, message: str) -> None:
        self._logger.info(message)
        self._notify(message)

    def error(self, message: str) -> None:
        self._logger.error(message)
        self._notify(f"Ошибка: {message}")

    def _notify(self, message: str) -> None:
        for callback in self._subscribers:
            callback(message)
