import math
import re
from pathlib import Path


class GCodeParser:
    _pattern = re.compile(r"([XYZ])([+-]?\d*\.?\d+)")

    def parse(self, file_path: str) -> list[tuple[float, float, float]]:
        points: list[tuple[float, float, float]] = []
        current = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        for raw_line in Path(file_path).read_text(encoding="utf-8").splitlines():
            line = raw_line.split(";", 1)[0].strip()
            if not line or not line.startswith(("G0", "G1")):
                continue
            updated = current.copy()
            for axis, value in self._pattern.findall(line):
                updated[axis] = float(value)
            point = (updated["X"], updated["Y"], updated["Z"])
            if point != (current["X"], current["Y"], current["Z"]):
                points.append(point)
                current = updated
        return points or [(0.0, 0.0, 0.0)]

    def path_length(self, points: list[tuple[float, float, float]]) -> float:
        total = 0.0
        for index in range(1, len(points)):
            x1, y1, z1 = points[index - 1]
            x2, y2, z2 = points[index]
            total += math.dist((x1, y1, z1), (x2, y2, z2))
        return total
