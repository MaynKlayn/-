import subprocess
import time
import os
from pathlib import Path
from datetime import datetime

import pyautogui
import psutil

try:
    import pygetwindow as gw
except ImportError:
    gw = None


class RealtimeInterfaceTester:
    def __init__(self) -> None:
        self.project_root = Path(__file__).resolve().parent
        self.main_script = self.project_root / "main.py"
        self.screenshots_dir = self.project_root / "ui_test_artifacts"
        self.screenshots_dir.mkdir(exist_ok=True)

        self.process = None
        self.window = None
        self.log_file = self.screenshots_dir / "ui_test_log.txt"

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.4

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        print(line)
        with open(self.log_file, "a", encoding="utf-8") as file:
            file.write(line + "\n")

    def take_screenshot(self, name: str) -> None:
        filename = self.screenshots_dir / f"{name}_{int(time.time())}.png"
        image = pyautogui.screenshot()
        image.save(filename)
        self.log(f"Скриншот сохранён: {filename.name}")

    def start_program(self) -> None:
        if not self.main_script.exists():
            raise FileNotFoundError(f"Не найден файл: {self.main_script}")

        self.log("Запускаю main.py")
        self.process = subprocess.Popen(
            ["python", str(self.main_script)],
            cwd=str(self.project_root)
        )

    def find_window(self, timeout: float = 15.0) -> None:
        if gw is None:
            raise RuntimeError("Не установлен pygetwindow")

        self.log("Ищу окно программы")
        end_time = time.time() + timeout

        while time.time() < end_time:
            windows = gw.getAllTitles()
            for title in windows:
                if "Управление роботом" in title or "роботом" in title.lower():
                    candidates = gw.getWindowsWithTitle(title)
                    if candidates:
                        self.window = candidates[0]
                        self.window.activate()
                        time.sleep(1.0)
                        self.log(f"Окно найдено: {title}")
                        return
            time.sleep(0.5)

        raise RuntimeError("Окно программы не найдено")

    def ensure_window_alive(self) -> None:
        if self.process is None:
            raise RuntimeError("Процесс не был запущен")

        if self.process.poll() is not None:
            raise RuntimeError("Программа завершилась раньше времени")

        self.log("Процесс жив, приложение не упало")

    def center_of_window(self) -> tuple[int, int]:
        if self.window is None:
            raise RuntimeError("Окно не найдено")

        x = self.window.left + self.window.width // 2
        y = self.window.top + self.window.height // 2
        return x, y

    def click_relative(self, rel_x: float, rel_y: float, note: str) -> None:
        if self.window is None:
            raise RuntimeError("Окно не найдено")

        x = int(self.window.left + self.window.width * rel_x)
        y = int(self.window.top + self.window.height * rel_y)

        self.log(f"Клик: {note} ({x}, {y})")
        pyautogui.click(x, y)
        time.sleep(0.8)

    def double_click_relative(self, rel_x: float, rel_y: float, note: str) -> None:
        if self.window is None:
            raise RuntimeError("Окно не найдено")

        x = int(self.window.left + self.window.width * rel_x)
        y = int(self.window.top + self.window.height * rel_y)

        self.log(f"Двойной клик: {note} ({x}, {y})")
        pyautogui.doubleClick(x, y)
        time.sleep(0.8)

    def press_key(self, key: str, note: str) -> None:
        self.log(f"Нажатие клавиши: {note} [{key}]")
        pyautogui.press(key)
        time.sleep(0.5)

    def type_text(self, text: str, note: str) -> None:
        self.log(f"Ввод текста: {note}")
        pyautogui.write(text, interval=0.03)
        time.sleep(0.7)

    def check_not_frozen(self, seconds: float = 2.0) -> None:
        self.log("Проверяю, что окно не зависло")
        start = time.time()

        while time.time() - start < seconds:
            self.ensure_window_alive()
            if self.window is not None:
                try:
                    _ = self.window.title
                except Exception as error:
                    raise RuntimeError(f"Окно не отвечает: {error}")
            time.sleep(0.3)

        self.log("Окно отвечает, признаков зависания нет")

    def test_tabs(self) -> None:
        self.log("Тестирую вкладки")
        self.take_screenshot("before_tabs")

        # Эти координаты приблизительные.
        # 1-я вкладка
        self.click_relative(0.18, 0.08, "Вкладка Процесс")
        self.take_screenshot("tab_process")

        # 2-я вкладка
        self.click_relative(0.33, 0.08, "Вкладка XYZ")
        self.take_screenshot("tab_xyz")

        # 3-я вкладка
        self.click_relative(0.48, 0.08, "Вкладка Сервис")
        self.take_screenshot("tab_service")

        self.log("Вкладки переключаются")

    def test_xyz_buttons(self) -> None:
        self.log("Тестирую XYZ-панель")
        self.click_relative(0.33, 0.08, "Открыть XYZ вкладку")
        self.take_screenshot("xyz_before")

        # Координаты примерные и зависят от размеров окна.
        self.click_relative(0.20, 0.28, "Кнопка X+")
        self.check_not_frozen(1.5)
        self.take_screenshot("xyz_after_x_plus")

        self.click_relative(0.35, 0.28, "Кнопка Y+")
        self.check_not_frozen(1.5)
        self.take_screenshot("xyz_after_y_plus")

        self.log("Кнопки XYZ нажимаются, окно не зависает")

    def test_service_buttons(self) -> None:
        self.log("Тестирую сервисную панель")
        self.click_relative(0.48, 0.08, "Открыть вкладку Сервис")
        self.take_screenshot("service_before")

        self.click_relative(0.22, 0.27, "Кнопка Эрозия ON")
        self.check_not_frozen(1.5)
        self.take_screenshot("service_after_erosion_on")

        self.log("Сервисная команда вызвана")

    def test_process_tab_with_demo_file(self) -> None:
        self.log("Тестирую вкладку процесса")

        demo_gcode = self.project_root / "demo_test.gcode"
        demo_gcode.write_text("G1 X0 Y0 Z0\nG1 X1 Y2 Z3\n", encoding="utf-8")

        self.click_relative(0.18, 0.08, "Открыть вкладку Процесс")
        self.take_screenshot("process_before")

        # Поле ввода пути
        self.click_relative(0.22, 0.20, "Поле пути к G-code")
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.2)
        self.press_key("backspace", "Очистить поле")
        self.type_text(str(demo_gcode), "Вставить путь к demo_test.gcode")

        # Кнопка Запуск
        self.click_relative(0.16, 0.31, "Кнопка Запуск")
        self.check_not_frozen(2.5)
        self.take_screenshot("process_after_start")

        self.log("Процесс запуска обработан")

    def cleanup_demo_file(self) -> None:
        demo_gcode = self.project_root / "demo_test.gcode"
        if demo_gcode.exists():
            demo_gcode.unlink()
            self.log("Временный demo_test.gcode удалён")

    def stop_program(self) -> None:
        if self.process is None:
            return

        self.log("Завершаю приложение")
        try:
            parent = psutil.Process(self.process.pid)
            children = parent.children(recursive=True)
            for child in children:
                child.terminate()
            parent.terminate()
        except Exception as error:
            self.log(f"Мягкое завершение не удалось: {error}")

        time.sleep(1.0)

        if self.process.poll() is None:
            try:
                self.process.kill()
                self.log("Процесс принудительно завершён")
            except Exception as error:
                self.log(f"Не удалось завершить процесс: {error}")
        else:
            self.log("Приложение завершено корректно")

    def run(self) -> None:
        try:
            self.log("=== СТАРТ ТЕСТА ИНТЕРФЕЙСА ===")
            self.start_program()
            time.sleep(2.0)
            self.find_window()
            self.ensure_window_alive()
            self.take_screenshot("app_started")

            self.test_tabs()
            self.test_xyz_buttons()
            self.test_service_buttons()
            self.test_process_tab_with_demo_file()

            self.ensure_window_alive()
            self.take_screenshot("final_state")
            self.log("=== ИТОГ: тест интерфейса завершён успешно ===")

        except Exception as error:
            self.log(f"=== ОШИБКА ТЕСТА: {error} ===")
            self.take_screenshot("error_state")
            raise
        finally:
            self.cleanup_demo_file()
            self.stop_program()


if __name__ == "__main__":
    tester = RealtimeInterfaceTester()
    tester.run()