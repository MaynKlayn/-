import logging


class AppLogger:
    def __init__(self, name: str = "robot_ui") -> None:
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    def info(self, message: str) -> None:
        self._logger.info(message)
