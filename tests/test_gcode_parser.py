from pathlib import Path

from robot_ui.gcode_parser import GCodeParser


def test_parse_and_path_length(tmp_path: Path) -> None:
    file_path = tmp_path / "demo.gcode"
    file_path.write_text("G0 X0 Y0 Z0\nG1 X3 Y4 Z0\nG1 X3 Y4 Z12\n", encoding="utf-8")
    parser = GCodeParser()
    points = parser.parse(str(file_path))
    assert points == [(3.0, 4.0, 0.0), (3.0, 4.0, 12.0)]
    assert parser.path_length(points) == 12.0
