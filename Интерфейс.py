# robot_ui.py
# -*- coding: utf-8 -*-
"""
Robot UI (single-file, GitHub-ready)

Требования выполнены:
- заглушки zaglushka_* с time.sleep(1)
- UI не зависает (QThreadPool)
- кнопки блокируются на время выполнения команды

Запуск:
  pip install PySide6 numpy matplotlib
  python robot_ui.py
"""

from __future__ import annotations

import os
import re
import time
import queue
from dataclasses import dataclass
from typing import Protocol, List, Tuple, Optional, runtime_checkable

import numpy as np

from PySide6.QtCore import QObject, Signal, Slot, QRunnable, QThreadPool, Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget,
    QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QDoubleSpinBox, QTextEdit, QFileDialog, QMessageBox, QProgressBar, QGridLayout, QLineEdit, QComboBox
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# =============================================================================
# 1) DOMAIN (интерфейсы / контракты)
# =============================================================================

@dataclass(frozen=True)
class MotionState:
    x: float
    y: float
    z: float
    joints: List[float]  # len=6


@dataclass(frozen=True)
class ErosionParams:
    electrode_diameter: float
    electrode_length: float
    erosion_time: float
    erosion_up_time: float
    erosion_depth: float
    erosion_speed: float
    mode: str  # "emulated" | "work" | "test"


@runtime_checkable
class IRobotMotion(Protocol):
    def set_speed(self, percent: float) -> None: ...
    def set_xyz(self, x: float, y: float, z: float) -> None: ...
    def set_joints(self, joints: List[float]) -> None: ...
    def home_xyz(self) -> None: ...
    def home_joints(self) -> None: ...


@runtime_checkable
class IErosionProcess(Protocol):
    def start(self, gcode_filename: str, params: ErosionParams) -> None: ...
    def pause(self) -> None: ...
    def resume(self) -> None: ...
    def stop(self) -> None: ...


@runtime_checkable
class IWaterSystem(Protocol):
    def water_on(self) -> None: ...
    def water_off(self) -> None: ...
    def pump_in_toggle(self) -> None: ...
    def pump_out_toggle(self) -> None: ...


# =============================================================================
# 2) INFRA (лог + асинхронный раннер)
# =============================================================================

class QueueLogger:
    """Логгер: пишет в stdout и в очередь (для UI)."""
    def __init__(self, q: queue.Queue):
        self.q = q

    def info(self, msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] INFO: {msg}"
        print(line)
        self.q.put(line)

    def error(self, msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] ERROR: {msg}"
        print(line)
        self.q.put(line)


class TaskSignals(QObject):
    finished = Signal()
    failed = Signal(str)


class BackgroundTask(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = TaskSignals()

    @Slot()
    def run(self):
        try:
            self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit()
        except Exception as e:
            self.signals.failed.emit(str(e))


class AsyncCommandRunner:
    """Запуск задач в фоне + блокировка кнопки на время выполнения."""
    def __init__(self):
        self.pool = QThreadPool.globalInstance()

    def run_with_button_lock(self, button: QPushButton, fn, *args, on_error=None, on_done=None, **kwargs):
        button.setEnabled(False)

        task = BackgroundTask(fn, *args, **kwargs)

        def _unlock():
            button.setEnabled(True)
            if on_done:
                on_done()

        def _fail(msg: str):
            button.setEnabled(True)
            if on_error:
                on_error(msg)

        task.signals.finished.connect(_unlock)
        task.signals.failed.connect(_fail)

        self.pool.start(task)
        return task


# =============================================================================
# 3) ADAPTERS (заглушки + классы, которые их вызывают)
# =============================================================================

# --- Заглушки по требованию задания ---
def zaglushka_set_speed(percent: float): time.sleep(1)
def zaglushka_set_xyz(x: float, y: float, z: float): time.sleep(1)
def zaglushka_set_joints(joints: List[float]): time.sleep(1)
def zaglushka_home_xyz(): time.sleep(1)
def zaglushka_home_joints(): time.sleep(1)

def zaglushka_erosion_start(filename: str, params: ErosionParams): time.sleep(1)
def zaglushka_erosion_pause(): time.sleep(1)
def zaglushka_erosion_resume(): time.sleep(1)
def zaglushka_erosion_stop(): time.sleep(1)

def zaglushka_water_on(): time.sleep(1)
def zaglushka_water_off(): time.sleep(1)
def zaglushka_pump_in_toggle(): time.sleep(1)
def zaglushka_pump_out_toggle(): time.sleep(1)


class StubRobotMotion(IRobotMotion):
    def __init__(self, logger: QueueLogger):
        self.log = logger

    def set_speed(self, percent: float) -> None:
        self.log.info(f"Stub: set_speed({percent})")
        zaglushka_set_speed(percent)

    def set_xyz(self, x: float, y: float, z: float) -> None:
        self.log.info(f"Stub: set_xyz(x={x:.2f}, y={y:.2f}, z={z:.2f})")
        zaglushka_set_xyz(x, y, z)

    def set_joints(self, joints: List[float]) -> None:
        self.log.info(f"Stub: set_joints({[round(j,2) for j in joints]})")
        zaglushka_set_joints(joints)

    def home_xyz(self) -> None:
        self.log.info("Stub: home_xyz()")
        zaglushka_home_xyz()

    def home_joints(self) -> None:
        self.log.info("Stub: home_joints()")
        zaglushka_home_joints()


class StubErosionProcess(IErosionProcess):
    def __init__(self, logger: QueueLogger):
        self.log = logger
        self.running = False
        self.paused = False

    def start(self, gcode_filename: str, params: ErosionParams) -> None:
        self.log.info(f"Stub: erosion.start(file='{gcode_filename}', mode={params.mode})")
        self.running = True
        self.paused = False
        zaglushka_erosion_start(gcode_filename, params)

    def pause(self) -> None:
        self.log.info("Stub: erosion.pause()")
        self.paused = True
        zaglushka_erosion_pause()

    def resume(self) -> None:
        self.log.info("Stub: erosion.resume()")
        self.paused = False
        zaglushka_erosion_resume()

    def stop(self) -> None:
        self.log.info("Stub: erosion.stop()")
        self.running = False
        self.paused = False
        zaglushka_erosion_stop()


class StubWaterSystem(IWaterSystem):
    def __init__(self, logger: QueueLogger):
        self.log = logger
        self.water_state = False
        self.pump_in = False
        self.pump_out = False

    def water_on(self) -> None:
        self.log.info("Stub: water_on()")
        self.water_state = True
        zaglushka_water_on()

    def water_off(self) -> None:
        self.log.info("Stub: water_off()")
        self.water_state = False
        zaglushka_water_off()

    def pump_in_toggle(self) -> None:
        self.pump_in = not self.pump_in
        self.log.info(f"Stub: pump_in_toggle() -> {self.pump_in}")
        zaglushka_pump_in_toggle()

    def pump_out_toggle(self) -> None:
        self.pump_out = not self.pump_out
        self.log.info(f"Stub: pump_out_toggle() -> {self.pump_out}")
        zaglushka_pump_out_toggle()


# =============================================================================
# 4) SERVICES (логика сценариев)
# =============================================================================

Point3 = Tuple[float, float, float]


@dataclass(frozen=True)
class GCodeInfo:
    filename: str
    points_count: int
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float
    path_length: float


class GCodeService:
    def parse_points(self, filename: str) -> List[Point3]:
        points: List[Point3] = []
        cx, cy, cz = 0.0, 0.0, 0.0

        with open(filename, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(";"):
                    continue
                if ";" in line:
                    line = line.split(";", 1)[0].strip()

                if line.startswith(("G0", "G00", "G1", "G01")):
                    x = self._extract(line, "X", cx)
                    y = self._extract(line, "Y", cy)
                    z = self._extract(line, "Z", cz)
                    if (x, y, z) != (cx, cy, cz):
                        points.append((x, y, z))
                        cx, cy, cz = x, y, z

        return points if points else [(0.0, 0.0, 0.0)]

    def build_info(self, filename: str, points: List[Point3]) -> GCodeInfo:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        zs = [p[2] for p in points]
        length = self.path_length(points)

        return GCodeInfo(
            filename=filename,
            points_count=len(points),
            x_min=min(xs), x_max=max(xs),
            y_min=min(ys), y_max=max(ys),
            z_min=min(zs), z_max=max(zs),
            path_length=length
        )

    def path_length(self, points: List[Point3]) -> float:
        if len(points) < 2:
            return 0.0
        total = 0.0
        for i in range(1, len(points)):
            x1, y1, z1 = points[i-1]
            x2, y2, z2 = points[i]
            total += float(np.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2))
        return total

    def _extract(self, line: str, axis: str, default: float) -> float:
        m = re.search(rf"{axis}([+-]?\d*\.?\d+)", line)
        return float(m.group(1)) if m else default


class MotionBus(QObject):
    state_changed = Signal(object)  # MotionState


class MotionService:
    def __init__(self, robot: IRobotMotion, logger: QueueLogger, x0: float, y0: float, z0: float):
        self.robot = robot
        self.log = logger
        self.x0, self.y0, self.z0 = x0, y0, z0
        self._state = MotionState(x=x0, y=y0, z=z0, joints=[0, 0, 0, 0, 0, 0])
        self.bus = MotionBus()

    @property
    def state(self) -> MotionState:
        return self._state

    def set_xyz(self, x: float, y: float, z: float) -> None:
        self.robot.set_xyz(x, y, z)
        self._state = MotionState(x=x, y=y, z=z, joints=self._state.joints)
        self.bus.state_changed.emit(self._state)

    def home_xyz(self) -> None:
        self.robot.home_xyz()
        self._state = MotionState(x=self.x0, y=self.y0, z=self.z0, joints=self._state.joints)
        self.bus.state_changed.emit(self._state)


class ErosionBus(QObject):
    progress = Signal(int)
    time_remaining = Signal(str)
    status = Signal(str, str)
    finished = Signal()
    started = Signal()


class ErosionService:
    """Процесс эрозии: низкоуровневый start/pause/stop + имитация прогресса для UI."""
    def __init__(self, erosion: IErosionProcess, logger: QueueLogger):
        self.ee = erosion
        self.log = logger
        self.bus = ErosionBus()
        self._running = False
        self._paused = False
        self._stop_requested = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_paused(self) -> bool:
        return self._paused

    def start(self, filename: str, params: ErosionParams) -> None:
        self._running = True
        self._paused = False
        self._stop_requested = False

        self.bus.status.emit("ПРОЦЕСС ВЫПОЛНЯЕТСЯ", "#27ae60")
        self.bus.started.emit()

        self.log.info(
            f"Start erosion: file={os.path.basename(filename)}, mode={params.mode}, "
            f"t={params.erosion_time}s, depth={params.erosion_depth}mm, speed={params.erosion_speed}mm/s"
        )

        # низкоуровневый старт (заглушка тоже sleep(1))
        self.ee.start(filename, params)

        # имитация прогресса
        total = max(1.0, float(params.erosion_time))
        t0 = time.time()
        while True:
            if self._stop_requested:
                break
            if self._paused:
                time.sleep(0.1)
                continue

            elapsed = time.time() - t0
            p = int(min(100, (elapsed / total) * 100))
            remaining = max(0, total - elapsed)

            self.bus.progress.emit(p)
            self.bus.time_remaining.emit(f"{int(remaining//60):02d}:{int(remaining%60):02d}")

            if p >= 100:
                break

            time.sleep(0.2)

        self._running = False
        if self._stop_requested:
            self.bus.status.emit("ПРОЦЕСС ОСТАНОВЛЕН", "#e74c3c")
            self.bus.time_remaining.emit("Остановлено")
            self.bus.progress.emit(0)
        else:
            self.bus.status.emit("ПРОЦЕСС ЗАВЕРШЕН", "#3498db")
            self.bus.time_remaining.emit("Завершено")
            self.bus.progress.emit(100)

        self.bus.finished.emit()

    def pause(self) -> None:
        if not self._running:
            return
        self._paused = True
        self.ee.pause()
        self.bus.status.emit("ПРОЦЕСС НА ПАУЗЕ", "#f39c12")
        self.log.info("Erosion paused")

    def resume(self) -> None:
        if not self._running:
            return
        self._paused = False
        self.ee.resume()
        self.bus.status.emit("ПРОЦЕСС ВЫПОЛНЯЕТСЯ", "#27ae60")
        self.log.info("Erosion resumed")

    def stop(self) -> None:
        if not self._running:
            return
        self._stop_requested = True
        self._paused = False
        self.ee.stop()
        self.log.info("Erosion stop requested")


class WaterService:
    def __init__(self, water: IWaterSystem, logger: QueueLogger):
        self.water = water
        self.log = logger
        self._water_state = False

    def water_on(self) -> None:
        self.water.water_on()
        self._water_state = True

    def water_off(self) -> None:
        self.water.water_off()
        self._water_state = False

    def pump_in_toggle(self) -> None:
        self.water.pump_in_toggle()

    def pump_out_toggle(self) -> None:
        self.water.pump_out_toggle()

    def status_text(self, motion_state: MotionState) -> str:
        return (
            "Текущий статус системы:\n"
            f"- X: {motion_state.x:.2f} мм\n"
            f"- Y: {motion_state.y:.2f} мм\n"
            f"- Z: {motion_state.z:.2f} мм\n"
            f"- Суставы: {', '.join([f'{j:.1f}°' for j in motion_state.joints])}\n"
            f"- Вода: {'включена' if self._water_state else 'выключена'}\n"
        )


# =============================================================================
# 5) UI
# =============================================================================

class ErosionTab(QWidget):
    def __init__(self, motion: MotionService, erosion: ErosionService, water: WaterService,
                 gcode: GCodeService, runner: AsyncCommandRunner, logger: QueueLogger, log_q: queue.Queue):
        super().__init__()
        self.motion = motion
        self.erosion = erosion
        self.water = water
        self.gcode = gcode
        self.runner = runner
        self.log = logger
        self.log_q = log_q

        self.points: List[Point3] = []
        self._build()
        self._wire()

    def _build(self):
        root = QVBoxLayout(self)

        # --- GCODE ---
        gbox = QGroupBox("G-code")
        gl = QVBoxLayout(gbox)

        row = QHBoxLayout()
        self.gcode_edit = QLineEdit()
        self.gcode_edit.setPlaceholderText("Выберите .gcode/.nc файл…")
        self.browse_btn = QPushButton("Обзор")
        row.addWidget(self.gcode_edit, 1)
        row.addWidget(self.browse_btn)
        gl.addLayout(row)

        self.ginfo = QTextEdit()
        self.ginfo.setReadOnly(True)
        gl.addWidget(self.ginfo)

        # plot
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.canvas = FigureCanvas(self.fig)
        gl.addWidget(self.canvas)

        root.addWidget(gbox)

        # --- Params ---
        pbox = QGroupBox("Параметры эрозии")
        pl = QGridLayout(pbox)

        def mkspin(r, label, key, dv, mn, mx, suffix):
            pl.addWidget(QLabel(label), r, 0)
            sp = QDoubleSpinBox()
            sp.setRange(mn, mx)
            sp.setValue(dv)
            sp.setSuffix(suffix)
            sp.setSingleStep(0.1)
            pl.addWidget(sp, r, 1)
            return sp

        self.sp_d = mkspin(0, "Толщина электрода", "d", 2.0, 0.1, 10.0, " мм")
        self.sp_L = mkspin(1, "Длина электрода", "L", 100.0, 10.0, 500.0, " мм")
        self.sp_t = mkspin(2, "Время прожига", "t", 10.0, 1.0, 600.0, " с")
        self.sp_up = mkspin(3, "Время подъёма", "up", 5.0, 1.0, 300.0, " с")
        self.sp_depth = mkspin(4, "Глубина прожига", "depth", 0.1, 0.01, 5.0, " мм")
        self.sp_speed = mkspin(5, "Скорость", "speed", 10.0, 1.0, 100.0, " мм/с")

        pl.addWidget(QLabel("Режим"), 6, 0)
        self.mode = QComboBox()
        self.mode.addItems(["emulated", "work", "test"])
        pl.addWidget(self.mode, 6, 1)

        root.addWidget(pbox)

        # --- Controls ---
        cbox = QGroupBox("Управление процессом")
        cl = QVBoxLayout(cbox)

        self.status = QLabel("Готов к запуску")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("font-weight: bold; padding: 8px; border-radius: 6px; background: #ecf0f1;")
        cl.addWidget(self.status)

        pr = QHBoxLayout()
        self.pb = QProgressBar()
        self.pb.setRange(0, 100)
        self.time_lbl = QLabel("Осталось: --:--")
        pr.addWidget(self.pb, 1)
        pr.addWidget(self.time_lbl)
        cl.addLayout(pr)

        btns = QHBoxLayout()
        self.start_btn = QPushButton("Запуск")
        self.pause_btn = QPushButton("⏸ Пауза")
        self.stop_btn = QPushButton("Стоп")
        self.pause_btn.setEnabled(False)
        btns.addWidget(self.start_btn)
        btns.addWidget(self.pause_btn)
        btns.addWidget(self.stop_btn)
        btns.addStretch()
        cl.addLayout(btns)

        root.addWidget(cbox)

        # --- Water ---
        wbox = QGroupBox("Вода / помпы")
        wl = QHBoxLayout(wbox)
        self.water_on_btn = QPushButton("Включить воду")
        self.water_off_btn = QPushButton("Выключить воду")
        self.pump_in_btn = QPushButton("Тоггл закачка")
        self.pump_out_btn = QPushButton("Тоггл откачка")
        wl.addWidget(self.water_on_btn)
        wl.addWidget(self.water_off_btn)
        wl.addWidget(self.pump_in_btn)
        wl.addWidget(self.pump_out_btn)
        root.addWidget(wbox)

        # --- Logs ---
        lbox = QGroupBox("Логи")
        ll = QVBoxLayout(lbox)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        ll.addWidget(self.log_text)
        root.addWidget(lbox, 1)

    def _wire(self):
        self.browse_btn.clicked.connect(self._select_gcode)

        self.start_btn.clicked.connect(self._start)
        self.pause_btn.clicked.connect(self._pause_toggle)
        self.stop_btn.clicked.connect(self._stop)

        self.water_on_btn.clicked.connect(lambda: self.runner.run_with_button_lock(self.water_on_btn, self.water.water_on))
        self.water_off_btn.clicked.connect(lambda: self.runner.run_with_button_lock(self.water_off_btn, self.water.water_off))
        self.pump_in_btn.clicked.connect(lambda: self.runner.run_with_button_lock(self.pump_in_btn, self.water.pump_in_toggle))
        self.pump_out_btn.clicked.connect(lambda: self.runner.run_with_button_lock(self.pump_out_btn, self.water.pump_out_toggle))

        # erosion signals
        self.erosion.bus.progress.connect(self.pb.setValue)
        self.erosion.bus.time_remaining.connect(self._set_time)
        self.erosion.bus.status.connect(self._set_status)
        self.erosion.bus.started.connect(lambda: self.pause_btn.setEnabled(True))
        self.erosion.bus.finished.connect(lambda: self.pause_btn.setEnabled(False))

        # simple log pump (UI timer-less): on every action we also try to drain queue
        # (на практике можно сделать QTimer, но здесь достаточно)
        self._drain_logs()

    def _drain_logs(self):
        try:
            while True:
                msg = self.log_q.get_nowait()
                self.log_text.append(msg)
        except queue.Empty:
            pass

    @Slot()
    def _select_gcode(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Выберите G-code", "", "G-code files (*.gcode *.nc);;All files (*.*)")
        if not fn:
            return
        if not fn.lower().endswith((".gcode", ".nc")):
            QMessageBox.critical(self, "Ошибка", "Нужен файл .gcode или .nc")
            return
        self.gcode_edit.setText(fn)
        try:
            self.points = self.gcode.parse_points(fn)
            info = self.gcode.build_info(fn, self.points)
            self.ginfo.setPlainText(
                f"Файл: {os.path.basename(info.filename)}\n"
                f"Точек: {info.points_count}\n"
                f"X: {info.x_min:.2f} .. {info.x_max:.2f}\n"
                f"Y: {info.y_min:.2f} .. {info.y_max:.2f}\n"
                f"Z: {info.z_min:.2f} .. {info.z_max:.2f}\n"
                f"Длина траектории: {info.path_length:.2f} мм\n"
            )
            self._draw()
            self.log.info("G-code loaded")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать G-code: {e}")
        finally:
            self._drain_logs()

    def _draw(self):
        self.ax.clear()
        pts = np.array(self.points, dtype=float)
        if len(pts) >= 1:
            self.ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], linewidth=2, alpha=0.7)
            self.ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], s=10, alpha=0.6)
        self.ax.set_xlabel("X (мм)")
        self.ax.set_ylabel("Y (мм)")
        self.ax.set_zlabel("Z (мм)")
        self.ax.set_title("Траектория G-code")
        self.canvas.draw()

    def _params(self) -> ErosionParams:
        return ErosionParams(
            electrode_diameter=self.sp_d.value(),
            electrode_length=self.sp_L.value(),
            erosion_time=self.sp_t.value(),
            erosion_up_time=self.sp_up.value(),
            erosion_depth=self.sp_depth.value(),
            erosion_speed=self.sp_speed.value(),
            mode=self.mode.currentText(),
        )

    @Slot()
    def _start(self):
        fn = self.gcode_edit.text().strip()
        if not fn or not os.path.exists(fn):
            QMessageBox.critical(self, "Ошибка", "Не выбран G-code файл")
            return
        if not self.points:
            QMessageBox.critical(self, "Ошибка", "Сначала загрузите G-code")
            return

        params = self._params()

        self.pause_btn.setText("⏸ Пауза")
        self.pause_btn.setStyleSheet("")

        self.runner.run_with_button_lock(
            self.start_btn,
            self.erosion.start,
            fn,
            params,
            on_error=lambda msg: QMessageBox.critical(self, "Ошибка", msg),
            on_done=self._drain_logs
        )

    @Slot()
    def _pause_toggle(self):
        if not self.erosion.is_running:
            return
        if not self.erosion.is_paused:
            self.erosion.pause()
            self.pause_btn.setText("▶ Продолжить")
            self.pause_btn.setStyleSheet("background: #3498db; color: white; font-weight: bold;")
        else:
            self.erosion.resume()
            self.pause_btn.setText("⏸ Пауза")
            self.pause_btn.setStyleSheet("")
        self._drain_logs()

    @Slot()
    def _stop(self):
        self.erosion.stop()
        self.pb.setValue(0)
        self.time_lbl.setText("Остановлено")
        self._drain_logs()

    @Slot(str)
    def _set_time(self, s: str):
        self.time_lbl.setText(f"Осталось: {s}" if ":" in s else s)
        self._drain_logs()

    @Slot(str, str)
    def _set_status(self, text: str, color: str):
        self.status.setText(text)
        self.status.setStyleSheet(f"font-weight: bold; padding: 8px; border-radius: 6px; background: {color};")
        self._drain_logs()


class ServiceTab(QWidget):
    def __init__(self, motion: MotionService, water: WaterService, runner: AsyncCommandRunner):
        super().__init__()
        self.motion = motion
        self.water = water
        self.runner = runner

        self._build()
        self._wire()
        self._refresh_status(self.motion.state)

    def _build(self):
        root = QVBoxLayout(self)

        mbox = QGroupBox("Движение XYZ")
        ml = QGridLayout(mbox)

        self.spX = QDoubleSpinBox(); self.spX.setRange(-1000, 1000); self.spX.setDecimals(2)
        self.spY = QDoubleSpinBox(); self.spY.setRange(-1000, 1000); self.spY.setDecimals(2)
        self.spZ = QDoubleSpinBox(); self.spZ.setRange(-1000, 1000); self.spZ.setDecimals(2)

        ml.addWidget(QLabel("X (мм)"), 0, 0); ml.addWidget(self.spX, 0, 1)
        ml.addWidget(QLabel("Y (мм)"), 1, 0); ml.addWidget(self.spY, 1, 1)
        ml.addWidget(QLabel("Z (мм)"), 2, 0); ml.addWidget(self.spZ, 2, 1)

        self.set_xyz_btn = QPushButton("Установить XYZ")
        self.home_xyz_btn = QPushButton("Вернуться в ноль (XYZ)")
        self.home_xyz_btn.setStyleSheet("background-color: #ff6b6b; color: white; font-weight: bold;")

        ml.addWidget(self.set_xyz_btn, 3, 0, 1, 2)
        ml.addWidget(self.home_xyz_btn, 4, 0, 1, 2)

        root.addWidget(mbox)

        sbox = QGroupBox("Статус")
        sl = QVBoxLayout(sbox)
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        sl.addWidget(self.status_text)
        root.addWidget(sbox, 1)

    def _wire(self):
        self.motion.bus.state_changed.connect(self._refresh_status)

        self.set_xyz_btn.clicked.connect(self._set_xyz)
        self.home_xyz_btn.clicked.connect(lambda: self.runner.run_with_button_lock(self.home_xyz_btn, self.motion.home_xyz))

    @Slot(object)
    def _refresh_status(self, st: MotionState):
        self.spX.setValue(st.x)
        self.spY.setValue(st.y)
        self.spZ.setValue(st.z)
        self.status_text.setPlainText(self.water.status_text(st))

    @Slot()
    def _set_xyz(self):
        x, y, z = self.spX.value(), self.spY.value(), self.spZ.value()
        self.runner.run_with_button_lock(self.set_xyz_btn, self.motion.set_xyz, x, y, z)


class MainWindow(QMainWindow):
    def __init__(self, motion: MotionService, erosion: ErosionService, water: WaterService,
                 gcode: GCodeService, runner: AsyncCommandRunner, logger: QueueLogger, log_q: queue.Queue):
        super().__init__()
        self.setWindowTitle("Управление электроэрозионной установкой (single-file)")
        self.setMinimumSize(1200, 720)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        tabs.addTab(ErosionTab(motion, erosion, water, gcode, runner, logger, log_q), "Процесс эрозии")
        tabs.addTab(ServiceTab(motion, water, runner), "Сервис")

        self.setStyleSheet("""
            QMainWindow { background-color: #f0f0f0; }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)


# =============================================================================
# 6) Composition Root (сборка системы)
# =============================================================================

X0, Y0, Z0 = 430.0, 0.0, 277.0  # твои константы

def build_system():
    log_q = queue.Queue()
    logger = QueueLogger(log_q)

    robot = StubRobotMotion(logger)
    ee = StubErosionProcess(logger)
    water_hw = StubWaterSystem(logger)

    runner = AsyncCommandRunner()

    motion = MotionService(robot, logger, X0, Y0, Z0)
    erosion = ErosionService(ee, logger)
    water = WaterService(water_hw, logger)
    gcode = GCodeService()

    return log_q, logger, runner, motion, erosion, water, gcode


def main():
    app = QApplication([])
    app.setStyle("Fusion")

    log_q, logger, runner, motion, erosion, water, gcode = build_system()
    w = MainWindow(motion, erosion, water, gcode, runner, logger, log_q)
    w.show()

    app.exec()


if __name__ == "__main__":
    main()
