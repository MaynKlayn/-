from threading import Event

from robot_ui.async_action_executor import AsyncActionExecutor


def test_async_executor_calls_callback() -> None:
    done = Event()
    errors = []
    executor = AsyncActionExecutor(workers=1)
    executor.submit(lambda: None, lambda error: (errors.append(error), done.set()))
    assert done.wait(2)
    assert errors == [None]
    executor.shutdown()
