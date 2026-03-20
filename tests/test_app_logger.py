from robot_ui.app_logger import AppLogger


def test_logger_notifies_subscribers() -> None:
    logger = AppLogger("test_logger_notifications")
    messages: list[str] = []
    logger.subscribe(messages.append)

    logger.info("test message")

    assert messages == ["test message"]
